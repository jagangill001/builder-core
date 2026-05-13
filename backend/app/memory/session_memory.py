from __future__ import annotations

from typing import Any

from app.tasks.task_models import TaskRecord, TaskSummary


def summarize_task(task: TaskRecord) -> TaskSummary:
    result = task.result or {}
    return TaskSummary(
        what_user_asked=task.original_message,
        workflow_used=task.workflow,
        tools_connectors_used=list(result.get("connectors_used", [])),
        files_touched=[],
        result=str(result.get("message", "")),
        errors=task.errors,
        warnings=task.warnings,
        next_step=str(result.get("next_step", "")),
    )


def summary_as_public_dict(summary: TaskSummary | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    if hasattr(summary, "model_dump"):
        return summary.model_dump()
    return summary.dict()
