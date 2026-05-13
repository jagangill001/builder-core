from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.legacy_models import BuildRequestRecord, CreatedFile, PlanStep, Project
from app.services import builder_service


def normalize_project_name(project_name: str | None) -> str:
    clean_name = (project_name or "Default Project").strip()
    return clean_name or "Default Project"


def list_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.name.asc()).all()


def get_or_create_project(db: Session, project_name: str) -> Project:
    clean_name = normalize_project_name(project_name)
    project = db.query(Project).filter(Project.name == clean_name).first()
    if project:
        return project

    project = Project(name=clean_name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def create_project(db: Session, project_name: str) -> Project:
    clean_name = normalize_project_name(project_name)
    project = db.query(Project).filter(Project.name == clean_name).first()
    if project:
        return project

    project = Project(name=clean_name)
    db.add(project)
    db.commit()
    db.refresh(project)

    builder_service.ensure_project_scaffold(clean_name)
    builder_service.build_project_shell(clean_name)
    return project


def record_request(
    db: Session,
    project: Project,
    instruction: str,
    status: str,
    plan: list[str],
    files_changed: list[str],
) -> None:
    request_record = BuildRequestRecord(
        instruction=instruction,
        status=status,
        project_id=project.id,
    )
    db.add(request_record)
    db.commit()
    db.refresh(request_record)

    for step in plan:
        db.add(PlanStep(request_id=request_record.id, step_text=step))

    for file_path in files_changed:
        db.add(CreatedFile(request_id=request_record.id, file_path=file_path))

    db.commit()


def list_history(db: Session, project_name: str | None = None) -> list[dict[str, Any]]:
    query = db.query(BuildRequestRecord).order_by(BuildRequestRecord.id.desc())
    if project_name:
        query = query.join(Project).filter(Project.name == normalize_project_name(project_name))

    items: list[dict[str, Any]] = []
    for record in query.all():
        items.append(
            {
                "instruction": record.instruction,
                "status": record.status,
                "project_name": record.project.name,
                "plan": [step.step_text for step in record.plans],
                "created_files": [file.file_path for file in record.files],
            }
        )
    return items
