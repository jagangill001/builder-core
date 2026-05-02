from __future__ import annotations

from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


class AppPlannerService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def suggest_mvp_features(self, goal: str) -> list[str]:
        return [
            "Saved research dashboard",
            "Trend summary cards",
            "Simple filters for category, source, and timeframe",
            "Notes panel for analyst or founder insights",
            "Export-ready Codex prompt or follow-up plan",
        ]

    def suggest_backend_routes(self, goal: str) -> list[str]:
        return [
            "GET /market/summary",
            "GET /market/findings",
            "POST /market/notes",
            "GET /market/trends",
            "POST /prompts/codex",
        ]

    def suggest_frontend_screens(self, goal: str) -> list[str]:
        return [
            "Overview dashboard",
            "Research findings screen",
            "Market opportunities screen",
            "Notes and memory screen",
            "Prompt export screen",
        ]

    def suggest_storage_collections(self, goal: str) -> list[str]:
        return [
            "market_analysis",
            "research_results",
            "project_memory",
            "search_documents",
            "search_chunks",
            "codex_prompts",
        ]

    def build_codex_prompt_for_app(self, app_plan: dict[str, Any]) -> str:
        return "\n".join(
            [
                "You are continuing the existing Builder Core project.",
                "Project name: Builder Core",
                "Repo: https://github.com/jagangill001/builder-core",
                "Main folders:",
                "- backend/",
                "- frontend/",
                "",
                f"Build or extend this app concept: {app_plan['app_concept']}",
                "",
                "MVP FEATURES:",
                *[f"- {item}" for item in app_plan["mvp_features"]],
                "",
                "BACKEND ROUTES:",
                *[f"- {item}" for item in app_plan["backend_routes"]],
                "",
                "FRONTEND SCREENS:",
                *[f"- {item}" for item in app_plan["frontend_screens"]],
                "",
                "DATA COLLECTIONS:",
                *[f"- {item}" for item in app_plan["storage_collections"]],
                "",
                "LEGAL AND SAFETY RULES:",
                "- Write the code yourself.",
                "- Do not copy external copyrighted code.",
                "- Do not add secrets or credentials to the code.",
                "- Do not fake success, deployment, or research.",
                "",
                "TESTING:",
                "- Run frontend build if possible.",
                "- Run backend syntax or import checks if possible.",
                "- Report what still needs manual setup.",
                "",
                "Keep the implementation simple, safe, and beginner-friendly.",
            ]
        )

    def create_app_plan(
        self,
        goal: str,
        research_result: dict[str, Any] | None = None,
        market_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        app_name = f"{goal.title()[:40]} App".replace("  ", " ")
        app_concept = (
            f"A Builder Core-supported app for {goal} that turns saved research into usable analysis and action steps."
        )

        result = {
            "app_name": app_name,
            "app_concept": app_concept,
            "mvp_features": self.suggest_mvp_features(goal),
            "backend_routes": self.suggest_backend_routes(goal),
            "frontend_screens": self.suggest_frontend_screens(goal),
            "storage_collections": self.suggest_storage_collections(goal),
            "storage_plan": [
                "Use the generic storage layer so Firestore can be the primary backend when enabled.",
                "Keep local JSON fallback safe for development and honest about Cloud Run limits.",
            ],
            "next_steps": [
                "Review the MVP scope and remove anything non-essential.",
                "Use the generated Codex prompt to implement the first safe version manually.",
            ],
            "research_result": research_result or {},
            "market_analysis": market_analysis or {},
        }
        result["codex_prompt"] = self.build_codex_prompt_for_app(result)
        return self.storage.save_record("app_plans", result)
