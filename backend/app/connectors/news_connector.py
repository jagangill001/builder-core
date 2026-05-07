from __future__ import annotations

import os
from typing import Any

from app.core.response_builder import LIVE_INTERNET_NOT_CONNECTED
from app.research.search_answer_engine import build_search_answer

NEWS_FALLBACK_MESSAGE = "News connector is not configured, so Builder Core searched live web results instead."


def answer_news_query(query: str) -> dict[str, Any]:
    provider = os.getenv("NEWS_PROVIDER", "").strip()
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if provider and api_key:
        return {
            "query": query,
            "answer": "News API support is reserved for a later phase. Builder Core did not invent news.",
            "summary": "News API support is reserved for a later phase. Builder Core did not invent news.",
            "sources": [],
            "facts": [],
            "claims": [],
            "unknowns": [
                {
                    "text": "A news provider is configured, but no Phase 5 news API implementation is connected yet.",
                    "reason": "News API integration has not been implemented.",
                }
            ],
            "confidence": "low",
            "missing_data": ["Connected news API implementation"],
            "warnings": ["News API implementation is not connected yet."],
            "search_connected": False,
            "live_search_connected": False,
            "memory_saved": False,
            "recommended_next_step": "Check primary reporting and official sources before acting on breaking news.",
            "answer_mode": "news",
            "used_live_search": False,
        }

    result = build_search_answer(_news_search_query(query))
    warnings = [NEWS_FALLBACK_MESSAGE, *[str(item) for item in result.get("warnings", []) if item]]
    if not result.get("search_connected"):
        answer = f"{NEWS_FALLBACK_MESSAGE} {LIVE_INTERNET_NOT_CONNECTED}"
    else:
        answer = str(result.get("answer") or "Builder Core found live news-related web results. Review the sources for the current picture.")
    return {
        **result,
        "answer": answer,
        "summary": answer,
        "warnings": list(dict.fromkeys(warnings)),
        "recommended_next_step": "Compare primary reporting and official sources before making decisions.",
        "answer_mode": "news",
        "used_live_search": bool(result.get("search_connected") or result.get("live_search_connected")),
    }


def _news_search_query(query: str) -> str:
    clean = " ".join((query or "").split())
    return clean if "news" in clean.lower() else f"latest news {clean}"
