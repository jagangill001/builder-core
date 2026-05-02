from __future__ import annotations

from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


class MarketAnalyzerService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def identify_target_users(self, topic: str) -> list[str]:
        topic_lower = topic.lower()
        if "dispatch" in topic_lower or "trucking" in topic_lower:
            return [
                "Small trucking companies",
                "Independent dispatchers",
                "Owner-operators who need a simpler operations view",
            ]
        return [
            "Primary operators in the target market",
            "Managers who need trend visibility",
            "Analysts or founders who need clearer market signals",
        ]

    def identify_competitor_research_questions(self, topic: str) -> list[str]:
        return [
            f"Which tools already help with {topic} today?",
            "What are those tools missing for smaller teams or first-time operators?",
            "Where is the biggest evidence gap in pricing, data quality, or workflow design?",
        ]

    def identify_risks_and_opportunities(self, topic: str) -> dict[str, list[str]]:
        return {
            "risks": [
                f"The {topic} market may need real domain interviews before the app idea is reliable.",
                "Saved knowledge may still be thin, so assumptions should stay labeled clearly.",
            ],
            "opportunities": [
                "A lightweight market dashboard could make saved research easier to compare over time.",
                "Builder Core can save a repeatable market-analysis workflow that gets better as the private index grows.",
            ],
        }

    def create_market_app_ideas(self, topic: str) -> list[str]:
        return [
            f"{topic.title()} signal dashboard",
            f"{topic.title()} research notebook with saved findings and alerts",
            f"{topic.title()} market-to-app planning assistant",
        ]

    def save_market_analysis(self, result: dict[str, Any]) -> dict[str, Any]:
        return self.storage.save_record("market_analysis", result)

    def analyze_market(self, topic: str, context_sources: list[dict[str, Any]]) -> dict[str, Any]:
        risks_and_opportunities = self.identify_risks_and_opportunities(topic)
        result = {
            "topic": topic,
            "market_summary": (
                f"Builder Core created a structured market-analysis view for {topic}. "
                "This is a planning aid based on saved knowledge, not a guaranteed market forecast."
            ),
            "target_users": self.identify_target_users(topic),
            "competitors_to_research": self.identify_competitor_research_questions(topic),
            "risks": risks_and_opportunities["risks"],
            "opportunities": risks_and_opportunities["opportunities"],
            "missing_data": [
                "Real customer interviews or user notes",
                "Verified competitor pricing and workflow details",
                "More saved research sources in Builder Core private search",
            ],
            "confidence": "low" if not context_sources else "medium",
            "app_ideas": self.create_market_app_ideas(topic),
            "context_sources": context_sources[:6],
        }
        return self.save_market_analysis(result)
