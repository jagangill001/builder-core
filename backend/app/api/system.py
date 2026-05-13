from __future__ import annotations

from fastapi import APIRouter

from app.api.chat import execute_goal
from app.core.commander import commander
from app.services import codex_bridge_service
from app.schemas import ChatRequest

router = APIRouter(prefix="/system")


@router.get("/status")
def get_status():
    status = commander.status()
    status["codex_bridge"] = codex_bridge_service.bridge_status()
    return status


@router.post("/goal")
def submit_goal(payload: ChatRequest):
    return execute_goal(
        message=payload.message,
        project_name=payload.project_name,
        worker_mode=payload.worker_mode,
    )
