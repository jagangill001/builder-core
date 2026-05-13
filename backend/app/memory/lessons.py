from __future__ import annotations

from typing import Any

from app.db.repository import repository

LESSONS_KEY = "lessons_learned"

DEFAULT_LESSONS = [
    "Frontend/backend URL mismatches should be surfaced as connection errors, not hidden by fake progress.",
    "Connector actions must say not configured when API keys or provider adapters are missing.",
    "Secrets and environment variable values must never be echoed back to the frontend.",
    "GitHub and deployment writes should be admin-protected and branch-first.",
]


def list_lessons() -> list[str]:
    payload = repository.get_project_memory(LESSONS_KEY) or {}
    stored = payload.get("items", [])
    return list(dict.fromkeys(DEFAULT_LESSONS + [str(item) for item in stored]))


def record_task_failure(task_id: str, errors: list[str], warnings: list[str]) -> None:
    existing = list_lessons()
    additions: list[str] = []
    if any("connector" in item.lower() or "not_configured" in item.lower() for item in errors + warnings):
        additions.append("When a connector is missing, return a clear not-configured result and recommended setup step.")
    if any("secret" in item.lower() for item in errors + warnings):
        additions.append("Secret-exposure requests should be blocked before routing or connector execution.")
    if any("backend" in item.lower() for item in errors + warnings):
        additions.append("Backend availability should be checked before reporting command execution progress.")
    payload = {
        "items": list(dict.fromkeys(existing + additions)),
        "latest_failure": {"task_id": task_id, "errors": errors, "warnings": warnings},
    }
    repository.save_project_memory(LESSONS_KEY, payload)


def repeated_error_summary() -> dict[str, Any]:
    lessons = list_lessons()
    return {
        "known_lessons": lessons,
        "repeated_issue_detection": "foundation",
        "message": "Builder Core records failure categories now; deeper clustering can be added when more task history exists.",
    }
