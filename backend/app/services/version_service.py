from __future__ import annotations

import json
from typing import Any

from app.database import SessionLocal
from app.legacy_models import VersionRecord
from app.services import builder_service, project_service


def predict_snapshot_files(project_name: str, plan_data: dict[str, Any]) -> list[str]:
    route_path = plan_data.get("route_path") or "/module"
    module_key = plan_data.get("module_key") or "generic_module"

    route_file = builder_service.route_file_path(project_name, route_path)
    api_file = route_file.with_name("api.txt")
    shell_dir = builder_service.app_root(project_name)
    predicted = [
        str(route_file),
        str(api_file),
        str(builder_service.registry_path(project_name)),
        str(builder_service.manifest_path(project_name, module_key)),
        str(shell_dir / "layout.tsx"),
        str(shell_dir / "page.tsx"),
    ]
    return list(dict.fromkeys(predicted))


def create_snapshot(
    project_name: str,
    *,
    message: str,
    plan_data: dict[str, Any],
) -> dict[str, Any]:
    clean_project_name = project_service.normalize_project_name(project_name)
    predicted_files = predict_snapshot_files(clean_project_name, plan_data)
    title = plan_data.get("title") or "module"
    intent = plan_data.get("intent") or "build"

    payload = {
        "kind": "pre_change_snapshot",
        "intent": intent,
        "title": title,
        "message": message,
        "files": predicted_files,
    }

    db = SessionLocal()
    try:
        project = project_service.get_or_create_project(db, clean_project_name)
        version = VersionRecord(
            project_id=project.id,
            snapshot_note=json.dumps(payload, ensure_ascii=True),
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return {
            "version_id": version.id,
            "snapshot_note": f"Snapshot before {intent} for {title}.",
            "files": predicted_files,
            "created_at": version.created_at,
        }
    finally:
        db.close()
