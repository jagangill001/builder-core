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


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def default_payload() -> dict[str, Any]:
    return {
        "project_memory": [],
        "assistant_memory": [],
        "chat_history": [],
        "research_tasks": [],
        "research_results": [],
        "self_improvement": [],
        "latest_summary": None,
        "codex_summaries": [],
        "latest_prompt": None,
        "prompt_history": [],
        "codex_prompts": [],
        "latest_intelligence_brief": None,
        "intelligence_history": [],
        "latest_bridge_status": None,
        "known_environment_problems": [],
        "lessons": [],
        "learning_lessons": [],
        "project_structure_summary": None,
    }


class ProjectStorageService:
    def __init__(self, base_dir: Path) -> None:
        self.runtime_dir = base_dir / "runtime_data"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_dir / "project_memory.json"
        self.lock = threading.Lock()

        self.storage_mode_requested = (os.environ.get("STORAGE_MODE") or "local").strip().lower()
        self.firestore_enabled = str(os.environ.get("FIRESTORE_ENABLED", "false")).lower() == "true"
        self.project_id = (os.environ.get("GCP_PROJECT_ID") or "").strip()
        self.bucket_name = (os.environ.get("GCS_BUCKET_NAME") or "").strip()
        self.storage_backend = "local_json"
        self.storage_message = (
            "Cloud-first memory is using local JSON fallback. This is fine for development, but Cloud Run local storage is temporary."
        )
        self.cloud_ready_notes = [
            "Firestore can later store memory, lessons, chat history, and research tasks.",
            "Google Cloud Storage can later store uploaded files and generated outputs.",
        ]

        if self.storage_mode_requested == "firestore":
            if self.firestore_enabled and self.project_id:
                try:
                    from google.cloud import firestore  # noqa: F401

                    self.storage_backend = "local_json"
                    self.storage_message = (
                        "Firestore mode was requested, but this service is still using safe local JSON fallback in this build."
                    )
                    self.cloud_ready_notes.insert(
                        0,
                        "Firestore libraries are available. The data structure is prepared, but the current build still uses local JSON storage.",
                    )
                except Exception:
                    self.storage_backend = "local_json"
                    self.storage_message = (
                        "Firestore mode was requested, but credentials or libraries were missing. Local JSON fallback is active."
                    )
                    self.cloud_ready_notes.insert(
                        0,
                        "Firestore fallback is active because credentials or libraries are missing.",
                    )

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

        if payload.get("learning_lessons") != payload.get("lessons"):
            payload["learning_lessons"] = list(payload.get("lessons", []))

        if payload.get("codex_prompts") != payload.get("prompt_history"):
            payload["codex_prompts"] = list(payload.get("prompt_history", []))

        return payload

    def _write_payload(self, payload: dict[str, Any]) -> None:
        payload["learning_lessons"] = list(payload.get("lessons", []))
        payload["codex_prompts"] = list(payload.get("prompt_history", []))
        atomic_write_json(self.path, payload)

    def _insert_limited(self, payload: dict[str, Any], key: str, record: dict[str, Any], limit: int) -> dict[str, Any]:
        payload[key].insert(0, record)
        payload[key] = payload[key][:limit]
        return record

    def health_check(self) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()

        return {
            "ok": True,
            "storage_backend": self.storage_backend,
            "storage_mode_requested": self.storage_mode_requested,
            "project_memory_count": len(payload.get("project_memory", [])),
            "assistant_memory_count": len(payload.get("assistant_memory", [])),
            "chat_history_count": len(payload.get("chat_history", [])),
            "research_task_count": len(payload.get("research_tasks", [])),
            "self_improvement_count": len(payload.get("self_improvement", [])),
            "lesson_count": len(payload.get("lessons", [])),
            "has_latest_summary": payload.get("latest_summary") is not None,
            "has_latest_prompt": payload.get("latest_prompt") is not None,
            "has_latest_intelligence_brief": payload.get("latest_intelligence_brief") is not None,
            "cloud_ready_notes": self.cloud_ready_notes,
        }

    def save_project_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": f"memory_{uuid4().hex[:12]}",
                "created_at": utc_now_iso(),
                **entry,
            }
            self._insert_limited(payload, "project_memory", record, 200)
            self._write_payload(payload)
        return record

    def get_project_memory(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("project_memory", [])[:limit]

    def save_assistant_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": f"assistant_memory_{uuid4().hex[:12]}",
                "created_at": utc_now_iso(),
                **entry,
            }
            self._insert_limited(payload, "assistant_memory", record, 200)
            self._write_payload(payload)
        return record

    def get_assistant_memory(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("assistant_memory", [])[:limit]

    def save_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": message.get("id") or f"chat_{uuid4().hex[:12]}",
                "created_at": message.get("created_at") or utc_now_iso(),
                **message,
            }
            self._insert_limited(payload, "chat_history", record, 400)
            self._write_payload(payload)
        return record

    def get_chat_history(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        items = payload.get("chat_history", [])[:limit]
        return list(reversed(items))

    def save_research_task(self, task: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            tasks = payload.get("research_tasks", [])
            existing_index = next((index for index, item in enumerate(tasks) if item.get("research_id") == task.get("research_id")), None)

            if existing_index is None:
                record = {
                    "research_id": task.get("research_id") or f"research_{uuid4().hex[:12]}",
                    "created_at": task.get("created_at") or utc_now_iso(),
                    "updated_at": task.get("updated_at") or utc_now_iso(),
                    **task,
                }
                self._insert_limited(payload, "research_tasks", record, 200)
            else:
                record = {
                    **tasks[existing_index],
                    **task,
                    "updated_at": utc_now_iso(),
                }
                tasks[existing_index] = record
                payload["research_tasks"] = sorted(
                    tasks,
                    key=lambda item: item.get("updated_at", ""),
                    reverse=True,
                )[:200]

            self._write_payload(payload)
        return record

    def get_research_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("research_tasks", [])[:limit]

    def get_research_task(self, research_id: str) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()

        for item in payload.get("research_tasks", []):
            if item.get("research_id") == research_id:
                return item

        return None

    def save_research_result(self, result: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": result.get("id") or f"research_result_{uuid4().hex[:12]}",
                "created_at": result.get("created_at") or utc_now_iso(),
                **result,
            }
            self._insert_limited(payload, "research_results", record, 200)
            self._write_payload(payload)
        return record

    def get_research_results(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("research_results", [])[:limit]

    def save_self_improvement(self, entry: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": entry.get("id") or f"improvement_{uuid4().hex[:12]}",
                "created_at": entry.get("created_at") or utc_now_iso(),
                **entry,
            }
            self._insert_limited(payload, "self_improvement", record, 200)
            self._write_payload(payload)
        return record

    def get_self_improvements(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("self_improvement", [])[:limit]

    def save_latest_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            saved_summary = {
                **summary,
                "saved_at": utc_now_iso(),
            }
            payload["latest_summary"] = saved_summary
            self._insert_limited(payload, "codex_summaries", saved_summary, 100)
            self._write_payload(payload)
        return payload["latest_summary"]

    def get_latest_summary(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("latest_summary")

    def get_codex_summaries(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("codex_summaries", [])[:limit]

    def save_latest_prompt(self, prompt_record: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            saved_record = {
                **prompt_record,
                "saved_at": utc_now_iso(),
            }
            payload["latest_prompt"] = saved_record
            self._insert_limited(payload, "prompt_history", saved_record, 100)
            self._write_payload(payload)
        return saved_record

    def get_latest_prompt(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("latest_prompt")

    def get_prompt_history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("prompt_history", [])[:limit]

    def save_latest_intelligence_brief(self, brief_record: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            saved_record = {
                **brief_record,
                "saved_at": utc_now_iso(),
            }
            payload["latest_intelligence_brief"] = saved_record
            self._insert_limited(payload, "intelligence_history", saved_record, 100)
            self._write_payload(payload)
        return saved_record

    def get_latest_intelligence_brief(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("latest_intelligence_brief")

    def get_intelligence_history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("intelligence_history", [])[:limit]

    def save_latest_bridge_status(self, bridge_status: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            payload["latest_bridge_status"] = {
                **bridge_status,
                "saved_at": utc_now_iso(),
            }
            self._write_payload(payload)
        return payload["latest_bridge_status"]

    def get_latest_bridge_status(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("latest_bridge_status")

    def save_known_environment_problems(self, problems: list[str]) -> list[str]:
        with self.lock:
            payload = self._read_payload()
            payload["known_environment_problems"] = list(dict.fromkeys(problem for problem in problems if problem))
            self._write_payload(payload)
        return payload["known_environment_problems"]

    def get_known_environment_problems(self) -> list[str]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("known_environment_problems", [])

    def save_lesson(self, lesson: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": lesson.get("id") or f"lesson_{uuid4().hex[:12]}",
                "created_at": lesson.get("created_at") or utc_now_iso(),
                **lesson,
            }
            self._insert_limited(payload, "lessons", record, 200)
            self._write_payload(payload)
        return record

    def get_lessons(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("lessons", [])[:limit]

    def save_project_structure_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            payload["project_structure_summary"] = {
                **summary,
                "saved_at": utc_now_iso(),
            }
            self._write_payload(payload)
        return payload["project_structure_summary"]

    def get_project_structure_summary(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("project_structure_summary")
