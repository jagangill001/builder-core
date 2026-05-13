from __future__ import annotations

from app.connectors.base import BaseConnector


class NewsConnector(BaseConnector):
    name = "news"
    required_env_vars = ["NEWS_API_KEY"]
    provider_env_var = "NEWS_PROVIDER"
    capabilities = ["news_question"]

    def query(self, message: str) -> dict[str, object]:
        return self.execute({"message": message})

    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        if not self.status().configured:
            return {
                "ok": False,
                "code": "not_configured",
                "message": "News connector not configured. Set NEWS_API_KEY on the backend.",
                "warnings": ["News requests need a configured news provider."],
                "sources": [],
                "status": self.status().as_dict(),
            }
        status = self.status()
        return {
            "ok": False,
            "code": "provider_missing",
            "message": f"News provider '{status.provider}' is not implemented. No live news request was executed.",
            "warnings": ["News connector is configured, but live provider execution is still provider_missing."],
            "sources": [],
            "query": payload.get("message", ""),
            "status": status.as_dict(),
        }
