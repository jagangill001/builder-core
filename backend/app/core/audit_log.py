from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"(?i)(api[_\s-]?key|admin[_\s-]?key|secret|password)\s*[:=]\s*\S+"),
)


def append_audit_entry(entry: dict[str, Any]) -> None:
    safe_entry = _redact_entry(entry)
    audit_path = get_audit_log_path()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(safe_entry, ensure_ascii=False, default=str) + "\n")


def read_recent_audit_entries(limit: int = 20) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, 100))
    audit_path = get_audit_log_path()
    if not audit_path.exists():
        return []

    lines = _tail_lines(audit_path, bounded_limit)
    entries: list[dict[str, Any]] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    entries.reverse()
    return entries


def get_audit_log_path() -> Path:
    configured_data_dir = os.getenv("BUILDER_CORE_DATA_DIR")
    data_dir = Path(configured_data_dir) if configured_data_dir else DEFAULT_DATA_DIR
    if not data_dir.is_absolute():
        data_dir = DEFAULT_DATA_DIR.parent / data_dir
    return data_dir / "audit_log.jsonl"


def _tail_lines(path: Path, limit: int) -> list[str]:
    with path.open("r", encoding="utf-8") as audit_file:
        lines = audit_file.readlines()
    return [line.strip() for line in lines[-limit:] if line.strip()]


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
