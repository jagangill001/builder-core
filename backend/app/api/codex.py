from __future__ import annotations

from fastapi import APIRouter

from app.core.commander import commander
from app.schemas import CodexTaskRequest
from app.services import codex_bridge_service

router = APIRouter(prefix="/codex")


@router.post("/task")
def create_codex_task(payload: CodexTaskRequest):
    return commander.execute(
        message=payload.message,
        project_name=payload.project_name or "Default Project",
        worker_mode=payload.worker_mode,
    )


@router.get("/task-status")
def get_codex_task_status(task_id: str | None = None, project_name: str | None = None):
    if task_id:
        task = codex_bridge_service.get_task_status(task_id)
        return {
            "ok": task is not None,
            "task": task,
            "bridge": codex_bridge_service.bridge_status(),
        }

    return {
        "ok": True,
        "items": codex_bridge_service.list_task_statuses(project_name=project_name),
        "bridge": codex_bridge_service.bridge_status(),
    }
