from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth.auth import AuthContext
from app.auth.dependencies import get_auth_context
from app.tasks.task_engine import task_engine
from app.tasks.task_models import TaskCreateRequest, model_to_dict
from app.tasks.task_store import task_store
from app.workflows.workflow_graph import build_workflow_graph

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create")
def create_task(payload: TaskCreateRequest, context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
    task = task_engine.create_and_process(payload, auth=context)
    return model_to_dict(task)


@router.get("/{task_id}")
def get_task(task_id: str) -> dict[str, object]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found."})
    return model_to_dict(task)


@router.get("/{task_id}/logs")
def get_task_logs(task_id: str) -> dict[str, object]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found."})
    return {"task_id": task_id, "items": [model_to_dict(log) for log in task.logs]}


@router.get("/{task_id}/workflow")
def get_task_workflow(task_id: str) -> dict[str, object]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found."})
    return build_workflow_graph(task)


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str) -> dict[str, object]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found."})
    return {
        "ok": False,
        "task_id": task_id,
        "implemented": False,
        "message": "Task cancellation is a placeholder. Immediate tasks normally finish before they can be cancelled.",
    }


@router.post("/{task_id}/retry")
def retry_task(task_id: str, context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "message": "Task not found."})
    retry_payload = TaskCreateRequest(
        message=task.original_message,
        priority=task.priority,
        timeout_seconds=task.timeout_seconds,
    )
    new_task = task_engine.create_and_process(retry_payload, auth=context)
    return {
        "ok": True,
        "message": "Retry created as a new backend-owned task.",
        "original_task_id": task_id,
        "task": model_to_dict(new_task),
    }
