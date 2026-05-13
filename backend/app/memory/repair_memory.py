from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.memory import append_entry
from app.legacy_models import Project, RepairCase

MEMORY_TYPE = "repair_memory"


def record_case(
    db: Session,
    project: Project,
    *,
    error_text: str,
    probable_cause: str,
    fix_applied: str,
    success: bool,
) -> RepairCase:
    case = RepairCase(
        project_id=project.id,
        error_text=error_text,
        probable_cause=probable_cause,
        fix_applied=fix_applied,
        success=success,
    )
    db.add(case)
    db.flush()
    return case


def record_failure_summary(
    db: Session,
    project: Project,
    *,
    task_id: str,
    message: str,
    error_text: str,
    summary: str,
) -> None:
    append_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key=f"failure:{task_id}",
        value={
            "message": message,
            "error_text": error_text,
            "summary": summary,
        },
    )


def recent_cases(db: Session, project: Project, limit: int = 5) -> list[dict[str, Any]]:
    cases = (
        db.query(RepairCase)
        .filter(RepairCase.project_id == project.id)
        .order_by(RepairCase.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "error_text": case.error_text,
            "probable_cause": case.probable_cause,
            "fix_applied": case.fix_applied,
            "success": case.success,
            "created_at": case.created_at,
        }
        for case in reversed(cases)
    ]


def latest_success_for_cause(
    db: Session,
    project: Project,
    probable_cause: str,
) -> dict[str, Any] | None:
    case = (
        db.query(RepairCase)
        .filter(
            RepairCase.project_id == project.id,
            RepairCase.probable_cause == probable_cause,
            RepairCase.success.is_(True),
        )
        .order_by(RepairCase.id.desc())
        .first()
    )
    if case is None:
        return None
    return {
        "error_text": case.error_text,
        "probable_cause": case.probable_cause,
        "fix_applied": case.fix_applied,
        "success": case.success,
        "created_at": case.created_at,
    }
