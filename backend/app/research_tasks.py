from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.learning import LearningService
    from app.storage import ProjectStorageService
except ImportError:
    from learning import LearningService
    from storage import ProjectStorageService


RESEARCH_CATEGORIES = [
    "general",
    "coding",
    "law",
    "market",
    "exam",
    "politics",
    "history",
    "language",
    "project",
]

SUPPORTED_SOURCES = ["web", "user_notes", "memory"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchTaskService:
    def __init__(self, storage: ProjectStorageService, learning: LearningService) -> None:
        self.storage = storage
        self.learning = learning

    def create_task(
        self,
        topic: str,
        goal: str,
        category: str,
        sources: list[str],
        run_now: bool,
    ) -> dict[str, Any]:
        normalized_category = category if category in RESEARCH_CATEGORIES else "general"
        normalized_sources = [source for source in sources if source in SUPPORTED_SOURCES] or ["memory"]

        task = {
            "research_id": f"research_{uuid4().hex[:12]}",
            "topic": topic,
            "goal": goal,
            "category": normalized_category,
            "sources": normalized_sources,
            "status": "running" if run_now else "created",
            "summary": "Research task created and waiting to run.",
            "findings": [],
            "limitations": [],
            "next_steps": [],
            "web_connected": False,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }

        if run_now:
            task = self._run_task(task)

        saved = self.storage.save_research_task(task)
        self.storage.save_project_memory(
            {
                "type": "research_task",
                "note": f"Saved research task for {topic}",
                "research_id": saved["research_id"],
                "category": normalized_category,
                "sources": normalized_sources,
            }
        )
        return saved

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.storage.get_research_tasks(limit)

    def get_task(self, research_id: str) -> dict[str, Any] | None:
        return self.storage.get_research_task(research_id)

    def run_web_research(self, topic: str, goal: str) -> dict[str, Any]:
        return {
            "connected": False,
            "summary": "Web research is not connected yet.",
            "topic": topic,
            "goal": goal,
        }

    def summarize_sources(self, sources: list[str], topic: str, goal: str) -> dict[str, Any]:
        findings: list[str] = []
        limitations: list[str] = []

        if "memory" in sources:
            memory = self.storage.get_project_memory(5)
            if memory:
                for entry in memory[:3]:
                    note = str(entry.get("note") or entry.get("command") or "Saved memory").strip()
                    findings.append(f"Memory note: {note}")
            else:
                limitations.append("No saved project memory was available for this research task.")

        if "user_notes" in sources:
            limitations.append("User notes were requested as a source, but no note payload was provided yet in this build.")

        if "web" in sources:
            limitations.append("Web research is not connected yet. This task was saved and can use provided notes/memory only.")

        if not findings:
            findings.append(f"Research goal captured: {goal}")
            findings.append(f"Topic saved for follow-up: {topic}")

        next_steps = [
            "Review the saved findings and decide whether a Codex prompt or a manual research pass should come next.",
            "If you need live internet facts, connect real web research later instead of guessing now.",
        ]

        return {
            "findings": findings[:8],
            "limitations": list(dict.fromkeys(limitations))[:6],
            "next_steps": next_steps,
        }

    def save_research_result(self, result: dict[str, Any]) -> dict[str, Any]:
        saved_result = self.storage.save_research_result(result)
        self.create_research_lesson(result)
        return saved_result

    def create_research_lesson(self, result: dict[str, Any]) -> dict[str, Any]:
        summary = str(result.get("summary") or "Research task completed.").strip()
        lesson = {
            "task_id": result.get("research_id"),
            "command": result.get("topic"),
            "what_happened": result.get("findings", []),
            "files_changed": [],
            "error": (result.get("limitations") or [None])[0],
            "lesson_learned": summary,
            "next_recommendation": (result.get("next_steps") or ["Review the findings and choose the next safe action."])[0],
            "status": result.get("status", "completed"),
            "created_at": utc_now_iso(),
        }
        return self.storage.save_lesson(lesson)

    def _run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        source_summary = self.summarize_sources(task["sources"], task["topic"], task["goal"])
        web_message = self.run_web_research(task["topic"], task["goal"])

        summary = (
            "Web research is not connected yet. This task was saved and can use provided notes/memory only."
            if "web" in task["sources"]
            else "Research task completed using saved memory and the current local context."
        )

        completed = {
            **task,
            "status": "completed",
            "summary": summary,
            "findings": source_summary["findings"],
            "limitations": list(dict.fromkeys(source_summary["limitations"] + [web_message["summary"] if "web" in task["sources"] else ""]))[:6],
            "next_steps": source_summary["next_steps"],
            "updated_at": utc_now_iso(),
            "web_connected": False,
        }
        self.save_research_result(completed)
        return completed
