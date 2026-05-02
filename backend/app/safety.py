from __future__ import annotations

from typing import Any


BLOCKED_PATTERNS = {
    "hacking": ["hack", "exploit", "payload", "credential stuffing", "sql injection", "ransomware"],
    "malware": ["malware", "virus", "trojan", "keylogger", "botnet"],
    "data_theft": ["steal data", "steal password", "exfiltrate", "dump database", "bypass password"],
    "dark_web": [".onion", "dark web", "tor hidden service"],
    "doxxing": ["doxx", "private address", "private phone number"],
    "illegal_surveillance": ["spy on", "surveil", "track someone secretly"],
    "paywall_bypass": ["bypass paywall", "remove paywall", "read article free illegally"],
}

HIGH_RISK_HINTS = ["guaranteed legal result", "guaranteed market outcome", "guaranteed political outcome"]


def check_request_safety(text: str, category: str | None = None) -> dict[str, Any]:
    content = (text or "").strip()
    lowered = content.lower()

    for reason, patterns in BLOCKED_PATTERNS.items():
        for pattern in patterns:
            if pattern in lowered:
                return {
                    "allowed": False,
                    "risk_level": "high",
                    "reason": f"Blocked because the request appears related to {reason.replace('_', ' ')}.",
                    "safe_alternative": "Ask Builder Core for a safe defensive, educational, or compliance-focused alternative instead.",
                }

    for pattern in HIGH_RISK_HINTS:
        if pattern in lowered:
            return {
                "allowed": False,
                "risk_level": "high",
                "reason": "Blocked because the request asks for a guaranteed legal, financial, or political outcome.",
                "safe_alternative": "Ask for a risk-aware framework, checklist, or research plan instead of a guaranteed outcome.",
            }

    category_hint = (category or "").lower()
    if category_hint in {"law", "market", "politics", "forecasting"}:
        return {
            "allowed": True,
            "risk_level": "medium",
            "reason": "Allowed with caution because this category needs careful wording and human verification.",
            "safe_alternative": "Keep the output educational, structured, and explicit about uncertainty.",
        }

    return {
        "allowed": True,
        "risk_level": "low",
        "reason": "Request passed the Builder Core safety firewall.",
        "safe_alternative": "Not needed.",
    }
