from __future__ import annotations

from typing import Any

from app.auth.auth import AuthContext
from app.brain.router import RouteDecision
from app.connectors.codex_bridge import CodexBridgeConnector
from app.connectors.github import GitHubConnector
from app.connectors.news import NewsConnector
from app.connectors.registry import connector_statuses
from app.connectors.search import SearchConnector
from app.connectors.weather import WeatherConnector
from app.deployment.deployment_status import deployment_checklist, deployment_status
from app.memory.project_memory import get_project_summary


STABLE_ANSWERS = {
    "what is builder core": "Builder Core is your AI command center: a backend-owned task system with routing, safety checks, connector awareness, project memory, and a frontend dashboard.",
    "what is fastapi": "FastAPI is a Python web framework for building APIs with type hints and automatic OpenAPI documentation.",
    "what is next.js": "Next.js is a React framework used for routing, rendering, and deploying web applications.",
    "what is github": "GitHub is a platform for hosting Git repositories, issues, pull requests, Actions workflows, and collaboration metadata.",
    "capital of france": "The capital of France is Paris.",
}


class AnswerBrain:
    def answer(self, message: str, route: RouteDecision, auth: AuthContext | None = None) -> dict[str, Any]:
        auth_context = auth or AuthContext()
        normalized = message.strip().lower().rstrip("?")
        if route.needs_follow_up:
            return self._follow_up(route)
        if route.intent == "stable_question":
            return self._stable_answer(normalized)
        if route.intent == "current_question":
            return self._connector_answer(SearchConnector().query(message), "search")
        if route.intent == "weather_question":
            return self._connector_answer(WeatherConnector().query(message), "weather")
        if route.intent == "news_question":
            return self._connector_answer(NewsConnector().query(message), "news")
        if route.intent == "project_task":
            return self._project_status()
        if route.intent == "memory_question":
            return self._project_status()
        if route.intent == "deployment_task":
            return self._deployment_answer()
        if route.intent == "codex_task":
            return self._codex_package(message, auth_context)
        if route.intent == "github_task":
            return self._github_task(message, auth_context)
        if route.intent == "coding_task":
            return self._coding_task(message, auth_context)
        if route.intent == "admin_task":
            return self._admin_answer(auth_context)
        return self._follow_up(route)

    def _stable_answer(self, normalized: str) -> dict[str, Any]:
        for key, answer in STABLE_ANSWERS.items():
            if key in normalized:
                return {
                    "message": answer,
                    "answer_type": "stable",
                    "requires_live_search": False,
                    "connectors_used": [],
                    "next_step": "Ask a project command when you want Builder Core to act on the repo.",
                }
        return {
            "message": "This looks like a stable question, but Builder Core does not have a confident built-in answer yet.",
            "answer_type": "stable",
            "requires_live_search": False,
            "connectors_used": [],
            "next_step": "Ask one clearer follow-up question or configure search for broader answers.",
            "warnings": ["Stable answer coverage is intentionally small for now."],
        }

    def _connector_answer(self, connector_result: dict[str, Any], connector_name: str) -> dict[str, Any]:
        return {
            "message": connector_result.get("message", ""),
            "answer_type": connector_name,
            "requires_live_search": True,
            "connectors_used": [connector_name],
            "sources": connector_result.get("sources", []),
            "warnings": connector_result.get("warnings", []),
            "next_step": "Configure the missing provider adapter before relying on this class of answer.",
        }

    def _project_status(self) -> dict[str, Any]:
        return {
            "message": "Builder Core project summary loaded from backend memory.",
            "answer_type": "project",
            "project_summary": get_project_summary(),
            "connectors": connector_statuses(),
            "connectors_used": ["memory", "connector_registry"],
            "next_step": "Use the command center to create a task, inspect connectors, or package coding work for Codex.",
        }

    def _deployment_answer(self) -> dict[str, Any]:
        return {
            "message": "Deployment awareness is available. Rollback is an honest placeholder until real Cloud Run control is implemented.",
            "answer_type": "deployment",
            "deployment_status": deployment_status(),
            "deployment_checklist": deployment_checklist(),
            "connectors_used": ["deployment"],
            "next_step": "Configure public service URLs and GitHub Actions access to make deployment checks richer.",
        }

    def _codex_package(self, message: str, auth: AuthContext) -> dict[str, Any]:
        if auth.role not in {"admin", "owner"}:
            return {
                "message": "Codex packaging requires admin mode. No package was created.",
                "answer_type": "codex_package",
                "auth_required": True,
                "connectors_used": ["auth"],
                "warnings": ["Admin-only Codex package action was not executed."],
                "next_step": "Enter the backend ADMIN_TOKEN in the frontend admin field, then retry.",
            }
        package = CodexBridgeConnector().package_task(message)
        return {
            "message": package["message"],
            "answer_type": "codex_package",
            "codex_package": package["package"],
            "connectors_used": ["codex_bridge"],
            "warnings": ["Real Codex execution is not wired into Builder Core yet."],
            "next_step": "Review the package, then send it through a real Codex/GitHub flow when configured.",
        }

    def _github_task(self, message: str, auth: AuthContext) -> dict[str, Any]:
        github = GitHubConnector()
        status = github.status()
        if "create" in message.lower() and "issue" in message.lower():
            if auth.role not in {"admin", "owner"}:
                return {
                    "message": "Creating GitHub issues requires admin mode.",
                    "answer_type": "github",
                    "auth_required": True,
                    "connectors_used": ["github"],
                    "warnings": ["Admin-only GitHub write action was not executed."],
                    "next_step": "Enable admin mode, then use /integrations/github/create-issue or /github/issues.",
                }
            if not status.configured:
                return {
                    "message": "GitHub connector not configured, so no issue was created.",
                    "answer_type": "github",
                    "connectors_used": ["github"],
                    "warnings": [status.last_error or "GitHub runtime settings are incomplete."],
                    "next_step": "Set GitHub env vars on the backend, then retry.",
                }
        return {
            "message": "GitHub task recognized. Builder Core can report status now and perform write actions only through admin-protected endpoints.",
            "answer_type": "github",
            "github_status": status.as_dict(),
            "connectors_used": ["github"],
            "next_step": "Use the GitHub panel or admin endpoint for a specific repo action.",
        }

    def _coding_task(self, message: str, auth: AuthContext) -> dict[str, Any]:
        if auth.role not in {"admin", "owner"}:
            return {
                "message": "Coding task recognized. Codex packaging is admin-protected, so no package was created.",
                "answer_type": "coding",
                "auth_required": True,
                "connectors_used": ["auth"],
                "warnings": ["Real coding-agent execution is still a placeholder and packaging requires admin mode."],
                "next_step": "Enable admin mode or use this as a planning-only task.",
            }
        package = CodexBridgeConnector().package_task(message)
        return {
            "message": "Coding task recognized. Builder Core prepared a Codex-ready package; no code was changed by this task.",
            "answer_type": "coding",
            "codex_package": package["package"],
            "connectors_used": ["codex_bridge"],
            "warnings": ["Real coding-agent execution is still a placeholder."],
            "next_step": "Review the package and run the coding work through a real branch/PR workflow.",
        }

    def _admin_answer(self, auth: AuthContext) -> dict[str, Any]:
        return {
            "message": "Admin mode is enabled for this request." if auth.role in {"admin", "owner"} else "Admin mode is not enabled for this request.",
            "answer_type": "admin",
            "admin": {
                "role": auth.role,
                "authenticated": auth.authenticated,
                "admin_configured": auth.admin_configured,
                "token_visible": False,
            },
            "connectors_used": ["auth"],
            "next_step": "Use admin mode only for protected writes such as memory updates, GitHub writes, Codex packaging, and rollback placeholders.",
        }

    def _follow_up(self, route: RouteDecision) -> dict[str, Any]:
        return {
            "message": "Builder Core needs one clarification before it can proceed.",
            "answer_type": "clarification",
            "follow_up_question": route.follow_up_question or "What should Builder Core do next?",
            "connectors_used": [],
            "next_step": route.follow_up_question or "Send a clearer command.",
        }
