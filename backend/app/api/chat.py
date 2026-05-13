from __future__ import annotations

from fastapi import APIRouter

from app.core.commander import commander
from app.database import SessionLocal
from app.schemas import BuildRequest, ChatRequest
from app.services import project_service

router = APIRouter()


def _empty_response(project_name: str, summary: str) -> dict:
    return {
        "ok": False,
        "assistant_reply": summary,
        "intent": "chat",
        "project_name": project_name,
        "worker_mode": "local",
        "plan": [],
        "files_changed": [],
        "files_created": [],
        "test_result": {
            "status": "failed",
            "summary": summary,
            "checks": [],
        },
        "build_triggered": False,
        "learned_items": [],
        "proposed_improvements": [],
        "workflow_trace": [],
        "codex_task": None,
    }


def execute_goal(
    message: str,
    project_name: str | None,
    forced_intent: str | None = None,
    worker_mode: str = "local",
) -> dict:
    clean_project_name = project_service.normalize_project_name(project_name)
    clean_message = message.strip()
    if not clean_message:
        return _empty_response(clean_project_name, "Please enter a message.")

    db = SessionLocal()
    try:
        result = commander.execute(
            message=clean_message,
            project_name=clean_project_name,
            forced_intent=forced_intent,
            worker_mode=worker_mode,
        )

        if result.get("build_triggered"):
            project = project_service.get_or_create_project(db, clean_project_name)
            project_service.record_request(
                db=db,
                project=project,
                instruction=clean_message,
                status=result["test_result"]["status"],
                plan=result["plan"],
                files_changed=result["files_changed"],
            )

        return result
    finally:
        db.close()


@router.post("/chat")
def chat(payload: ChatRequest):
    return execute_goal(
        message=payload.message,
        project_name=payload.project_name,
        worker_mode=payload.worker_mode,
    )


@router.post("/plan")
def create_plan(payload: BuildRequest):
    result = execute_goal(
        message=payload.instruction,
        project_name=payload.project_name,
        forced_intent="build",
        worker_mode="local",
    )
    return {
        "ok": result["ok"],
        "message": "Plan created successfully." if result["ok"] else result["assistant_reply"],
        "instruction": payload.instruction.strip(),
        "project_name": result["project_name"],
        "module_key": result.get("module_key"),
        "route_path": result.get("route_path"),
        "title": result.get("title"),
        "status": result["test_result"]["status"],
        "plan": result["plan"],
        "created_files": result["files_changed"],
        "files_changed": result["files_changed"],
        "test_result": result["test_result"],
        "learned_items": result["learned_items"],
        "proposed_improvements": result["proposed_improvements"],
    }
