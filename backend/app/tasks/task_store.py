from __future__ import annotations

from threading import RLock
from uuid import uuid4

from app.db.repository import repository
from app.tasks.task_models import SourceModel, TaskCreateRequest, TaskLog, TaskRecord, TaskSummary, utc_now


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = RLock()

    def create(self, payload: TaskCreateRequest) -> TaskRecord:
        now = utc_now()
        task = TaskRecord(
            task_id=f"task_{uuid4().hex[:12]}",
            original_message=payload.message,
            normalized_message=normalize_message(payload.message),
            status="received",
            progress=0,
            current_stage="received",
            priority=payload.priority,
            timeout_seconds=payload.timeout_seconds,
            created_at=now,
            updated_at=now,
        )
        task.logs.append(TaskLog(stage="received", message="Task received by backend."))
        with self._lock:
            self._tasks[task.task_id] = task
        repository.save_task(task)
        repository.append_task_log(task.task_id, task.logs[-1])
        return task

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            if task_id in self._tasks:
                return self._tasks[task_id]
        task = repository.get_task(task_id)
        if task:
            with self._lock:
                self._tasks[task_id] = task
        return task

    def save(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = utc_now()
        with self._lock:
            self._tasks[task.task_id] = task
        repository.save_task(task)
        return task

    def advance(self, task_id: str, *, stage: str, progress: int, message: str, status: str = "running") -> TaskRecord:
        task = self._require(task_id)
        task.current_stage = stage
        task.progress = max(0, min(progress, 100))
        task.status = status
        log = TaskLog(stage=stage, message=message)
        task.logs.append(log)
        repository.append_task_log(task_id, log)
        return self.save(task)

    def add_warning(self, task_id: str, warning: str) -> TaskRecord:
        task = self._require(task_id)
        if warning and warning not in task.warnings:
            task.warnings.append(warning)
        return self.save(task)

    def add_error(self, task_id: str, error: str) -> TaskRecord:
        task = self._require(task_id)
        if error and error not in task.errors:
            task.errors.append(error)
        return self.save(task)

    def set_result(
        self,
        task_id: str,
        *,
        result: dict,
        sources: list[SourceModel] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> TaskRecord:
        task = self._require(task_id)
        task.result = result
        if sources is not None:
            task.sources = sources
        for warning in warnings or []:
            if warning not in task.warnings:
                task.warnings.append(warning)
        for error in errors or []:
            if error not in task.errors:
                task.errors.append(error)
        return self.save(task)

    def complete(self, task_id: str, summary: TaskSummary) -> TaskRecord:
        task = self._require(task_id)
        task.summary = summary
        task.status = "completed"
        task.current_stage = "completed"
        task.progress = 100
        task.logs.append(TaskLog(stage="completed", message="Task completed by backend."))
        repository.save_task_summary(task_id, summary)
        repository.append_task_log(task_id, task.logs[-1])
        return self.save(task)

    def fail(self, task_id: str, summary: TaskSummary) -> TaskRecord:
        task = self._require(task_id)
        task.summary = summary
        task.status = "failed"
        task.current_stage = "failed"
        task.progress = 100
        task.logs.append(TaskLog(stage="failed", level="error", message="Task failed or was blocked by backend."))
        repository.save_task_summary(task_id, summary)
        repository.append_task_log(task_id, task.logs[-1])
        return self.save(task)

    def _require(self, task_id: str) -> TaskRecord:
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")
        return task


def normalize_message(message: str) -> str:
    return " ".join(message.strip().lower().replace("_", " ").replace("-", " ").split())


task_store = TaskStore()
