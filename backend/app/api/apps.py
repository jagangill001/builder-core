from __future__ import annotations

from fastapi import APIRouter

from app.services import builder_service, project_service

router = APIRouter()


@router.get("/apps")
def get_apps(project_name: str = "Default Project"):
    clean_project_name = project_service.normalize_project_name(project_name)
    inspection = builder_service.inspect_project(clean_project_name)
    return {
        "ok": True,
        "project_name": clean_project_name,
        "modules": inspection.get("modules", []),
        "routes": inspection.get("routes", []),
        "inspection": inspection,
    }


@router.get("/project-files")
def get_project_files(project_name: str):
    clean_project_name = project_service.normalize_project_name(project_name)
    return {"items": builder_service.list_project_files(clean_project_name)}


@router.get("/run-info")
def get_run_info(project_name: str):
    clean_project_name = project_service.normalize_project_name(project_name)
    return builder_service.get_run_info(clean_project_name)
