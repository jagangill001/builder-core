from __future__ import annotations

import re
from typing import Any
from urllib import parse as urlparse


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


DOMAIN_PATTERN = re.compile(
    r"\b(?:https?://)?(?:www\.)?([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+)(?:/[^\s<>\"]*)?",
    flags=re.IGNORECASE,
)


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
        "domain": extract_domain_from_message(normalized),
        "learned_domain_request": is_learned_domain_request(normalized),
        "learned_domain_list_request": is_learned_domain_list_request(normalized),
    }


def extract_domain_from_message(message: str) -> str:
    for match in DOMAIN_PATTERN.finditer(str(message or "")):
        candidate = match.group(0).strip(".,;:!?)]}")
        if "://" in candidate:
            parsed = urlparse.urlparse(candidate)
            host = parsed.hostname or ""
        else:
            host = match.group(1)
        host = host.lower().removeprefix("www.")
        if host and not _looks_like_file_name(host):
            return host
    return ""


def is_learned_domain_list_request(message: str) -> bool:
    lowered = str(message or "").lower()
    return any(
        phrase in lowered
        for phrase in [
            "show learned domains",
            "list learned domains",
            "learned domains",
            "show learned urls",
            "list learned urls",
            "learned urls",
        ]
    )


def is_learned_domain_request(message: str) -> bool:
    lowered = str(message or "").lower()
    if is_learned_domain_list_request(lowered):
        return True
    if not extract_domain_from_message(lowered):
        return False
    return any(
        phrase in lowered
        for phrase in [
            "what did you learn from",
            "what do you know from",
            "search inside",
            "search learned domain",
            "learned domain",
            "learned url",
        ]
    )


def remove_domains_from_message(message: str) -> str:
    return DOMAIN_PATTERN.sub(" ", str(message or ""))


def _normalize_memory_prefix(message: str) -> str:
    if re.match(r"(?i)^remember this\s+[^:]", message):
        return re.sub(r"(?i)^remember this\s+", "remember this: ", message, count=1)
    if re.match(r"(?i)^save this\s+[^:]", message):
        return re.sub(r"(?i)^save this\s+", "save this: ", message, count=1)
    if re.match(r"(?i)^add this to knowledge\s+[^:]", message):
        return re.sub(r"(?i)^add this to knowledge\s+", "add this to knowledge: ", message, count=1)
    return message


def _looks_like_file_name(host: str) -> bool:
    return host.endswith((".py", ".tsx", ".ts", ".js", ".json", ".md", ".txt", ".css", ".html"))
