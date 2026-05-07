from __future__ import annotations

from typing import Literal

from app.models.command_models import CommandIntent

QuestionMode = Literal["clarify", "direct_answer", "live_search", "weather", "news", "general_chat"]

LIVE_MARKERS = (
    "current",
    "latest",
    "today",
    "tonight",
    "now",
    "recent",
    "new",
    "breaking",
    "price",
    "stock",
    "election",
    "government",
    "prime minister now",
    "who is prime minister",
    "release",
    "version",
    "docs",
    "documentation",
    "source check",
    "verify",
    "fact check",
    "fake news",
    "is this true",
    "what happened",
)

WEATHER_MARKERS = ("weather", "temperature", "forecast", "rain today", "snow today")
NEWS_MARKERS = ("news", "headline", "headlines", "breaking")
DIRECT_STARTERS = (
    "what is",
    "what are",
    "who was",
    "how does",
    "how do",
    "explain",
    "teach me",
    "define",
    "tell me about",
)


def classify_question(message: str, intent: CommandIntent) -> dict[str, object]:
    normalized = _normalize(message)
    if not normalized:
        return {"mode": "clarify", "live_search_needed": False, "reason": "empty_message"}

    if any(marker in normalized for marker in WEATHER_MARKERS):
        return {"mode": "weather", "live_search_needed": True, "reason": "weather_query"}

    if any(marker in normalized for marker in NEWS_MARKERS):
        return {"mode": "news", "live_search_needed": True, "reason": "news_query"}

    if intent in {"research", "decision_analysis"}:
        return {"mode": "live_search", "live_search_needed": True, "reason": f"{intent}_intent"}

    if any(marker in normalized for marker in LIVE_MARKERS):
        return {"mode": "live_search", "live_search_needed": True, "reason": "current_or_verification_marker"}

    if normalized.startswith(DIRECT_STARTERS) or intent in {"teaching", "coding", "cloud"}:
        return {"mode": "direct_answer", "live_search_needed": False, "reason": "stable_direct_question"}

    if normalized.endswith("?"):
        return {"mode": "direct_answer", "live_search_needed": False, "reason": "stable_question"}

    return {"mode": "general_chat", "live_search_needed": False, "reason": "general_chat"}


def _normalize(message: str) -> str:
    return " ".join((message or "").lower().replace("-", " ").replace("_", " ").split())
