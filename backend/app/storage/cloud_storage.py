from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

_COLLECTION_RE = re.compile(r"[^a-zA-Z0-9_\-]")

try:
    from google.cloud import storage as gcs_storage
except Exception:  # pragma: no cover - optional dependency/runtime credentials
    gcs_storage = None

try:
    from google.cloud import firestore as gcp_firestore
except Exception:  # pragma: no cover - optional dependency/runtime credentials
    gcp_firestore = None


class CloudStorageBackend:
    backend_name = "gcs"

    def __init__(self, bucket_name: str, project: str | None = None) -> None:
        if gcs_storage is None:
            raise RuntimeError("google-cloud-storage is not available.")
        if not bucket_name:
            raise RuntimeError("GCS_BUCKET_NAME is not configured.")
        client = gcs_storage.Client(project=project or None)
        self.bucket_name = bucket_name
        self.bucket = client.bucket(bucket_name)

    def save_jsonl(self, collection_name: str, record: dict[str, Any]) -> dict[str, Any]:
        blob = self.bucket.blob(self._jsonl_name(collection_name))
        existing = blob.download_as_text(encoding="utf-8") if blob.exists() else ""
        line = json.dumps(record, ensure_ascii=False, default=str)
        blob.upload_from_string(existing + line + "\n", content_type="application/jsonl")
        return record

    def read_recent_jsonl(self, collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 500))
        blob = self.bucket.blob(self._jsonl_name(collection_name))
        if not blob.exists():
            return []
        lines = blob.download_as_text(encoding="utf-8").splitlines()
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
        blob = self.bucket.blob(self._json_name(collection_name, object_id))
        blob.upload_from_string(json.dumps(record, indent=2, ensure_ascii=False, default=str), content_type="application/json")
        return record

    def read_json(self, collection_name: str, object_id: str) -> dict[str, Any] | None:
        blob = self.bucket.blob(self._json_name(collection_name, object_id))
        if not blob.exists():
            return None
        try:
            value = json.loads(blob.download_as_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def _jsonl_name(self, collection_name: str) -> str:
        return f"builder_core/{_safe_name(collection_name)}.jsonl"

    def _json_name(self, collection_name: str, object_id: str) -> str:
        return f"builder_core/{_safe_name(collection_name)}/{_safe_name(object_id)}.json"


class FirestoreStorageBackend:
    backend_name = "firestore"

    def __init__(self, project: str) -> None:
        if gcp_firestore is None:
            raise RuntimeError("google-cloud-firestore is not available.")
        if not project:
            raise RuntimeError("GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT is not configured.")
        self.client = gcp_firestore.Client(project=project)

    def save_jsonl(self, collection_name: str, record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(record)
        payload.setdefault("id", _record_id(payload))
        payload.setdefault("created_at", _now())
        payload.setdefault("updated_at", payload.get("created_at"))
        self.client.collection(_collection(collection_name)).document(str(payload["id"])).set(payload)
        return record

    def read_recent_jsonl(self, collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 500))
        documents = self.client.collection(_collection(collection_name)).limit(bounded_limit).stream()
        items = [_normalize(document.to_dict() or {}) for document in documents]
        return sorted(items, key=lambda item: str(item.get("updated_at") or item.get("timestamp") or item.get("created_at") or ""), reverse=True)[:bounded_limit]

    def save_json(self, collection_name: str, object_id: str, record: dict[str, Any]) -> dict[str, Any]:
        payload = dict(record)
        payload.setdefault("id", object_id)
        payload.setdefault("updated_at", _now())
        self.client.collection(_collection(collection_name)).document(_safe_name(object_id)).set(payload)
        return record

    def read_json(self, collection_name: str, object_id: str) -> dict[str, Any] | None:
        document = self.client.collection(_collection(collection_name)).document(_safe_name(object_id)).get()
        if not document.exists:
            return None
        value = _normalize(document.to_dict() or {})
        return value if isinstance(value, dict) else None


def _collection(collection_name: str) -> str:
    return f"builder_core_phase3_{_safe_name(collection_name)}"


def _record_id(record: dict[str, Any]) -> str:
    for key in ("id", "command_id", "approval_id", "sandbox_id", "report_id", "task_id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return _safe_name(value)
    return f"record_{uuid4().hex[:12]}"


def _safe_name(value: str) -> str:
    cleaned = _COLLECTION_RE.sub("_", str(value).strip())
    return cleaned or "record"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value