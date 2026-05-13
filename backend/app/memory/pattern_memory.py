from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.memory import append_entry, load_json, recent_entries
from app.legacy_models import Project

MEMORY_TYPE = "pattern_memory"


def record_success_pattern(
    db: Session,
    project: Project,
    *,
    intent: str,
    module_key: str | None,
    plan: list[str],
    files_changed: list[str],
    summary: str,
) -> None:
    module_label = module_key or "general"
    append_entry(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        key=f"{intent}:{module_label}",
        value={
            "intent": intent,
            "module_key": module_key,
            "plan": plan,
            "files_changed": files_changed[:12],
            "summary": summary,
        },
    )


def recent_patterns(db: Session, project: Project, limit: int = 5) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    for entry in recent_entries(
        db,
        memory_type=MEMORY_TYPE,
        project_id=project.id,
        limit=limit,
    ):
        payload = load_json(entry.value_json, {})
        patterns.append(
            {
                "key": entry.key,
                "intent": payload.get("intent"),
                "module_key": payload.get("module_key"),
                "plan": payload.get("plan", []),
                "summary": payload.get("summary", ""),
            }
        )
    return patterns
