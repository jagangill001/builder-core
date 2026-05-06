from __future__ import annotations

from typing import Any


def build_timeline(sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    safe_sources = sources or []
    if not safe_sources:
        return {
            "before": [],
            "during": [],
            "after": [],
            "event_count": 0,
            "missing_data": ["Verified source timeline"],
        }

    return {
        "before": [],
        "during": [],
        "after": [],
        "event_count": 0,
        "missing_data": ["Timeline extraction is not connected to a verified source parser yet."],
    }
