from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp_progress(value: Any) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = 0

    return max(0, min(100, numeric))


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def normalize_firestore_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    return value


class LocalJsonTaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        if not self.path.exists():
            atomic_write_json(self.path, {"items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        items = payload.get("items", [])
        return items if isinstance(items, list) else []

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        atomic_write_json(self.path, {"items": items})

    def list_tasks(self) -> list[dict[str, Any]]:
        with self.lock:
            items = self._read_items()

        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        with self.lock:
            for item in self._read_items():
                if item.get("id") == task_id:
                    return item

        return None

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            items = self._read_items()
            items.append(task)
            self._write_items(items)

        return task

    def update_task(self, task_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        with self.lock:
            items = self._read_items()
            updated_item: Optional[dict[str, Any]] = None

            for item in items:
                if item.get("id") != task_id:
                    continue

                item.update(updates)
                updated_item = item
                break

            if updated_item is None:
                return None

            self._write_items(items)

        return updated_item


class FirestoreTaskStore:
    def __init__(self, project_id: str, collection_name: str = "builder_core_tasks") -> None:
        from google.cloud import firestore

        self.client = firestore.Client(project=project_id)
        self.collection = self.client.collection(collection_name)
        self.order_desc = firestore.Query.DESCENDING

    def _normalize_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {key: normalize_firestore_value(value) for key, value in payload.items()}

    def list_tasks(self) -> list[dict[str, Any]]:
        documents = self.collection.order_by("updated_at", direction=self.order_desc).stream()
        return [self._normalize_task(document.to_dict()) for document in documents]

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        document = self.collection.document(task_id).get()
        if not document.exists:
            return None

        return self._normalize_task(document.to_dict())

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        self.collection.document(task["id"]).set(task)
        return task

    def update_task(self, task_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        document_ref = self.collection.document(task_id)
        document = document_ref.get()
        if not document.exists:
            return None

        document_ref.update(updates)
        return self.get_task(task_id)


class AutomationTaskService:
    def __init__(self, base_dir: Path) -> None:
        self.runtime_dir = base_dir / "runtime_data"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.storage_backend = "local_json"
        self.storage_message = (
            "Cloud-first task tracking active. Local fallback used because Firestore is not enabled."
        )

        firestore_enabled = str(os.environ.get("FIRESTORE_ENABLED", "false")).lower() == "true"
        project_id = (os.environ.get("GCP_PROJECT_ID") or "").strip()

        if firestore_enabled and project_id:
            try:
                self.store = FirestoreTaskStore(project_id)
                self.storage_backend = "firestore"
                self.storage_message = "Cloud-first task tracking active. Firestore storage is enabled."
                return
            except Exception:
                self.storage_backend = "local_json"
                self.storage_message = (
                    "Cloud-first task tracking active. Local fallback used because Firestore is not enabled or not available."
                )

        self.store = LocalJsonTaskStore(self.runtime_dir / "automation_tasks.json")

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
        )
        created = self.store.create_task(task)
        return self._with_storage_details(created)

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        items = self.store.list_tasks()
        return [self._with_storage_details(task) for task in items[:limit]]

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        task = self.store.get_task(task_id)
        if task is None:
            return None

        return self._with_storage_details(task)

    def update_task(self, task_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        normalized_updates = self._normalize_updates(updates)
        updated = self.store.update_task(task_id, normalized_updates)
        if updated is None:
            return None

        return self._with_storage_details(updated)
