from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services import builder_service, memory_service, project_service


def _pending_test_result() -> dict[str, Any]:
    return {
        "status": "pending",
        "summary": "Waiting for tester bee.",
        "checks": [],
    }


@dataclass(slots=True)
class WorkflowState:
    task_id: str
    message: str
    project_name: str
    forced_intent: str | None = None
    worker_mode: str = "local"
    intent: str = "chat"
    memory: dict[str, Any] = field(default_factory=dict)
    inspection: dict[str, Any] | None = None
    run_info: dict[str, Any] | None = None
    plan_data: dict[str, Any] = field(default_factory=dict)
    files_changed: list[str] = field(default_factory=list)
    test_result: dict[str, Any] = field(default_factory=_pending_test_result)
    learned_items: list[str] = field(default_factory=list)
    proposed_improvements: list[str] = field(default_factory=list)
    assistant_reply: str = ""
    workflow_trace: list[dict[str, str]] = field(default_factory=list)
    version_snapshot: dict[str, Any] | None = None
    memory_snapshot: dict[str, Any] = field(default_factory=dict)
    repair_attempts: int = 0
    max_repair_attempts: int = 2
    repair_history: list[dict[str, Any]] = field(default_factory=list)
    codex_task: dict[str, Any] | None = None

    def add_trace(self, bee_name: str, summary: str) -> None:
        self.workflow_trace.append({"bee": bee_name, "summary": summary})


def build_workflow_context(
    task_id: str,
    message: str,
    project_name: str | None,
    forced_intent: str | None = None,
    worker_mode: str = "local",
) -> WorkflowState:
    clean_project_name = project_service.normalize_project_name(project_name)
    clean_message = message.strip()
    memory = memory_service.get_project_memory(clean_project_name)
    inspection = builder_service.inspect_project(clean_project_name)

    return WorkflowState(
        task_id=task_id,
        message=clean_message,
        project_name=clean_project_name,
        forced_intent=forced_intent,
        worker_mode=worker_mode,
        memory=memory,
        inspection=inspection,
    )
