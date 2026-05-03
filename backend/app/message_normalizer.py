from __future__ import annotations

import re
from typing import Any


WORD_FIXES = {
    "reserch": "research",
    "serch": "search",
    "knowlege": "knowledge",
    "learm": "learn",
    "rember": "remember",
    "secuirty": "security",
    "udpates": "updates",
    "udpate": "update",
}

PHRASE_FIXES = {
    "make app": "build app",
    "make an app": "build app",
    "search my knowledge for": "search your knowledge for",
    "search my knowlege for": "search your knowledge for",
    "serch my knowledge for": "search your knowledge for",
    "serch my knowlege for": "search your knowledge for",
}


def normalize_message(message: str) -> dict[str, Any]:
    original = str(message or "")
    normalized = original
    corrections: list[dict[str, str]] = []

    for before, after in PHRASE_FIXES.items():
        pattern = re.compile(re.escape(before), flags=re.IGNORECASE)
        if pattern.search(normalized):
            normalized = pattern.sub(after, normalized)
            corrections.append({"from": before, "to": after})

    for before, after in WORD_FIXES.items():
        pattern = re.compile(rf"\b{re.escape(before)}\b", flags=re.IGNORECASE)
        if pattern.search(normalized):
            normalized = pattern.sub(after, normalized)
            corrections.append({"from": before, "to": after})

    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = _normalize_memory_prefix(normalized)

    return {
        "original_message": original,
        "normalized_message": normalized or original.strip(),
        "changed": normalized.strip() != original.strip(),
        "corrections": corrections,
    }


def _normalize_memory_prefix(message: str) -> str:
    if re.match(r"(?i)^remember this\s+[^:]", message):
        return re.sub(r"(?i)^remember this\s+", "remember this: ", message, count=1)
    if re.match(r"(?i)^save this\s+[^:]", message):
        return re.sub(r"(?i)^save this\s+", "save this: ", message, count=1)
    if re.match(r"(?i)^add this to knowledge\s+[^:]", message):
        return re.sub(r"(?i)^add this to knowledge\s+", "add this to knowledge: ", message, count=1)
    return message
