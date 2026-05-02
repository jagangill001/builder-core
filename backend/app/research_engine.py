from __future__ import annotations

from typing import Any

try:
    from app.private_search import PrivateSearchService
    from app.storage import ProjectStorageService
except ImportError:
    from private_search import PrivateSearchService
    from storage import ProjectStorageService


class ResearchEngineService:
    def __init__(self, storage: ProjectStorageService, search: PrivateSearchService) -> None:
        self.storage = storage
        self.search = search

    def create_research_questions(self, topic: str) -> list[str]:
        return [
            f"What problem in {topic} matters most to users?",
            f"What evidence already exists in Builder Core about {topic}?",
            f"What still needs human verification for {topic}?",
        ]

    def identify_unknowns(self, topic: str, sources: list[dict[str, Any]]) -> list[str]:
        unknowns = [
            f"Builder Core still needs more saved sources to answer {topic} with higher confidence.",
            "Live internet-wide research is not connected yet.",
        ]
        if not sources:
            unknowns.insert(0, "No matching private-search sources were found yet.")
        return unknowns[:5]

    def summarize_research_from_sources(self, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "Builder Core did not find matching private-search sources yet, so this result is a structured low-confidence starting point."
        top_titles = ", ".join(str(item.get("title") or "Saved source") for item in sources[:3])
        return f"Builder Core used private-search sources such as {top_titles} to build this internal research summary."

    def save_research_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return self.storage.save_record("research_results", result)

    def run_internal_research(self, topic: str, goal: str, category: str) -> dict[str, Any]:
        search_result = self.search.search_private_index(f"{topic} {goal}", limit=8)
        sources = search_result.get("results", [])
        findings = [
            item.get("preview") or item.get("title") or "Saved source"
            for item in sources[:5]
        ]

        if not findings:
            findings = [
                f"Builder Core saved the topic '{topic}' and can research it further using future documents or URL ingests.",
                f"Goal captured: {goal}",
            ]

        result = {
            "topic": topic,
            "goal": goal,
            "category": category,
            "summary": self.summarize_research_from_sources(sources),
            "findings": findings[:6],
            "sources": [
                {
                    "title": item.get("title"),
                    "source_type": item.get("source_type"),
                    "url": item.get("url"),
                    "score": item.get("score"),
                }
                for item in sources[:6]
            ],
            "limitations": [
                "Live internet-wide research is not connected yet. Builder Core can only search its own private index, saved knowledge, user notes, and safely ingested public URLs."
            ],
            "unknowns": self.identify_unknowns(topic, sources),
            "confidence": "medium" if sources else "low",
            "next_steps": [
                "Add more user notes, documents, or safe URL ingests if you need stronger evidence.",
                "Use this result to build a market analysis, app plan, or Codex prompt.",
            ],
            "private_search_used": True,
            "results_count": search_result.get("results_count", 0),
        }
        return self.save_research_result(result)
