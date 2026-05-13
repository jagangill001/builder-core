from __future__ import annotations

from typing import Any

from app.database import SessionLocal
from app.memory import pattern_memory, project_memory, repair_memory, short_term
from app.legacy_models import Project
from app.services import builder_service
from app.services import project_service


def _fresh_project_memory() -> dict[str, Any]:
    return {
        "latest_generated_module": None,
        "latest_plan": [],
        "latest_build_result": {},
        "latest_intent": "chat",
        "recent_chat_history": [],
        "latest_files_created": [],
        "recent_patterns": [],
        "recent_repairs": [],
    }


def _load_legacy_memory_store() -> dict[str, Any]:
    return builder_service.read_json_file(
        builder_service.assistant_memory_path(),
        {
            "selected_project": "Default Project",
            "recent_chat_history": [],
            "project_memories": {},
        },
    )


def _legacy_snapshot(project_name: str) -> dict[str, Any]:
    store = _load_legacy_memory_store()
    project_key = builder_service.safe_name(project_name)
    project_memory_store = store.get("project_memories", {}).get(project_key, {}).copy()

    snapshot = _fresh_project_memory()
    snapshot.update(project_memory_store)
    snapshot["selected_project"] = store.get("selected_project", project_name)
    return snapshot


def get_project_memory(project_name: str) -> dict[str, Any]:
    clean_project_name = project_service.normalize_project_name(project_name)
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.name == clean_project_name).first()
        if project is None:
            return _legacy_snapshot(clean_project_name)

        snapshot = _fresh_project_memory()
        snapshot.update(project_memory.snapshot(db, project))
        snapshot["selected_project"] = clean_project_name
        snapshot["recent_chat_history"] = short_term.recent_history(db, project)
        snapshot["recent_patterns"] = pattern_memory.recent_patterns(db, project)
        snapshot["recent_repairs"] = repair_memory.recent_cases(db, project)
        return snapshot
    finally:
        db.close()


def remember_workflow(
    project_name: str,
    task_id: str,
    user_message: str,
    assistant_reply: str,
    intent: str,
    plan: list[str],
    build_result: dict[str, Any],
    module_key: str | None,
    files_created: list[str],
    inspection: dict[str, Any] | None = None,
    version_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_project_name = project_service.normalize_project_name(project_name)
    db = SessionLocal()
    try:
        project = project_service.get_or_create_project(db, clean_project_name)
        short_term.record_workflow(
            db,
            project,
            task_id=task_id,
            user_message=user_message,
            assistant_reply=assistant_reply,
            intent=intent,
            result_status=build_result.get("status", "unknown"),
            summary=build_result.get("summary", ""),
            files_changed=files_created,
        )
        project_memory.record_workflow(
            db,
            project,
            goal=user_message,
            intent=intent,
            plan=plan,
            files_changed=files_created,
            build_result=build_result,
            summary=assistant_reply,
            module_key=module_key,
            inspection=inspection,
            version_snapshot=version_snapshot,
        )
        if build_result.get("status") == "success":
            pattern_memory.record_success_pattern(
                db,
                project,
                intent=intent,
                module_key=module_key,
                plan=plan,
                files_changed=files_created,
                summary=build_result.get("summary", ""),
            )
        else:
            repair_memory.record_failure_summary(
                db,
                project,
                task_id=task_id,
                message=user_message,
                error_text=build_result.get("summary", ""),
                summary=assistant_reply,
            )

        db.commit()
    finally:
        db.close()

    return get_project_memory(clean_project_name)
