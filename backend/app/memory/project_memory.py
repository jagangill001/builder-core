from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.memory import latest_entry, load_json, upsert_entry
from app.legacy_models import Project

MEMORY_TYPE = "project_memory"
PROJECT_SUMMARY_KEY = "builder_core_project_summary"


DEFAULT_PROJECT_SUMMARY: dict[str, Any] = {
    "project_name": "Builder Core",
    "repo": "jagangill001/builder-core",
    "live_frontend_url": "https://builder-core-frontend-599596796788.us-central1.run.app",
    "live_backend_url": "https://builder-core-599596796788.us-central1.run.app",
    "backend_folder": "backend",
    "frontend_folder": "frontend",
    "current_stack": ["FastAPI", "Next.js", "Google Cloud Run", "GitHub Actions", "SQLite local fallback"],
    "known_problems": [
        "Live search, weather, and news need real provider adapters before they can answer current questions.",
        "Codex execution is package-only until a real execution integration exists.",
        "Deployment rollback is a placeholder until Cloud Run control is wired safely.",
    ],
    "completed_fixes": [
        "Backend-owned task model foundation.",
        "Honest connector status model.",
        "Admin-token foundation for protected actions.",
    ],
    "pending_work": [
        "Configure real connector provider adapters.",
        "Move long-running tasks to an external worker.",
        "Wire real Codex/GitHub PR execution when ready.",
    ],
    "next_recommended_steps": [
        "Test the /tasks/create command flow locally.",
        "Configure admin token and verify protected endpoints.",
        "Configure GitHub env vars before enabling real repo writes.",
    ],
}


def record_workflow(
    db: Session,
    project: Project,
    *,
    goal: str,
    intent: str,
    plan: list[str],
    files_changed: list[str],
    build_result: dict[str, Any],
    summary: str,
    module_key: str | None,
    inspection: dict[str, Any] | None,
    version_snapshot: dict[str, Any] | None,
) -> None:
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_goal",
        value={"message": goal},
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_intent",
        value={"intent": intent},
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_plan",
        value=plan,
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_files_changed",
        value=files_changed[:20],
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_build_result",
        value=build_result,
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_summary",
        value={"assistant_reply": summary},
    )
    upsert_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key="latest_inspection",
        value=inspection or {},
    )
    if module_key:
        upsert_entry(
            db,
            memory_type=MEMORY_TYPE,
            project_id=project.id,
            key="latest_generated_module",
            value={"module_key": module_key},
        )
    if version_snapshot:
        upsert_entry(
            db,
            memory_type=MEMORY_TYPE,
            project_id=project.id,
            key="latest_snapshot",
            value=version_snapshot,
        )


def snapshot(db: Session, project: Project) -> dict[str, Any]:
    def read_value(key: str, default: Any) -> Any:
        entry = latest_entry(
            db,
            memory_type=MEMORY_TYPE,
            project_id=project.id,
            key=key,
        )
        if entry is None:
            return default
        return load_json(entry.value_json, default)

    latest_generated_module = read_value("latest_generated_module", {}).get("module_key")
    latest_intent = read_value("latest_intent", {}).get("intent", "chat")
    latest_summary = read_value("latest_summary", {}).get("assistant_reply", "")

    return {
        "latest_generated_module": latest_generated_module,
        "latest_plan": read_value("latest_plan", []),
        "latest_build_result": read_value("latest_build_result", {}),
        "latest_intent": latest_intent,
        "latest_files_created": read_value("latest_files_changed", []),
        "latest_summary": latest_summary,
        "latest_snapshot": read_value("latest_snapshot", {}),
    }


def get_project_summary() -> dict[str, Any]:
    from app.db.repository import repository

    stored = repository.get_project_memory(PROJECT_SUMMARY_KEY) or {}
    return _merge_summary(DEFAULT_PROJECT_SUMMARY, stored)


def update_project_summary(updates: dict[str, Any]) -> dict[str, Any]:
    from app.db.repository import repository

    current = get_project_summary()
    clean_updates = {key: value for key, value in updates.items() if key in DEFAULT_PROJECT_SUMMARY}
    updated = _merge_summary(current, clean_updates)
    repository.save_project_memory(PROJECT_SUMMARY_KEY, updated)
    return updated


def _merge_summary(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(merged.get(key), list) and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*merged[key], *value]))
        elif value not in (None, ""):
            merged[key] = value
    return merged
