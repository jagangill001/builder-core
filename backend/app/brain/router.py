from __future__ import annotations

from dataclasses import dataclass, field


INTENTS = {
    "stable_question",
    "current_question",
    "weather_question",
    "news_question",
    "coding_task",
    "github_task",
    "codex_task",
    "deployment_task",
    "project_task",
    "memory_question",
    "admin_task",
    "unknown",
}


@dataclass(frozen=True, slots=True)
class RouteDecision:
    intent: str
    workflow: str
    requires_live_search: bool = False
    needs_follow_up: bool = False
    follow_up_question: str | None = None
    confidence: float = 0.5
    reasons: list[str] = field(default_factory=list)


def classify_command(message: str) -> RouteDecision:
    normalized = normalize_message(message)
    if not normalized:
        return RouteDecision(
            intent="unknown",
            workflow="clarify",
            needs_follow_up=True,
            follow_up_question="What would you like Builder Core to do?",
            confidence=1.0,
            reasons=["Empty command."],
        )

    if _contains_any(normalized, ("weather", "temperature", "forecast", "rain today", "snow today")):
        return RouteDecision("weather_question", "weather_answer", True, confidence=0.9, reasons=["Weather keyword detected."])
    if _contains_any(normalized, ("news", "headline", "latest story", "breaking", "current events")):
        return RouteDecision("news_question", "news_answer", True, confidence=0.9, reasons=["News/current events keyword detected."])
    if _contains_any(normalized, ("today", "latest", "right now", "current", "recent", "this week", "this month", "2026")):
        return RouteDecision("current_question", "live_answer", True, confidence=0.75, reasons=["Time-sensitive wording detected."])
    if _contains_any(normalized, ("github", "issue", "pull request", "pr ", "commit", "branch", "workflow run")):
        return RouteDecision("github_task", "github_workflow", confidence=0.85, reasons=["GitHub workflow keyword detected."])
    if _contains_any(normalized, ("codex", "coding agent", "package this task", "package task")):
        return RouteDecision("codex_task", "codex_package", confidence=0.9, reasons=["Codex packaging keyword detected."])
    if _contains_any(normalized, ("deploy", "deployment", "cloud run", "rollback", "release", "ci/cd", "github actions")):
        return RouteDecision("deployment_task", "deployment_status", confidence=0.85, reasons=["Deployment keyword detected."])
    if _contains_any(normalized, ("admin", "authorization", "auth", "token", "role", "owner mode")):
        return RouteDecision("admin_task", "admin_status", confidence=0.75, reasons=["Admin/auth keyword detected."])
    if _contains_any(normalized, ("memory", "remember", "summary", "summarize project", "project progress")):
        return RouteDecision("memory_question", "memory_answer", confidence=0.8, reasons=["Memory or summary keyword detected."])
    if _contains_any(normalized, ("builder core status", "project status", "what should i build next", "connector status", "integration status")):
        return RouteDecision("project_task", "project_status", confidence=0.85, reasons=["Project command keyword detected."])
    if _contains_any(normalized, ("code", "frontend", "backend", "fastapi", "next.js", "nextjs", "bug", "fix", "test", "typescript", "python")):
        return RouteDecision("coding_task", "coding_planning", confidence=0.8, reasons=["Coding keyword detected."])
    if _looks_like_question(normalized):
        return RouteDecision("stable_question", "stable_answer", confidence=0.65, reasons=["Question without time-sensitive wording."])

    return RouteDecision(
        intent="unknown",
        workflow="clarify",
        needs_follow_up=True,
        follow_up_question="Should Builder Core answer a question, inspect project status, or prepare an automation task?",
        confidence=0.35,
        reasons=["No clear command category matched."],
    )


def normalize_message(message: str) -> str:
    return " ".join(message.strip().lower().replace("_", " ").replace("-", " ").split())


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _looks_like_question(value: str) -> bool:
    return value.endswith("?") or value.startswith(("what ", "who ", "why ", "how ", "when ", "where ", "is ", "are ", "does ", "do "))
