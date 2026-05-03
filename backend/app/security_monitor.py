from __future__ import annotations

import ipaddress
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


ATTACK_PATHS = [
    "/wp-admin",
    "/.env",
    "/.git",
    "/admin",
    "/phpmyadmin",
    "/server-status",
    "/config",
    "/api/secrets",
    "/actuator",
    "/debug",
]

SECRET_PATH_PARTS = ["secret", "token", "credential", "private-key", "service-account", ".env", ".git"]
SUSPICIOUS_USER_AGENTS = ["sqlmap", "nikto", "nessus", "nmap", "masscan", "acunetix", "dirbuster", "gobuster"]
SENSITIVE_HEADERS = ["authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token", "token", "secret", "key"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_header_value(name: str, value: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in SENSITIVE_HEADERS):
        return "[redacted]"
    value = str(value).replace("\r", " ").replace("\n", " ").strip()
    return value[:160]


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value.strip())
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)
    except ValueError:
        return False


class SecurityMonitorService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage
        self._ip_high_counts: Counter[str] = Counter()
        self._ip_suspicious_counts: Counter[str] = Counter()

    def record_security_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_id = event.get("event_id") or f"security_event_{uuid4().hex[:12]}"
        prepared = {
            "id": event_id,
            "event_id": event_id,
            "event_type": event.get("event_type") or "suspicious_request",
            "severity": event.get("severity") or "low",
            "ip_address": event.get("ip_address"),
            "user_agent": str(event.get("user_agent") or "")[:240],
            "path": event.get("path") or "",
            "method": event.get("method") or "",
            "reason": event.get("reason") or "Security event recorded.",
            "headers_summary": event.get("headers_summary") or {},
            "geo_hint": event.get("geo_hint") or estimate_geo_hint(event.get("ip_address")),
            "created_at": event.get("created_at") or utc_now_iso(),
        }
        ip = str(prepared.get("ip_address") or "")
        if ip:
            self._ip_suspicious_counts[ip] += 1
            if prepared["severity"] in {"high", "critical"}:
                self._ip_high_counts[ip] += 1
        return self.storage.save_record("security_events", prepared)

    def list_security_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.storage.list_records("security_events", max(1, min(limit, 500)))

    def get_security_summary(self) -> dict[str, Any]:
        events = self.list_security_events(200)
        recent_high = [event for event in events if event.get("severity") in {"high", "critical"}][:10]
        top_ips = Counter(str(event.get("ip_address") or "unknown") for event in events if event.get("ip_address")).most_common(8)
        return {
            "security_monitor_enabled": True,
            "events_count": len(events),
            "recent_high_severity": recent_high,
            "top_suspicious_ips": [{"ip_address": ip, "count": count} for ip, count in top_ips],
            "warnings": [
                "IP headers can be spoofed unless trusted proxy configuration is enforced.",
                "IP location is approximate and does not identify a person.",
                "VPN, proxy, and cloud hosts may hide the true origin.",
                "Builder Core follows a no-retaliation policy and uses defensive controls only.",
            ],
            "recommendations": [
                "Add authentication before exposing admin security dashboards.",
                "Use Cloud Armor or API Gateway for production WAF and rate limits.",
                "Review high-severity events before changing firewall policy.",
            ],
        }

    def detect_suspicious_request(self, request: Any) -> dict[str, Any]:
        path = str(getattr(getattr(request, "url", None), "path", "") or "")
        query = str(getattr(getattr(request, "url", None), "query", "") or "")
        method = str(getattr(request, "method", "") or "")
        headers = getattr(request, "headers", {}) or {}
        user_agent = str(headers.get("user-agent", "") if hasattr(headers, "get") else "")
        content_length = str(headers.get("content-length", "0") if hasattr(headers, "get") else "0")
        reasons: list[str] = []
        severity = "low"

        lowered_path = path.lower()
        lowered_query = query.lower()
        lowered_agent = user_agent.lower()

        if any(lowered_path == item or lowered_path.startswith(item + "/") for item in ATTACK_PATHS):
            reasons.append("Request path matches a common attack or scanning path.")
            severity = "high" if any(part in lowered_path for part in SECRET_PATH_PARTS) else "medium"

        if any(part in lowered_path for part in SECRET_PATH_PARTS):
            reasons.append("Request path appears to target secrets, credentials, or config.")
            severity = "high"

        if self._looks_like_injection(lowered_query):
            reasons.append("Query string contains injection-like or traversal-like patterns.")
            severity = "high"

        if any(agent in lowered_agent for agent in SUSPICIOUS_USER_AGENTS):
            reasons.append("User-Agent looks like a scanning or vulnerability tool.")
            severity = "medium" if severity == "low" else severity

        try:
            if int(content_length or "0") > 1_000_000:
                reasons.append("Payload is unusually large for this service.")
                severity = "medium" if severity == "low" else severity
        except ValueError:
            pass

        ip_address = extract_client_ip(request)
        if ip_address and self._ip_high_counts[ip_address] >= 5 and severity == "high":
            reasons.append("Repeated high-severity events were seen from this source.")
            severity = "critical"
        elif ip_address and self._ip_suspicious_counts[ip_address] >= 10 and severity in {"low", "medium"}:
            reasons.append("Repeated suspicious requests were seen from this source.")
            severity = "medium"

        return {
            "suspicious": bool(reasons),
            "event_type": "possible_attack" if severity in {"high", "critical"} else "suspicious_request",
            "severity": severity,
            "reason": "; ".join(reasons) if reasons else "No suspicious rule matched.",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "path": path,
            "method": method,
            "headers_summary": summarize_headers_safely(request),
            "geo_hint": estimate_geo_hint(ip_address),
        }

    def create_incident_report(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        items = events if events is not None else self.list_security_events(200)
        return create_incident_report(items)

    def record_response_status(self, request: Any, status_code: int) -> None:
        if status_code not in {404, 500}:
            return
        severity = "low" if status_code == 404 else "medium"
        self.record_security_event(
            {
                "event_type": "suspicious_request" if status_code == 404 else "system_error",
                "severity": severity,
                "ip_address": extract_client_ip(request),
                "user_agent": getattr(request, "headers", {}).get("user-agent", ""),
                "path": str(getattr(getattr(request, "url", None), "path", "") or ""),
                "method": str(getattr(request, "method", "") or ""),
                "reason": f"Repeated {status_code} responses can indicate probing or instability.",
                "headers_summary": summarize_headers_safely(request),
                "geo_hint": estimate_geo_hint(extract_client_ip(request)),
            }
        )

    def _looks_like_injection(self, text: str) -> bool:
        if not text:
            return False
        patterns = [
            r"<\s*script",
            r"\.\./",
            r"union\s+select",
            r"or\s+1\s*=\s*1",
            r"drop\s+table",
            r"exec\s*\(",
            r"\|\|",
            r";\s*(cat|curl|wget|bash|sh|powershell|cmd)",
            r"\$\(",
        ]
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def extract_client_ip(request: Any) -> str | None:
    headers = getattr(request, "headers", {}) or {}

    x_forwarded_for = headers.get("x-forwarded-for") if hasattr(headers, "get") else None
    if x_forwarded_for:
        parts = [part.strip() for part in str(x_forwarded_for).split(",") if part.strip()]
        for part in parts:
            if _is_public_ip(part):
                return part
        if parts:
            return parts[0]

    x_real_ip = headers.get("x-real-ip") if hasattr(headers, "get") else None
    if x_real_ip:
        return str(x_real_ip).strip()

    forwarded = headers.get("forwarded") if hasattr(headers, "get") else None
    if forwarded:
        match = re.search(r"for=\"?\[?([^;,\]\" ]+)", str(forwarded), flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return str(host).strip() if host else None


def summarize_headers_safely(request: Any) -> dict[str, str]:
    headers = getattr(request, "headers", {}) or {}
    summary: dict[str, str] = {}
    if not hasattr(headers, "items"):
        return summary
    for name, value in headers.items():
        lowered = str(name).lower()
        if lowered in {"host", "user-agent", "content-type", "content-length", "x-forwarded-for", "x-real-ip", "forwarded"}:
            summary[lowered] = _safe_header_value(lowered, str(value))
        elif any(token in lowered for token in SENSITIVE_HEADERS):
            summary[lowered] = "[redacted]"
    return summary


def estimate_geo_hint(ip_address: str | None) -> dict[str, Any]:
    if not ip_address:
        return {
            "available": False,
            "note": "No client IP was available to estimate source metadata.",
        }
    return {
        "available": False,
        "ip_address": ip_address,
        "note": "Geo lookup is not configured. IP source can be logged, but exact location is not known.",
        "warnings": [
            "IP headers can be spoofed unless trusted proxy configuration is enforced.",
            "IP location is approximate.",
            "VPN/proxy/cloud servers may hide true origin.",
            "This does not identify a person.",
        ],
    }


def create_incident_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    if not events:
        highest = "low"
    else:
        highest = max((str(event.get("severity") or "low") for event in events), key=lambda item: severity_order.get(item, 0))
    patterns = Counter(str(event.get("reason") or "Unknown") for event in events).most_common(8)
    sources = Counter(str(event.get("ip_address") or "unknown") for event in events if event.get("ip_address")).most_common(8)
    recommendations = [
        "Review recent high-severity paths and confirm whether they are scanners or expected health checks.",
        "Keep secrets out of frontend bundles and public routes.",
        "Add Cloud Armor/API Gateway and admin authentication before stronger blocking policy.",
        "Do not retaliate. Use defensive controls, logs, and provider abuse reporting where appropriate.",
    ]
    return {
        "summary": f"Analyzed {len(events)} security events. Highest observed severity is {highest}.",
        "events_analyzed": len(events),
        "highest_severity": highest,
        "top_patterns": [{"pattern": pattern, "count": count} for pattern, count in patterns],
        "approximate_sources": [{"ip_address": ip, "count": count, "geo_hint": estimate_geo_hint(ip)} for ip, count in sources],
        "recommended_actions": recommendations,
        "disclaimer": "IP location is approximate and does not identify a person.",
    }
