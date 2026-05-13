from __future__ import annotations

from fastapi import APIRouter, Depends

from app.audit.audit_log import record_audit
from app.auth.auth import AuthContext
from app.auth.dependencies import require_admin
from app.brain.recommendations import recommended_next_steps
from app.memory.lessons import list_lessons, repeated_error_summary
from app.memory.project_memory import get_project_summary, update_project_summary

router = APIRouter(prefix="/project", tags=["project"])


@router.get("/summary")
def project_summary() -> dict[str, object]:
    return get_project_summary()


@router.post("/memory/update")
def update_memory(payload: dict[str, object], context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = {"ok": True, "summary": update_project_summary(payload)}
    record_audit(
        action="project_memory_update",
        route="/project/memory/update",
        success=True,
        auth=context,
        warnings=[],
        errors=[],
    )
    return result


@router.get("/lessons")
def project_lessons() -> dict[str, object]:
    return {"items": list_lessons(), "details": repeated_error_summary()}


@router.get("/recommendations")
def project_recommendations() -> dict[str, object]:
    return {"items": recommended_next_steps()}
