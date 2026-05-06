from __future__ import annotations

import re
from typing import Any

from app.storage.storage_backend import read_recent_jsonl, save_jsonl

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"(?i)(api[_\s-]?key|admin[_\s-]?key|secret|password)\s*[:=]\s*\S+"),
)


def append_audit_entry(entry: dict[str, Any]) -> None:
    save_jsonl("audit_log", _redact_entry(entry))


def read_recent_audit_entries(limit: int = 20) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 100))
    return read_recent_jsonl("audit_log", bounded_limit)


def _redact_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(value) for key, value in entry.items()}


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def _redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted