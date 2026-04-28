from __future__ import annotations

import json
import os
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


def safe_filename(name: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in {".", "-", "_"} else "_" for character in name)
    return cleaned or "builder_core_file.txt"


class LocalFileStore:
    def __init__(self, runtime_dir: Path) -> None:
        self.metadata_path = runtime_dir / "storage_files.json"
        self.files_dir = runtime_dir / "storage_files"
        self.files_dir.mkdir(parents=True, exist_ok=True)

        if not self.metadata_path.exists():
            atomic_write_json(self.metadata_path, {"items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        if not self.metadata_path.exists():
            return []

        try:
            payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        items = payload.get("items", [])
        return items if isinstance(items, list) else []

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        atomic_write_json(self.metadata_path, {"items": items})

    def list_files(self) -> list[dict[str, Any]]:
        return sorted(self._read_items(), key=lambda item: item.get("updated_at", ""), reverse=True)

    def get_file(self, file_id: str) -> Optional[dict[str, Any]]:
        for item in self._read_items():
            if item.get("id") != file_id:
                continue

            record = dict(item)
            file_path = Path(record["local_path"])
            if file_path.exists():
                record["content"] = file_path.read_text(encoding="utf-8")
            return record

        return None

    def create_file(
        self,
        filename: str,
        content: str,
        content_type: str = "text/plain",
        task_id: Optional[str] = None,
    ) -> dict[str, Any]:
        file_id = f"file_{uuid4().hex[:12]}"
        stored_name = f"{file_id}_{safe_filename(filename)}"
        file_path = self.files_dir / stored_name
        file_path.write_text(content, encoding="utf-8")

        timestamp = utc_now_iso()
        record = {
            "id": file_id,
            "filename": filename,
            "content_type": content_type,
            "task_id": task_id,
            "size_bytes": len(content.encode("utf-8")),
            "local_path": str(file_path),
            "storage_backend": "local_files",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        items = self._read_items()
        items.append(record)
        self._write_items(items)
        return record

    def delete_file(self, file_id: str) -> Optional[dict[str, Any]]:
        items = self._read_items()
        removed: Optional[dict[str, Any]] = None
        kept: list[dict[str, Any]] = []

        for item in items:
            if item.get("id") == file_id and removed is None:
                removed = item
                continue

            kept.append(item)

        if removed is None:
            return None

        file_path = Path(removed["local_path"])
        if file_path.exists():
            file_path.unlink()

        self._write_items(kept)
        removed["deleted_at"] = utc_now_iso()
        return removed


class GCSFileStore:
    def __init__(self, bucket_name: str, prefix: str = "builder-core-files") -> None:
        from google.cloud import storage

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/") or "builder-core-files"

    def _blob_name(self, file_id: str, filename: str) -> str:
        return f"{self.prefix}/{file_id}/{safe_filename(filename)}"

    def list_files(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for blob in self.bucket.list_blobs(prefix=f"{self.prefix}/"):
            if blob.name.endswith("/"):
                continue

            parts = blob.name.split("/")
            file_id = parts[1] if len(parts) > 2 else blob.name.replace("/", "_")
            items.append(
                {
                    "id": file_id,
                    "filename": parts[-1],
                    "content_type": blob.content_type,
                    "task_id": None,
                    "size_bytes": blob.size,
                    "gcs_uri": f"gs://{self.bucket_name}/{blob.name}",
                    "storage_backend": "gcs",
                    "created_at": blob.time_created.isoformat() if blob.time_created else None,
                    "updated_at": blob.updated.isoformat() if blob.updated else None,
                }
            )

        return sorted(items, key=lambda item: item.get("updated_at") or "", reverse=True)

    def get_file(self, file_id: str) -> Optional[dict[str, Any]]:
        matches = [item for item in self.list_files() if item["id"] == file_id]
        if not matches:
            return None

        return matches[0]

    def create_file(
        self,
        filename: str,
        content: str,
        content_type: str = "text/plain",
        task_id: Optional[str] = None,
    ) -> dict[str, Any]:
        file_id = f"file_{uuid4().hex[:12]}"
        blob_name = self._blob_name(file_id, filename)
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=content_type)
        blob.reload()

        return {
            "id": file_id,
            "filename": filename,
            "content_type": content_type,
            "task_id": task_id,
            "size_bytes": blob.size,
            "gcs_uri": f"gs://{self.bucket_name}/{blob_name}",
            "storage_backend": "gcs",
            "created_at": blob.time_created.isoformat() if blob.time_created else utc_now_iso(),
            "updated_at": blob.updated.isoformat() if blob.updated else utc_now_iso(),
        }

    def delete_file(self, file_id: str) -> Optional[dict[str, Any]]:
        record = self.get_file(file_id)
        if record is None:
            return None

        gcs_uri = record.get("gcs_uri", "")
        if isinstance(gcs_uri, str) and gcs_uri.startswith(f"gs://{self.bucket_name}/"):
            blob_name = gcs_uri.replace(f"gs://{self.bucket_name}/", "", 1)
            self.bucket.blob(blob_name).delete()

        record["deleted_at"] = utc_now_iso()
        return record


class FileStorageService:
    def __init__(self, base_dir: Path) -> None:
        self.runtime_dir = base_dir / "runtime_data"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.storage_backend = "local_files"
        self.storage_message = "Cloud-first file storage is active. Local fallback is being used because Cloud Storage is not configured."

        bucket_name = (os.environ.get("GCS_BUCKET_NAME") or "").strip()

        if bucket_name:
            try:
                self.store = GCSFileStore(bucket_name)
                self.storage_backend = "gcs"
                self.storage_message = "Cloud-first file storage is active. Google Cloud Storage is enabled."
                return
            except Exception:
                self.storage_backend = "local_files"
                self.storage_message = "Cloud-first file storage is active. Local fallback is being used because Cloud Storage is not configured or not available."

        self.store = LocalFileStore(self.runtime_dir)

    def list_files(self) -> list[dict[str, Any]]:
        return self.store.list_files()

    def get_file(self, file_id: str) -> Optional[dict[str, Any]]:
        return self.store.get_file(file_id)

    def create_file(
        self,
        filename: str,
        content: str,
        content_type: str = "text/plain",
        task_id: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.store.create_file(filename, content, content_type, task_id)

    def delete_file(self, file_id: str) -> Optional[dict[str, Any]]:
        return self.store.delete_file(file_id)
