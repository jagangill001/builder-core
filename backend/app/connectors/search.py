from __future__ import annotations

from app.brain.source_ranker import rank_source
from app.connectors.base import BaseConnector


class SearchConnector(BaseConnector):
    name = "search"
    required_env_vars = ["SEARCH_API_KEY"]
    provider_env_var = "SEARCH_PROVIDER"
    capabilities = ["classify_current_question", "rank_sources", "live_search"]

    def query(self, query: str) -> dict[str, object]:
        return self.execute({"query": query})

    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        status = self.status()
        if not status.configured:
            return {
                "ok": False,
                "code": "not_configured",
                "message": "Search connector not configured. Set SEARCH_API_KEY on the backend.",
                "sources": [],
                "warnings": ["Live search is required for this answer, but SEARCH_API_KEY is missing."],
                "status": status.as_dict(),
            }

        return {
            "ok": False,
            "code": "provider_missing",
            "message": f"Search provider '{status.provider}' is not implemented. No live search was executed.",
            "sources": [
                rank_source(
                    title="Search provider adapter placeholder",
                    url="",
                    snippet=f"Query was not sent to a live provider: {payload.get('query', '')}",
                )
            ],
            "warnings": ["Search connector is configured, but live provider execution is still provider_missing."],
            "status": status.as_dict(),
        }
