from __future__ import annotations

from typing import Any

from app.connectors.search_connector import LIVE_INTERNET_NOT_CONNECTED, get_search_status

LIVE_SEARCH_NOT_CONNECTED = LIVE_INTERNET_NOT_CONNECTED


class LiveSourceCollector:
    def collect(self, query: str) -> dict[str, Any]:
        search_status = get_search_status(query)
        return {
            "connected": bool(search_status.get("connected")),
            "provider": search_status.get("provider"),
            "sources": list(search_status.get("results", [])),
            "message": str(search_status.get("message") or LIVE_SEARCH_NOT_CONNECTED),
            "query": query.strip(),
        }


def collect_live_sources(query: str) -> dict[str, Any]:
    return LiveSourceCollector().collect(query)