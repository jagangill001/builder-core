from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SelfImprovementService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def record_interaction_lesson(self, chat_or_task: dict[str, Any]) -> dict[str, Any]:
        user_message = str(chat_or_task.get("user_message") or chat_or_task.get("command") or "").strip()
        assistant_reply = str(chat_or_task.get("assistant_reply") or chat_or_task.get("summary") or "").strip()
        status = str(chat_or_task.get("status") or "saved").strip()
        errors = chat_or_task.get("errors") or []
        suggestions = chat_or_task.get("suggestions") or []

        what_failed = errors[0] if isinstance(errors, list) and errors else ""
        repeated_preferences = self._find_repeated_preferences(user_message)
        better_future_instruction = self.build_better_future_prompt(user_message or "Keep improving Builder Core safely.")

        entry = {
            "category": str(chat_or_task.get("category") or "chat"),
            "user_goal": chat_or_task.get("user_goal") or user_message,
            "selected_agent": chat_or_task.get("selected_agent"),
            "tools_used": chat_or_task.get("tools_used", []),
            "user_message": user_message,
            "assistant_reply": assistant_reply,
            "what_worked": (
                "Saved a clear interaction that Builder Core can reuse later."
                if assistant_reply
                else "Captured the request, but the reply quality still needs improvement."
            ),
            "what_failed": what_failed or "No major failure was recorded for this note.",
            "better_future_instruction": better_future_instruction,
            "repeated_user_preferences": repeated_preferences,
            "project_mistake": what_failed or "No recurring project mistake was detected in this note.",
            "project_lesson": self._build_project_lesson(status, suggestions),
            "missing_knowledge": chat_or_task.get("missing_knowledge", []),
            "security_warnings": chat_or_task.get("security_warnings", []),
            "storage_used": chat_or_task.get("storage_used"),
            "next_recommended_improvement": self.suggest_next_project_upgrade(),
            "created_at": utc_now_iso(),
        }
        return self.storage.save_self_improvement(entry)

    def get_improvement_notes(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.storage.get_self_improvements(limit)

    def build_better_future_prompt(self, user_goal: str) -> str:
        recent_notes = self.storage.get_self_improvements(5)
        preference_hints: list[str] = []
        for note in recent_notes:
            for item in note.get("repeated_user_preferences", []) if isinstance(note.get("repeated_user_preferences"), list) else []:
                text = str(item).strip()
                if text and text not in preference_hints:
                    preference_hints.append(text)

        hint_text = "; ".join(preference_hints[:3]) if preference_hints else "keep replies clear, safe, and practical"
        return (
            f"Future prompt improvement for this goal: {user_goal[:180]}. "
            f"Use saved lessons, stay honest about limits, and {hint_text}."
        )

    def suggest_next_project_upgrade(self) -> str:
        notes = self.storage.get_self_improvements(6)
        if not notes:
            return "Save a few assistant or research outcomes first so Builder Core can recommend sharper upgrades."

        if not self.storage.get_chat_history(5):
            return "Keep using the Builder Core Assistant so the project has more real chat history to learn from."

        if not self.storage.get_research_tasks(3):
            return "Create a real research task so Builder Core can start comparing chat ideas with saved research results."

        return "Review the latest assistant memory and lessons, then tighten the next Codex prompt with the strongest saved signals."

    def _find_repeated_preferences(self, user_message: str) -> list[str]:
        preferences: list[str] = []
        lowered = user_message.lower()

        if "simple" in lowered or "beginner" in lowered:
            preferences.append("Prefers simple, beginner-friendly explanations.")
        if "safe" in lowered or "honest" in lowered:
            preferences.append("Prefers safe and honest system behavior.")
        if "memory" in lowered or "remember" in lowered:
            preferences.append("Wants Builder Core to remember useful context for future tasks.")
        if "cloud" in lowered or "google cloud" in lowered:
            preferences.append("Prefers cloud-first architecture over laptop-only storage.")

        return preferences[:4]

    def _build_project_lesson(self, status: str, suggestions: list[Any]) -> str:
        if status.startswith("failed"):
            return "When a flow fails, Builder Core should surface the reason clearly instead of pretending progress."

        if suggestions:
            return "Good assistant replies should end with a small number of concrete next actions."

        return "Builder Core improves when it saves a clear summary, one lesson, and one next step from each interaction."
