from __future__ import annotations

from fastapi import APIRouter

from app.database import SessionLocal
from app.schemas import ProjectCreate
from app.services import project_service

router = APIRouter()


@router.get("/projects")
def get_projects():
    db = SessionLocal()
    try:
        projects = project_service.list_projects(db)
        return {"items": [{"id": project.id, "name": project.name} for project in projects]}
    finally:
        db.close()


@router.post("/projects")
def create_project(payload: ProjectCreate):
    db = SessionLocal()
    try:
        clean_name = payload.name.strip()
        if not clean_name:
            return {"ok": False, "message": "Project name is empty."}

        project = project_service.create_project(db, clean_name)
        return {
            "ok": True,
            "message": "Project created successfully.",
            "project": {"id": project.id, "name": project.name},
        }
    finally:
        db.close()


@router.get("/history")
def get_history(project_name: str | None = None):
    db = SessionLocal()
    try:
        return {"items": project_service.list_history(db, project_name)}
    finally:
        db.close()
