from __future__ import annotations

from app.brain.context_manager import has_useful_context

AMBIGUOUS_SHORT_REQUESTS = {
    "fix it",
    "fix this",
    "that one",
    "what about this",
    "make it better",
    "do it",
    "update it",
    "change it",
}


def followup_questions(message: str, history: list[dict[str, str]]) -> list[str]:
    normalized = _normalize(message)
    if not normalized:
        return ["What would you like Builder Core to do?"]
    if normalized in AMBIGUOUS_SHORT_REQUESTS and not has_useful_context(history):
        return ["Which part do you want me to fix?"]
    if len(normalized.split()) <= 2 and normalized in {"this", "that", "it"} and not has_useful_context(history):
        return ["What should Builder Core focus on?"]
    return []


def _normalize(message: str) -> str:
    return " ".join((message or "").lower().replace("-", " ").replace("_", " ").split())
