from __future__ import annotations

import os
from typing import Any

from app.core.response_builder import LIVE_INTERNET_NOT_CONNECTED
from app.research.search_answer_engine import build_search_answer

WEATHER_FALLBACK_MESSAGE = "Weather connector is not configured, so Builder Core searched live web results instead."


def answer_weather_query(query: str) -> dict[str, Any]:
    provider = os.getenv("WEATHER_PROVIDER", "").strip()
    api_key = os.getenv("WEATHER_API_KEY", "").strip()
    if provider and api_key:
        return {
            "query": query,
            "answer": "Weather API support is reserved for a later phase. Builder Core did not invent weather data.",
            "summary": "Weather API support is reserved for a later phase. Builder Core did not invent weather data.",
            "sources": [],
            "facts": [],
            "claims": [],
            "unknowns": [
                {
                    "text": "A weather provider is configured, but no Phase 5 weather API implementation is connected yet.",
                    "reason": "Weather API integration has not been implemented.",
                }
            ],
            "confidence": "low",
            "missing_data": ["Connected weather API implementation"],
            "warnings": ["Weather API implementation is not connected yet."],
            "search_connected": False,
            "live_search_connected": False,
            "memory_saved": False,
            "recommended_next_step": "Use a trusted weather service for time-sensitive weather decisions.",
            "answer_mode": "weather",
            "used_live_search": False,
        }

    result = build_search_answer(_weather_search_query(query))
    warnings = [WEATHER_FALLBACK_MESSAGE, *[str(item) for item in result.get("warnings", []) if item]]
    if not result.get("search_connected"):
        answer = f"{WEATHER_FALLBACK_MESSAGE} {LIVE_INTERNET_NOT_CONNECTED}"
    else:
        answer = str(result.get("answer") or "Builder Core found live weather-related web results. Review the sources for current conditions.")
    return {
        **result,
        "answer": answer,
        "summary": answer,
        "warnings": list(dict.fromkeys(warnings)),
        "recommended_next_step": "For safety-critical plans, confirm weather with an official weather service.",
        "answer_mode": "weather",
        "used_live_search": bool(result.get("search_connected") or result.get("live_search_connected")),
    }


def _weather_search_query(query: str) -> str:
    clean = " ".join((query or "").split())
    return clean if "weather" in clean.lower() else f"weather {clean}"
