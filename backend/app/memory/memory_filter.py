from __future__ import annotations

import re
from typing import Any

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*['\"]?[^'\"\s,;]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]{12,}"),
    re.compile(r"(?i)sk-[a-z0-9]{16,}"),
)

BLOCKED_MEMORY_TERMS = {
    "password",
    "api key",
    "secret key",
    "admin key",
    "private profile",
    "access token",
    "refresh token",
}


def filter_memory_record(record: dict[str, Any]) -> tuple[bool, dict[str, Any], list[str]]:
    warnings: list[str] = []
    text_blob = " ".join(_walk_strings(record)).lower()
    if any(term in text_blob for term in BLOCKED_MEMORY_TERMS):
        warnings.append("Memory contained private or secret-like data and was not saved.")
        return False, {}, warnings

    safe_record = {
        "memory_id": _redact(str(record.get("memory_id") or "")),
        "memory_type": _safe_memory_type(record.get("memory_type")),
        "topic": _redact(_truncate(str(record.get("topic") or ""), 240)),
        "summary": _redact(_truncate(str(record.get("summary") or ""), 1200)),
        "sources": _filter_sources(record.get("sources")),
        "confidence": _safe_confidence(record.get("confidence")),
        "verify_before_use": True,
        "created_at": _redact(str(record.get("created_at") or "")),
    }
    return True, safe_record, warnings


def redact_sensitive_text(text: str) -> str:
    return _redact(text)


def _filter_sources(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    sources: list[dict[str, str]] = []
    for item in value[:8]:
        if not isinstance(item, dict):
            continue
        sources.append(
            {
                "title": _redact(_truncate(str(item.get("title") or ""), 240)),
                "url": _redact(_truncate(str(item.get("url") or ""), 500)),
                "snippet": _redact(_truncate(str(item.get("snippet") or item.get("summary") or ""), 500)),
                "source_domain": _redact(_truncate(str(item.get("source_domain") or ""), 120)),
            }
        )
    return sources


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        output: list[str] = []
        for item in value.values():
            output.extend(_walk_strings(item))
        return output
    if isinstance(value, list):
        output = []
        for item in value:
            output.extend(_walk_strings(item))
        return output
    return []


def _redact(text: str) -> str:
    output = text
    for pattern in SECRET_PATTERNS:
        output = pattern.sub("[REDACTED]", output)
    return output


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def _safe_memory_type(value: Any) -> str:
    memory_type = str(value or "search_answer").strip().lower()
    allowed = {"search_answer", "research_note", "source_note", "project_fact"}
    return memory_type if memory_type in allowed else "search_answer"


def _safe_confidence(value: Any) -> str:
    confidence = str(value or "low").strip().lower()
    return confidence if confidence in {"low", "medium", "high"} else "low"
