from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


COLLECTION_NAMES = [
    "tasks",
    "command_history",
    "chat_history",
    "assistant_memory",
    "project_memory",
    "research_tasks",
    "research_results",
    "codex_prompts",
    "codex_summaries",
    "learning_lessons",
    "self_improvement",
    "app_plans",
    "market_analysis",
    "storage_tests",
    "search_documents",
    "search_chunks",
    "search_queries",
    "knowledge_base",
    "tool_registry",
    "document_ingest",
    "url_ingest_records",
    "crawler_plans",
    "intelligence_history",
    "bridge_status_history",
    "project_structure_summaries",
    "environment_problems",
]

COLLECTION_LIMITS = {
    "tasks": 300,
    "command_history": 300,
    "chat_history": 400,
    "assistant_memory": 200,
    "project_memory": 300,
    "research_tasks": 200,
    "research_results": 200,
    "codex_prompts": 200,
    "codex_summaries": 200,
    "learning_lessons": 200,
    "self_improvement": 200,
    "app_plans": 120,
    "market_analysis": 120,
    "storage_tests": 80,
    "search_documents": 600,
    "search_chunks": 3000,
    "search_queries": 300,
    "knowledge_base": 600,
    "tool_registry": 80,
    "document_ingest": 300,
    "url_ingest_records": 300,
    "crawler_plans": 120,
    "intelligence_history": 200,
    "bridge_status_history": 80,
    "project_structure_summaries": 40,
    "environment_problems": 80,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def default_payload() -> dict[str, Any]:
    payload = {name: [] for name in COLLECTION_NAMES}
    payload.update(
        {
            "latest_summary": None,
            "latest_prompt": None,
            "latest_intelligence_brief": None,
            "latest_bridge_status": None,
            "project_structure_summary": None,
            "known_environment_problems": [],
        }
    )
    return payload


def normalize_firestore_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    if isinstance(value, dict):
        return {key: normalize_firestore_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [normalize_firestore_value(item) for item in value]

    return value


def pick_record_id(record: dict[str, Any]) -> str:
    candidate_keys = (
        "id",
        "task_id",
        "command_id",
        "document_id",
        "research_id",
        "chat_id",
        "tool_id",
        "url_ingest_id",
        "plan_id",
    )
    for key in candidate_keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return f"record_{uuid4().hex[:12]}"


class LocalJsonCollectionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        if not self.path.exists():
            atomic_write_json(self.path, default_payload())

    def _read_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return default_payload()

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default_payload()

        defaults = default_payload()
        for key, value in defaults.items():
            payload.setdefault(key, value)

        if "lessons" in payload and payload.get("learning_lessons") == []:
            payload["learning_lessons"] = list(payload.get("lessons", []))
        if "prompt_history" in payload and payload.get("codex_prompts") == []:
            payload["codex_prompts"] = list(payload.get("prompt_history", []))
        if "intelligence_history" not in payload:
            payload["intelligence_history"] = []

        return payload

    def _write_payload(self, payload: dict[str, Any]) -> None:
        atomic_write_json(self.path, payload)

    def save_record(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        limit = COLLECTION_LIMITS.get(collection, 200)
        with self.lock:
            payload = self._read_payload()
            items = [item for item in payload.get(collection, []) if item.get("id") != record["id"]]
            items.insert(0, record)
            payload[collection] = items[:limit]
            self._write_payload(payload)
        return record

    def get_record(self, collection: str, record_id: str) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()

        for item in payload.get(collection, []):
            if item.get("id") == record_id:
                return item
        return None

    def list_records(self, collection: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        items = payload.get(collection, [])
        return items[:limit]

    def update_record(self, collection: str, record_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
            items = payload.get(collection, [])
            updated: Optional[dict[str, Any]] = None

            for item in items:
                if item.get("id") != record_id:
                    continue

                item.update(updates)
                updated = item
                break

            if updated is None:
                return None

            payload[collection] = sorted(
                items,
                key=lambda entry: entry.get("updated_at", entry.get("created_at", "")),
                reverse=True,
            )[: COLLECTION_LIMITS.get(collection, 200)]
            self._write_payload(payload)

        return updated


class FirestoreCollectionStore:
    def __init__(self, project_id: str) -> None:
        from google.cloud import firestore

        self.client = firestore.Client(project=project_id)

    def save_record(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        self.client.collection(collection).document(record["id"]).set(record)
        return record

    def get_record(self, collection: str, record_id: str) -> Optional[dict[str, Any]]:
        document = self.client.collection(collection).document(record_id).get()
        if not document.exists:
            return None
        payload = document.to_dict() or {}
        return normalize_firestore_value(payload)

    def list_records(self, collection: str, limit: int = 50) -> list[dict[str, Any]]:
        documents = self.client.collection(collection).limit(limit).stream()
        items = [normalize_firestore_value(document.to_dict() or {}) for document in documents]
        return sorted(
            items,
            key=lambda item: item.get("updated_at", item.get("created_at", "")),
            reverse=True,
        )[:limit]

    def update_record(self, collection: str, record_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        document_ref = self.client.collection(collection).document(record_id)
        document = document_ref.get()
        if not document.exists:
            return None
        document_ref.update(updates)
        return self.get_record(collection, record_id)


class ProjectStorageService:
    def __init__(self, base_dir: Path) -> None:
        self.runtime_dir = base_dir / "runtime_data"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_dir / "project_memory.json"
        self.local_store = LocalJsonCollectionStore(self.path)

        self.storage_mode_requested = (os.environ.get("STORAGE_MODE") or "local").strip().lower()
        self.firestore_enabled = str(os.environ.get("FIRESTORE_ENABLED", "false")).lower() == "true"
        self.project_id = (os.environ.get("GCP_PROJECT_ID") or "").strip()
        self.bucket_name = (os.environ.get("GCS_BUCKET_NAME") or "").strip()
        self.lock = threading.Lock()
        self.primary_store: Optional[FirestoreCollectionStore] = None
        self.using_firestore = False
        self.using_fallback = True
        self.storage_backend = "local_json"
        self.storage_message = (
            "Cloud-first memory is using local JSON fallback. This is fine for development, but Cloud Run local storage is temporary."
        )
        self.warnings: list[str] = []
        self.cloud_ready_notes = [
            "Firestore can later store memory, lessons, chat history, research tasks, private search records, and app plans.",
            "Google Cloud Storage can later store uploaded files and generated outputs.",
        ]

        if self.storage_mode_requested == "firestore" and self.firestore_enabled and self.project_id:
            try:
                self.primary_store = FirestoreCollectionStore(self.project_id)
                self.using_firestore = True
                self.using_fallback = False
                self.storage_backend = "firestore"
                self.storage_message = (
                    "Cloud-first storage is active. Firestore is configured as the primary store with local JSON fallback ready."
                )
            except Exception as error:
                self.warnings.append(self._format_firestore_warning(error))
                self.primary_store = None
                self.using_firestore = False
                self.using_fallback = True
                self.storage_backend = "local_json"
                self.storage_message = (
                    "Firestore mode was requested, but Builder Core is using local JSON fallback because Firestore could not initialize."
                )
        elif self.storage_mode_requested == "firestore":
            self.warnings.append(
                "Firestore mode was requested, but FIRESTORE_ENABLED or GCP_PROJECT_ID is missing. Local JSON fallback is active."
            )

    def _format_firestore_warning(self, error: Exception) -> str:
        message = str(error)
        lowered = message.lower()
        if "permission" in lowered or "403" in lowered or "datastore" in lowered:
            return (
                "Firestore is enabled but the Cloud Run service account does not have permission. "
                "Add Cloud Datastore User role."
            )
        return f"Firestore warning: {message}"

    def _prepare_record(self, record: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(record)
        prepared["id"] = pick_record_id(prepared)
        prepared.setdefault("created_at", utc_now_iso())
        prepared["updated_at"] = utc_now_iso()
        return prepared

    def _remember_warning(self, warning: str) -> None:
        if warning and warning not in self.warnings:
            self.warnings.append(warning)

    def save_record(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        prepared = self._prepare_record(record)

        if self.primary_store is not None and self.using_firestore:
            try:
                saved = self.primary_store.save_record(collection, prepared)
                return normalize_firestore_value(saved)
            except Exception as error:
                self._remember_warning(self._format_firestore_warning(error))
                self.using_fallback = True

        return self.local_store.save_record(collection, prepared)

    def get_record(self, collection: str, record_id: str) -> Optional[dict[str, Any]]:
        if self.primary_store is not None and self.using_firestore:
            try:
                record = self.primary_store.get_record(collection, record_id)
                if record is not None:
                    return record
            except Exception as error:
                self._remember_warning(self._format_firestore_warning(error))
                self.using_fallback = True

        return self.local_store.get_record(collection, record_id)

    def list_records(self, collection: str, limit: int = 50) -> list[dict[str, Any]]:
        if self.primary_store is not None and self.using_firestore:
            try:
                items = self.primary_store.list_records(collection, limit)
                if items:
                    return items
            except Exception as error:
                self._remember_warning(self._format_firestore_warning(error))
                self.using_fallback = True

        return self.local_store.list_records(collection, limit)

    def update_record(self, collection: str, record_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        normalized_updates = normalize_firestore_value(dict(updates))
        normalized_updates["updated_at"] = utc_now_iso()

        if self.primary_store is not None and self.using_firestore:
            try:
                updated = self.primary_store.update_record(collection, record_id, normalized_updates)
                if updated is not None:
                    return updated
            except Exception as error:
                self._remember_warning(self._format_firestore_warning(error))
                self.using_fallback = True

        return self.local_store.update_record(collection, record_id, normalized_updates)

    def get_storage_status(self) -> dict[str, Any]:
        return {
            "storage_mode": self.storage_mode_requested or "local",
            "storage_backend": self.storage_backend,
            "storage_message": self.storage_message,
            "firestore_enabled": self.firestore_enabled,
            "gcp_project_id": self.project_id or "missing",
            "gcs_bucket_name": self.bucket_name or "missing",
            "using_firestore": self.using_firestore and self.primary_store is not None,
            "using_fallback": self.using_fallback or self.primary_store is None,
            "warnings": self.warnings,
            "collections": COLLECTION_NAMES,
            "checked_at": utc_now_iso(),
        }

    def run_storage_test(self) -> dict[str, Any]:
        record = {
            "type": "storage_test",
            "note": "Builder Core storage test",
            "id": f"storage_test_{uuid4().hex[:12]}",
        }
        warnings = list(self.warnings)

        try:
            saved = self.save_record("storage_tests", record)
            read_back = self.get_record("storage_tests", saved["id"])
            storage_used = "firestore" if self.primary_store is not None and self.using_firestore and not self.using_fallback else "local"
            if self.using_fallback and self.primary_store is not None:
                storage_used = "local"

            return {
                "ok": True,
                "storage_used": storage_used,
                "record_id": saved["id"],
                "saved": True,
                "read_back": read_back is not None,
                "warnings": warnings + self.warnings,
            }
        except Exception as error:
            warnings.append(str(error))
            return {
                "ok": False,
                "storage_used": "local" if self.primary_store is None or self.using_fallback else "firestore",
                "record_id": record["id"],
                "saved": False,
                "read_back": False,
                "warnings": warnings,
            }

    def health_check(self) -> dict[str, Any]:
        return {
            "ok": True,
            **self.get_storage_status(),
            "project_memory_count": len(self.get_project_memory(200)),
            "assistant_memory_count": len(self.get_assistant_memory(200)),
            "chat_history_count": len(self.get_chat_history(200)),
            "research_task_count": len(self.get_research_tasks(200)),
            "lesson_count": len(self.get_lessons(200)),
            "self_improvement_count": len(self.get_self_improvements(200)),
            "search_document_count": len(self.list_records("search_documents", 1000)),
            "search_chunk_count": len(self.list_records("search_chunks", 3000)),
        }

    def save_project_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("project_memory", entry)

    def get_project_memory(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("project_memory", limit)

    def save_assistant_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("assistant_memory", entry)

    def get_assistant_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.list_records("assistant_memory", limit)

    def save_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("chat_history", message)

    def get_chat_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self.list_records("chat_history", limit)))

    def save_research_task(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = task.get("research_id") or task.get("id")
        payload = {
            **task,
            "id": task_id or pick_record_id(task),
            "research_id": task_id or pick_record_id(task),
        }
        return self.save_record("research_tasks", payload)

    def get_research_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("research_tasks", limit)

    def get_research_task(self, research_id: str) -> Optional[dict[str, Any]]:
        record = self.get_record("research_tasks", research_id)
        if record is not None:
            return record

        for item in self.get_research_tasks(200):
            if item.get("research_id") == research_id:
                return item
        return None

    def save_research_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("research_results", result)

    def get_research_results(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("research_results", limit)

    def save_self_improvement(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("self_improvement", entry)

    def get_self_improvements(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("self_improvement", limit)

    def save_latest_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("codex_summaries", summary)

    def get_latest_summary(self) -> Optional[dict[str, Any]]:
        items = self.list_records("codex_summaries", 1)
        return items[0] if items else None

    def get_codex_summaries(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("codex_summaries", limit)

    def save_latest_prompt(self, prompt_record: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("codex_prompts", prompt_record)

    def get_latest_prompt(self) -> Optional[dict[str, Any]]:
        items = self.list_records("codex_prompts", 1)
        return items[0] if items else None

    def get_prompt_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("codex_prompts", limit)

    def save_latest_intelligence_brief(self, brief_record: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("intelligence_history", brief_record)

    def get_latest_intelligence_brief(self) -> Optional[dict[str, Any]]:
        items = self.list_records("intelligence_history", 1)
        return items[0] if items else None

    def get_intelligence_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("intelligence_history", limit)

    def save_latest_bridge_status(self, bridge_status: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("bridge_status_history", bridge_status)

    def get_latest_bridge_status(self) -> Optional[dict[str, Any]]:
        items = self.list_records("bridge_status_history", 1)
        return items[0] if items else None

    def save_known_environment_problems(self, problems: list[str]) -> list[str]:
        unique = list(dict.fromkeys(problem for problem in problems if problem))
        for problem in unique:
            self.save_record(
                "environment_problems",
                {
                    "id": f"env_problem_{abs(hash(problem))}",
                    "note": problem,
                },
            )
        return unique

    def get_known_environment_problems(self) -> list[str]:
        items = self.list_records("environment_problems", 80)
        notes: list[str] = []
        for item in items:
            note = item.get("note")
            if isinstance(note, str) and note and note not in notes:
                notes.append(note)
        return notes

    def save_lesson(self, lesson: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("learning_lessons", lesson)

    def get_lessons(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.list_records("learning_lessons", limit)

    def save_project_structure_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        return self.save_record("project_structure_summaries", summary)

    def get_project_structure_summary(self) -> Optional[dict[str, Any]]:
        items = self.list_records("project_structure_summaries", 1)
        return items[0] if items else None
