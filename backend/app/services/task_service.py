from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp_progress(value: Any) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = 0
    return max(0, min(100, numeric))


class AutomationTaskService:
    def __init__(self, base_dir: Path, storage: Optional[ProjectStorageService] = None) -> None:
        self.base_dir = base_dir
        self.storage = storage
        self.storage_backend = storage.storage_backend if storage is not None else "local_json"
        self.storage_message = (
            storage.storage_message
            if storage is not None
            else "Task storage is using local JSON fallback."
        )

    def _with_storage_details(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            **task,
            "storage_backend": self.storage_backend,
            "storage_message": self.storage_message,
        }

    def _normalize_updates(self, updates: dict[str, Any]) -> dict[str, Any]:
        normalized_updates: dict[str, Any] = {}

        text_fields = (
            "command",
            "project_name",
            "status",
            "stage",
            "current_stage",
            "github_commit",
            "workflow_status",
        )
        passthrough_fields = (
            "logs",
            "errors",
            "summary",
            "bridge_status",
            "files_changed",
            "stage_history",
            "config_problems",
            "manual_setup",
            "testing_result",
            "deploy_result",
            "generated_prompt",
            "codex_summary",
            "prompt_metadata",
            "known_issues",
            "what_completed",
            "what_remains",
            "next_recommended_step",
            "intelligence_mode",
            "intelligence_brief",
        )

        for key in text_fields:
            if key in updates and updates[key] is not None:
                normalized_updates[key] = updates[key]

        for key in passthrough_fields:
            if key in updates:
                normalized_updates[key] = updates[key]

        if "progress" in updates and updates["progress"] is not None:
            normalized_updates["progress"] = clamp_progress(updates["progress"])

        stage_value = normalized_updates.get("stage")
        current_stage_value = normalized_updates.get("current_stage")

        if stage_value and not current_stage_value:
            normalized_updates["current_stage"] = stage_value
        if current_stage_value and not stage_value:
            normalized_updates["stage"] = current_stage_value

        normalized_updates["updated_at"] = utc_now_iso()
        return normalized_updates

    def _build_task_record(
        self,
        command: str,
        project_name: str,
        status: str = "received",
        stage: str = "received",
        progress: int = 1,
        github_commit: Optional[str] = None,
        workflow_status: Optional[str] = None,
        logs: Optional[list[str]] = None,
        errors: Optional[list[str]] = None,
        summary: Optional[dict[str, Any]] = None,
        bridge_status: Optional[dict[str, Any]] = None,
        files_changed: Optional[list[str]] = None,
        generated_prompt: Optional[str] = None,
        codex_summary: Optional[str] = None,
        intelligence_mode: Optional[str] = None,
        intelligence_brief: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        timestamp = utc_now_iso()
        return {
            "id": f"task_{uuid4().hex[:12]}",
            "command": command,
            "project_name": project_name,
            "status": status,
            "stage": stage,
            "current_stage": stage,
            "progress": clamp_progress(progress),
            "github_commit": github_commit,
            "workflow_status": workflow_status,
            "logs": list(logs or []),
            "errors": list(errors or []),
            "summary": summary,
            "bridge_status": bridge_status or {},
            "files_changed": list(files_changed or []),
            "generated_prompt": generated_prompt,
            "codex_summary": codex_summary,
            "prompt_metadata": None,
            "known_issues": [],
            "what_completed": [],
            "what_remains": [],
            "next_recommended_step": None,
            "intelligence_mode": intelligence_mode,
            "intelligence_brief": intelligence_brief,
            "stage_history": [
                {
                    "stage": stage,
                    "status": status,
                    "progress": clamp_progress(progress),
                    "timestamp": timestamp,
                    "message": "Task created.",
                }
            ],
            "config_problems": [],
            "manual_setup": [],
            "testing_result": None,
            "deploy_result": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def create_task(
        self,
        command: str,
        project_name: str,
        status: str = "received",
        current_stage: str = "received",
        progress: int = 1,
        github_commit: Optional[str] = None,
        workflow_status: Optional[str] = None,
        logs: Optional[list[str]] = None,
        errors: Optional[list[str]] = None,
        summary: Optional[dict[str, Any]] = None,
        bridge_status: Optional[dict[str, Any]] = None,
        files_changed: Optional[list[str]] = None,
        generated_prompt: Optional[str] = None,
        codex_summary: Optional[str] = None,
        intelligence_mode: Optional[str] = None,
        intelligence_brief: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        task = self._build_task_record(
            command=command,
            project_name=project_name,
            status=status,
            stage=current_stage,
            progress=progress,
            github_commit=github_commit,
            workflow_status=workflow_status,
            logs=logs,
            errors=errors,
            summary=summary,
            bridge_status=bridge_status,
            files_changed=files_changed,
            generated_prompt=generated_prompt,
            codex_summary=codex_summary,
            intelligence_mode=intelligence_mode,
            intelligence_brief=intelligence_brief,
        )
        if self.storage is None:
            raise RuntimeError("AutomationTaskService requires a storage backend.")

        created = self.storage.save_record("tasks", task)
        self.storage_backend = self.storage.storage_backend
        self.storage_message = self.storage.storage_message
        return self._with_storage_details(created)

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        if self.storage is None:
            return []
        self.storage_backend = self.storage.storage_backend
        self.storage_message = self.storage.storage_message
        return [self._with_storage_details(task) for task in self.storage.list_records("tasks", limit)]

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        if self.storage is None:
            return None
        task = self.storage.get_record("tasks", task_id)
        if task is None:
            return None
        self.storage_backend = self.storage.storage_backend
        self.storage_message = self.storage.storage_message
        return self._with_storage_details(task)

    def update_task(self, task_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        if self.storage is None:
            return None
        normalized_updates = self._normalize_updates(updates)
        updated = self.storage.update_record("tasks", task_id, normalized_updates)
        if updated is None:
            return None
        self.storage_backend = self.storage.storage_backend
        self.storage_message = self.storage.storage_message
        return self._with_storage_details(updated)
