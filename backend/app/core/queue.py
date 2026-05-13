from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class QueueTask:
    task_id: str
    project_name: str
    message: str
    forced_intent: str | None
    status: str = "queued"
    intent: str | None = None
    created_at: str = field(default_factory=_timestamp)
    updated_at: str = field(default_factory=_timestamp)
    bees_visited: list[str] = field(default_factory=list)
    notes: list[dict[str, str]] = field(default_factory=list)
    result_summary: str | None = None

    def note(self, bee_name: str, summary: str) -> None:
        if bee_name not in self.bees_visited:
            self.bees_visited.append(bee_name)
        self.notes.append({"bee": bee_name, "summary": summary})
        self.updated_at = _timestamp()


class BeeQueue:
    def __init__(self, history_limit: int = 20) -> None:
        self._history: deque[QueueTask] = deque(maxlen=history_limit)
        self._active: QueueTask | None = None
        self._lock = Lock()

    def enqueue(
        self,
        project_name: str,
        message: str,
        forced_intent: str | None = None,
    ) -> QueueTask:
        task = QueueTask(
            task_id=uuid4().hex[:12],
            project_name=project_name,
            message=message,
            forced_intent=forced_intent,
        )
        with self._lock:
            self._history.append(task)
        return task

    def mark_started(self, task_id: str, intent: str) -> None:
        task = self._find(task_id)
        if not task:
            return
        with self._lock:
            task.status = "running"
            task.intent = intent
            task.updated_at = _timestamp()
            self._active = task

    def note(self, task_id: str, bee_name: str, summary: str) -> None:
        task = self._find(task_id)
        if not task:
            return
        with self._lock:
            task.note(bee_name, summary)

    def mark_completed(self, task_id: str, result_summary: str) -> None:
        task = self._find(task_id)
        if not task:
            return
        with self._lock:
            task.status = "completed"
            task.result_summary = result_summary
            task.updated_at = _timestamp()
            if self._active and self._active.task_id == task_id:
                self._active = None

    def mark_failed(self, task_id: str, result_summary: str) -> None:
        task = self._find(task_id)
        if not task:
            return
        with self._lock:
            task.status = "failed"
            task.result_summary = result_summary
            task.updated_at = _timestamp()
            if self._active and self._active.task_id == task_id:
                self._active = None

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            active = self._serialize_task(self._active) if self._active else None
            recent = [self._serialize_task(task) for task in list(self._history)]
        return {
            "active_task": active,
            "recent_tasks": recent[-10:],
            "queued_count": len([task for task in recent if task["status"] == "queued"]),
        }

    def _find(self, task_id: str) -> QueueTask | None:
        for task in reversed(self._history):
            if task.task_id == task_id:
                return task
        return None

    @staticmethod
    def _serialize_task(task: QueueTask) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "project_name": task.project_name,
            "message": task.message,
            "forced_intent": task.forced_intent,
            "intent": task.intent,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "bees_visited": task.bees_visited,
            "notes": task.notes[-6:],
            "result_summary": task.result_summary,
        }
