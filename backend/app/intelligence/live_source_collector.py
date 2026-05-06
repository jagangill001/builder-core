from __future__ import annotations

import os
from typing import Any

LIVE_SEARCH_NOT_CONNECTED = "Live search is not connected yet."


class LiveSourceCollector:
    def __init__(self) -> None:
        self.provider = os.getenv("LIVE_SEARCH_PROVIDER", "").strip() or None
        self.api_key_configured = bool(os.getenv("LIVE_SEARCH_API_KEY", "").strip())
        self.endpoint = os.getenv("LIVE_SEARCH_ENDPOINT", "").strip() or None

    def collect(self, query: str) -> dict[str, Any]:
        return {
            "connected": False,
            "provider": None,
            "sources": [],
            "message": LIVE_SEARCH_NOT_CONNECTED,
            "query": query.strip(),
        }


def collect_live_sources(query: str) -> dict[str, Any]:
    return LiveSourceCollector().collect(query)
