from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.memory import append_entry, load_json, recent_entries
from app.legacy_models import Project

MEMORY_TYPE = "short_term"


def record_workflow(
    db: Session,
    project: Project,
    *,
    task_id: str,
    user_message: str,
    assistant_reply: str,
    intent: str,
    result_status: str,
    summary: str,
    files_changed: list[str],
) -> None:
    append_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key=f"workflow:{task_id}",
        value={
            "task_id": task_id,
            "user_message": user_message,
            "assistant_reply": assistant_reply,
            "intent": intent,
            "result_status": result_status,
            "summary": summary,
            "files_changed": files_changed[:12],
        },
    )


def recent_history(db: Session, project: Project, limit: int = 6) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for entry in recent_entries(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        limit=limit,
    ):
        payload = load_json(entry.value_json, {})
        user_message = payload.get("user_message")
        assistant_reply = payload.get("assistant_reply")
        if user_message:
            history.append({"role": "user", "content": user_message})
        if assistant_reply:
            history.append({"role": "assistant", "content": assistant_reply})
    return history[-12:]
