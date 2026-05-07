from __future__ import annotations

from typing import Any

from app.memory.memory_filter import BLOCKED_MEMORY_TERMS, redact_sensitive_text
from app.memory.memory_store import search_memory
from app.storage.storage_backend import read_recent_jsonl

MEMORY_COLLECTION = "safe_memory"
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "with",
}
GENERIC_TOPIC_WORDS = {
    "current",
    "government",
    "leader",
    "minister",
    "prime",
    "president",
    "official",
    "office",
    "holder",
    "today",
    "latest",
    "news",
}
COUNTRY_ALIASES = {
    "canada": {"canada", "canadian"},
    "india": {"india", "indian"},
    "united_states": {"usa", "u.s.", "us", "united", "states", "america", "american"},
    "united_kingdom": {"uk", "u.k.", "britain", "british", "england"},
}


def recall_relevant_memories(query: str, limit: int = 3) -> dict[str, Any]:
    tokens = _tokens(query)
    bounded_limit = max(1, min(int(limit), 10))
    if not tokens:
        return {"ok": True, "query": query, "items": [], "limit": bounded_limit}

    scored: list[tuple[int, dict[str, Any]]] = []
    query_countries = _country_matches(query)
    important_query_tokens = tokens.difference(GENERIC_TOPIC_WORDS)
    for item in read_recent_jsonl(MEMORY_COLLECTION, 200):
        if not isinstance(item, dict) or _contains_secret_marker(item):
            continue
        haystack = _memory_text(item)
        item_tokens = _tokens(haystack)
        overlap = tokens.intersection(item_tokens)
        memory_countries = _country_matches(haystack)
        important_overlap = important_query_tokens.intersection(item_tokens)
        if not _topic_relevant(query_countries, memory_countries, important_overlap, len(overlap)):
            continue
        score = len(overlap) + (3 * len(query_countries.intersection(memory_countries))) + (2 * len(important_overlap))
        if score >= _minimum_score(tokens):
            scored.append((score, _safe_memory_preview(item)))

    scored.sort(key=lambda entry: entry[0], reverse=True)
    return {
        "ok": True,
        "query": query,
        "items": [item for _, item in scored[:bounded_limit]],
        "limit": bounded_limit,
    }


def _safe_memory_preview(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "memory_id": str(item.get("memory_id") or ""),
        "memory_type": str(item.get("memory_type") or ""),
        "topic": redact_sensitive_text(str(item.get("topic") or "")),
        "summary": redact_sensitive_text(str(item.get("summary") or "")),
        "sources": item.get("sources") if isinstance(item.get("sources"), list) else [],
        "confidence": str(item.get("confidence") or "low"),
        "verify_before_use": True,
        "created_at": str(item.get("created_at") or ""),
    }


def _memory_text(item: dict[str, Any]) -> str:
    source_text = " ".join(
        str(source.get("title") or "") for source in item.get("sources", []) if isinstance(source, dict)
    )
    return " ".join([str(item.get("topic") or ""), str(item.get("summary") or ""), source_text])


def _contains_secret_marker(item: dict[str, Any]) -> bool:
    text = _memory_text(item).lower()
    return "[redacted]" in text or any(term in text for term in BLOCKED_MEMORY_TERMS)


def _tokens(text: str) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in str(text or ""))
    return {token for token in cleaned.split() if len(token) > 2 and token not in STOP_WORDS}


def _country_matches(text: str) -> set[str]:
    normalized = f" {_normalize_for_match(text)} "
    matches: set[str] = set()
    for country, aliases in COUNTRY_ALIASES.items():
        if any(f" {_normalize_for_match(alias)} " in normalized for alias in aliases):
            matches.add(country)
    return matches


def _topic_relevant(
    query_countries: set[str],
    memory_countries: set[str],
    important_overlap: set[str],
    overlap_count: int,
) -> bool:
    if query_countries and memory_countries and query_countries.isdisjoint(memory_countries):
        return False
    if query_countries and not memory_countries and overlap_count < 3:
        return False
    if query_countries.intersection(memory_countries):
        return True
    return bool(important_overlap)


def _minimum_score(tokens: set[str]) -> int:
    if len(tokens) <= 1:
        return 3
    if len(tokens) <= 3:
        return 4
    return 5


def _normalize_for_match(text: str) -> str:
    return " ".join(str(text or "").lower().replace(".", " ").replace("-", " ").replace("_", " ").split())


__all__ = ["search_memory", "recall_relevant_memories"]
