from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.memory.memory_filter import filter_memory_record
from app.storage.storage_backend import read_recent_jsonl, save_jsonl

MEMORY_COLLECTION = "safe_memory"


def save_safe_memory(record: dict[str, Any]) -> dict[str, Any]:
    prepared = {
        "memory_id": record.get("memory_id") or f"mem_{uuid4().hex[:12]}",
        "memory_type": record.get("memory_type") or "search_answer",
        "topic": record.get("topic") or "",
        "summary": record.get("summary") or "",
        "sources": record.get("sources") or [],
        "confidence": record.get("confidence") or "low",
        "verify_before_use": True,
        "created_at": record.get("created_at") or datetime.now(UTC).isoformat(),
    }
    allowed, safe_record, warnings = filter_memory_record(prepared)
    if not allowed:
        return {"saved": False, "item": None, "warnings": warnings}
    saved = save_jsonl(MEMORY_COLLECTION, safe_record)
    return {"saved": True, "item": saved, "warnings": warnings}


def get_recent_memories(limit: int = 20) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 100))
    return {
        "ok": True,
        "items": read_recent_jsonl(MEMORY_COLLECTION, bounded_limit),
        "limit": bounded_limit,
    }


def search_memory(query: str, limit: int = 20) -> dict[str, Any]:
    clean_query = " ".join((query or "").lower().split())
    bounded_limit = max(1, min(int(limit), 100))
    if not clean_query:
        return {"ok": True, "query": query, "items": [], "limit": bounded_limit}

    matches: list[dict[str, Any]] = []
    for item in read_recent_jsonl(MEMORY_COLLECTION, 200):
        haystack = " ".join(
            [
                str(item.get("topic") or ""),
                str(item.get("summary") or ""),
                " ".join(str(source.get("title") or "") for source in item.get("sources", []) if isinstance(source, dict)),
            ]
        ).lower()
        if clean_query in haystack:
            matches.append(item)
        if len(matches) >= bounded_limit:
            break
    return {"ok": True, "query": query, "items": matches, "limit": bounded_limit}
