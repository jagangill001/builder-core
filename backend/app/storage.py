from __future__ import annotations

import json
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


class ProjectStorageService:
    def __init__(self, base_dir: Path) -> None:
        self.runtime_dir = base_dir / "runtime_data"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.storage_backend = "local_json"
        self.storage_message = (
            "Project memory is using local JSON storage. This works for development, but Cloud Run local storage is temporary."
        )
        self.path = self.runtime_dir / "project_memory.json"
        self.lock = threading.Lock()

        if not self.path.exists():
            atomic_write_json(
                self.path,
                {
                    "project_memory": [],
                    "latest_summary": None,
                    "latest_prompt": None,
                    "prompt_history": [],
                    "latest_bridge_status": None,
                    "known_environment_problems": [],
                    "lessons": [],
                    "project_structure_summary": None,
                },
            )

    def _read_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "project_memory": [],
                "latest_summary": None,
                "latest_prompt": None,
                "prompt_history": [],
                "latest_bridge_status": None,
                "known_environment_problems": [],
                "lessons": [],
                "project_structure_summary": None,
            }

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "project_memory": [],
                "latest_summary": None,
                "latest_prompt": None,
                "prompt_history": [],
                "latest_bridge_status": None,
                "known_environment_problems": [],
                "lessons": [],
                "project_structure_summary": None,
            }

        payload.setdefault("project_memory", [])
        payload.setdefault("latest_summary", None)
        payload.setdefault("latest_prompt", None)
        payload.setdefault("prompt_history", [])
        payload.setdefault("latest_bridge_status", None)
        payload.setdefault("known_environment_problems", [])
        payload.setdefault("lessons", [])
        payload.setdefault("project_structure_summary", None)
        return payload

    def _write_payload(self, payload: dict[str, Any]) -> None:
        atomic_write_json(self.path, payload)

    def health_check(self) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()

        return {
            "ok": True,
            "storage_backend": self.storage_backend,
            "project_memory_count": len(payload.get("project_memory", [])),
            "lesson_count": len(payload.get("lessons", [])),
            "has_latest_summary": payload.get("latest_summary") is not None,
            "has_latest_prompt": payload.get("latest_prompt") is not None,
        }

    def save_project_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            record = {
                "id": f"memory_{uuid4().hex[:12]}",
                "created_at": utc_now_iso(),
                **entry,
            }
            payload["project_memory"].insert(0, record)
            payload["project_memory"] = payload["project_memory"][:200]
            self._write_payload(payload)
        return record

    def get_project_memory(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("project_memory", [])[:limit]

    def save_latest_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            payload["latest_summary"] = {
                **summary,
                "saved_at": utc_now_iso(),
            }
            self._write_payload(payload)
        return payload["latest_summary"]

    def get_latest_summary(self) -> Optional[dict[str, Any]]:
        with self.lock:
            payload = self._read_payload()
        return payload.get("latest_summary")

    def save_latest_prompt(self, prompt_record: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            payload = self._read_payload()
            saved_record = {
                **prompt_record,
                "saved_at": utc_now_iso(),
            }
            payload["latest_prompt"] = saved_record
            payload["prompt_history"].insert(0, saved_record)
            payload["prompt_history"] = payload["prompt_history"][:100]
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
                "id": f"lesson_{uuid4().hex[:12]}",
                "created_at": utc_now_iso(),
                **lesson,
            }
            payload["lessons"].insert(0, record)
            payload["lessons"] = payload["lessons"][:200]
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
