from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


DEFAULT_SCHEDULE = {
    "id": "learning_schedule_default",
    "enabled": False,
    "mode": "manual",
    "allowed_hours": ["02:00-04:00"],
    "timezone": "America/Toronto",
    "daily_url_limit": 50,
    "max_urls_per_run": 5,
    "categories": [],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningScheduleService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def get_settings(self) -> dict[str, Any]:
        existing = self.storage.get_record("learning_schedule_settings", DEFAULT_SCHEDULE["id"])
        if existing:
            return {
                **DEFAULT_SCHEDULE,
                **existing,
                "background_enabled": False,
                "warnings": self._warnings(existing),
            }
        payload = {**DEFAULT_SCHEDULE, "updated_at": utc_now_iso(), "background_enabled": False, "warnings": self._warnings(DEFAULT_SCHEDULE)}
        return payload

    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = str(payload.get("mode") or DEFAULT_SCHEDULE["mode"]).strip().lower()
        if mode not in {"manual", "scheduled_ready"}:
            mode = "manual"
        settings = {
            **DEFAULT_SCHEDULE,
            "enabled": bool(payload.get("enabled", False)),
            "mode": mode,
            "allowed_hours": payload.get("allowed_hours") if isinstance(payload.get("allowed_hours"), list) else DEFAULT_SCHEDULE["allowed_hours"],
            "timezone": str(payload.get("timezone") or DEFAULT_SCHEDULE["timezone"]),
            "daily_url_limit": self._bounded_int(payload.get("daily_url_limit"), 50, 1, 500),
            "max_urls_per_run": self._bounded_int(payload.get("max_urls_per_run"), 5, 1, 50),
            "categories": payload.get("categories") if isinstance(payload.get("categories"), list) else [],
            "updated_at": utc_now_iso(),
        }
        saved = self.storage.save_record("learning_schedule_settings", settings)
        return {**saved, "background_enabled": False, "warnings": self._warnings(saved)}

    def _warnings(self, settings: dict[str, Any]) -> list[str]:
        warnings = [
            "Schedule settings are saved only. Builder Core does not create Cloud Scheduler, Cloud Tasks, or paid background jobs automatically.",
            "Use a manual run-now action to ingest within limits.",
        ]
        if settings.get("enabled") and settings.get("mode") == "scheduled_ready":
            warnings.append("Scheduled-ready mode still needs a human-created Cloud Scheduler/Cloud Run Jobs setup later.")
        return warnings

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default
        return max(minimum, min(maximum, number))
