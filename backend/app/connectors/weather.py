from __future__ import annotations

from app.connectors.base import BaseConnector


class WeatherConnector(BaseConnector):
    name = "weather"
    required_env_vars = ["WEATHER_API_KEY"]
    provider_env_var = "WEATHER_PROVIDER"
    capabilities = ["weather_question"]

    def query(self, message: str) -> dict[str, object]:
        return self.execute({"message": message})

    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        if not self.status().configured:
            return {
                "ok": False,
                "code": "not_configured",
                "message": "Weather connector not configured. Set WEATHER_API_KEY on the backend.",
                "warnings": ["Weather requests need a configured weather provider."],
                "sources": [],
                "status": self.status().as_dict(),
            }
        status = self.status()
        return {
            "ok": False,
            "code": "provider_missing",
            "message": f"Weather provider '{status.provider}' is not implemented. No live weather request was executed.",
            "warnings": ["Weather connector is configured, but live provider execution is still provider_missing."],
            "sources": [],
            "query": payload.get("message", ""),
            "status": status.as_dict(),
        }
