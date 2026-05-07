from __future__ import annotations

from typing import Any

ALLOWED_ROLES = {"user", "assistant"}
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_CHARS = 700


def normalize_history(history: Any, *, limit: int = MAX_HISTORY_MESSAGES) -> list[dict[str, str]]:
    if not isinstance(history, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in history[-limit:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        content = _clean_content(item.get("content"))
        if role not in ALLOWED_ROLES or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def recent_context_text(history: list[dict[str, str]]) -> str:
    parts = []
    for item in history:
        role = item.get("role") or "user"
        content = item.get("content") or ""
        if content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts)


def has_useful_context(history: list[dict[str, str]]) -> bool:
    return bool(recent_context_text(history).strip())


def _clean_content(value: Any) -> str:
    clean = " ".join(str(value or "").split())
    if len(clean) <= MAX_HISTORY_CHARS:
        return clean
    return clean[: MAX_HISTORY_CHARS - 3].rstrip() + "..."
