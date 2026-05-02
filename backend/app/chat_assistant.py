from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.learning import LearningService
    from app.model_router import ModelRouterService
    from app.private_search import PrivateSearchService
    from app.storage import ProjectStorageService
except ImportError:
    from learning import LearningService
    from model_router import ModelRouterService
    from private_search import PrivateSearchService
    from storage import ProjectStorageService


ASSISTANT_MODES = [
    "general",
    "coding",
    "research",
    "law",
    "market",
    "exam",
    "project",
    "creative",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatAssistantService:
    def __init__(
        self,
        storage: ProjectStorageService,
        learning: LearningService,
        model_router: ModelRouterService,
        private_search: PrivateSearchService,
    ) -> None:
        self.storage = storage
        self.learning = learning
        self.model_router = model_router
        self.private_search = private_search

    def build_status(self) -> dict[str, Any]:
        return self.model_router.get_active_model_status()

    def chat(self, message: str, mode: str, save_to_memory: bool) -> dict[str, Any]:
        normalized_mode = mode if mode in ASSISTANT_MODES else "general"
        chat_id = f"chat_{uuid4().hex[:12]}"
        created_at = utc_now_iso()

        memory = self.storage.get_project_memory(6)
        assistant_memory = self.storage.get_assistant_memory(6)
        lessons = self.learning.get_lessons(6)
        latest_summary = self.storage.get_latest_summary()
        history = self.storage.get_chat_history(8)
        search_result = self.private_search.search_private_index(message, limit=5)
        memory_used = self._build_memory_used(memory, assistant_memory, lessons, latest_summary, search_result)
        suggestions = self._build_suggestions(normalized_mode, message)
        next_actions = self._build_next_actions(normalized_mode, message, latest_summary, search_result)

        reply = self.model_router.generate_reply(
            prompt=message,
            context={
                "mode": normalized_mode,
                "memory": memory + assistant_memory,
                "lessons": lessons,
                "latest_summary": latest_summary or {},
                "recent_history": history,
                "workflow": f"assistant_{normalized_mode}",
                "private_search": search_result,
            },
        )

        self.storage.save_chat_message(
            {
                "chat_id": chat_id,
                "role": "user",
                "mode": normalized_mode,
                "message": message,
                "created_at": created_at,
            }
        )
        self.storage.save_chat_message(
            {
                "chat_id": chat_id,
                "role": "assistant",
                "mode": normalized_mode,
                "message": reply,
                "suggestions": suggestions,
                "next_actions": next_actions,
                "memory_used": memory_used,
                "search_used": {
                    "results_count": search_result.get("results_count", 0),
                    "top_sources": search_result.get("top_sources", []),
                },
                "created_at": created_at,
            }
        )

        saved_to_memory = False
        if save_to_memory:
            note = self.storage.save_assistant_memory(
                {
                    "type": "assistant_chat",
                    "mode": normalized_mode,
                    "source": "assistant_chat",
                    "user_message": message,
                    "assistant_reply": reply,
                    "note": f"Saved assistant chat for {normalized_mode} mode.",
                    "suggestions": suggestions,
                    "next_actions": next_actions,
                }
            )
            self.storage.save_project_memory(
                {
                    "type": "assistant_chat",
                    "mode": normalized_mode,
                    "note": f"Saved assistant chat about: {message[:160]}",
                    "chat_id": chat_id,
                    "assistant_memory_id": note["id"],
                }
            )
            saved_to_memory = True

        return {
            "chat_id": chat_id,
            "reply": reply,
            "suggestions": suggestions,
            "memory_used": memory_used,
            "saved_to_memory": saved_to_memory,
            "next_actions": next_actions,
            "created_at": created_at,
            "assistant_status": self.build_status(),
        }

    def get_history(self, limit: int = 30) -> list[dict[str, Any]]:
        return self.storage.get_chat_history(limit)

    def generate_ideas(self, topic: str, goal: str) -> dict[str, Any]:
        context = {
            "project_name": "Builder Core",
            "memory": self.storage.get_project_memory(6),
            "lessons": self.learning.get_lessons(6),
        }
        idea_lines = self.model_router.generate_ideas(topic, context)
        ideas = []
        for index, line in enumerate(idea_lines):
            ideas.append(
                {
                    "idea_title": line,
                    "why_it_is_useful": "This idea keeps Builder Core useful without pretending it already has full automation.",
                    "difficulty": "Low" if index == 0 else "Medium",
                    "possible_next_step": "Turn the idea into a research task or Codex prompt.",
                    "risk_or_limitation": "Needs real saved evidence before the final decision should be trusted.",
                }
            )

        best_idea = ideas[0] if ideas else {
            "idea_title": "Refine the goal",
            "why_it_is_useful": "A clearer goal leads to a better prompt.",
            "difficulty": "Low",
            "possible_next_step": "Clarify the goal in one sentence.",
            "risk_or_limitation": "The topic is still too broad.",
        }
        return {
            "ideas": ideas,
            "best_idea": best_idea["idea_title"],
            "why": best_idea["why_it_is_useful"],
            "next_steps": [idea["possible_next_step"] for idea in ideas[:3]],
            "created_at": utc_now_iso(),
        }

    def _build_suggestions(self, mode: str, message: str) -> list[str]:
        shared = [
            "Save the important part of this discussion to memory if you want Builder Core to reuse it later.",
            "Generate a Codex prompt if you are ready to turn this into a repo change.",
        ]
        mode_specific = {
            "research": ["Create a research task so the findings and limitations stay organized."],
            "market": ["Use the market-analysis workflow so Builder Core can separate evidence from assumptions."],
            "coding": ["Turn the idea into a small implementation plan before changing multiple files."],
        }
        return (mode_specific.get(mode, []) + shared)[:5]

    def _build_next_actions(
        self,
        mode: str,
        message: str,
        latest_summary: dict[str, Any] | None,
        search_result: dict[str, Any],
    ) -> list[str]:
        actions = [
            "I can research this when you ask me.",
            "I can save this to memory.",
            "I can create a research task.",
            "I can use previous memory and lessons.",
            "I do not automatically know new internet information unless research is run.",
        ]
        if isinstance(latest_summary, dict):
            next_step = latest_summary.get("next_recommended_step")
            if isinstance(next_step, str) and next_step.strip():
                actions.insert(0, next_step)
        if search_result.get("results_count", 0) == 0:
            actions.append("Add notes, documents, or safe URL ingests if you want stronger private-search context.")
        return list(dict.fromkeys(actions))[:6]

    def _build_memory_used(
        self,
        memory: list[dict[str, Any]],
        assistant_memory: list[dict[str, Any]],
        lessons: list[dict[str, Any]],
        latest_summary: dict[str, Any] | None,
        search_result: dict[str, Any],
    ) -> list[str]:
        items: list[str] = []
        for entry in memory[:3]:
            note = str(entry.get("note") or entry.get("command") or "").strip()
            if note:
                items.append(note)
        for entry in assistant_memory[:2]:
            note = str(entry.get("note") or entry.get("user_message") or "").strip()
            if note:
                items.append(note)
        for lesson in lessons[:2]:
            text = str(lesson.get("lesson_learned") or "").strip()
            if text:
                items.append(text)
        if isinstance(latest_summary, dict):
            text = str(latest_summary.get("next_recommended_step") or "").strip()
            if text:
                items.append(text)
        for source in search_result.get("top_sources", [])[:2]:
            if isinstance(source, str) and source.strip():
                items.append(f"Private search source: {source}")
        return list(dict.fromkeys(items))[:8]
