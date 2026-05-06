from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_COLLECTION_RE = re.compile(r"[^a-zA-Z0-9_\-]")


class LocalStorageBackend:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or DATA_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save_jsonl(self, collection_name: str, record: dict[str, Any]) -> dict[str, Any]:
        path = self._jsonl_path(collection_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def read_recent_jsonl(self, collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 500))
        path = self._jsonl_path(collection_name)
        if not path.exists():
            return []
        with self._lock:
            lines = path.read_text(encoding="utf-8").splitlines()
        items: list[dict[str, Any]] = []
        for line in lines[-bounded_limit:]:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                items.append(value)
        items.reverse()
        return items

    def save_json(self, collection_name: str, object_id: str, record: dict[str, Any]) -> dict[str, Any]:
        path = self._json_path(collection_name, object_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(record, indent=2, ensure_ascii=False, default=str)
        with self._lock:
            path.write_text(payload, encoding="utf-8")
        return record

    def read_json(self, collection_name: str, object_id: str) -> dict[str, Any] | None:
        path = self._json_path(collection_name, object_id)
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def _jsonl_path(self, collection_name: str) -> Path:
        return self.base_dir / f"{_safe_name(collection_name)}.jsonl"

    def _json_path(self, collection_name: str, object_id: str) -> Path:
        return self.base_dir / _safe_name(collection_name) / f"{_safe_name(object_id)}.json"


def _safe_name(value: str) -> str:
    cleaned = _COLLECTION_RE.sub("_", str(value).strip())
    return cleaned or "record"