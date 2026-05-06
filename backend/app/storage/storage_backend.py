from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.storage.local_storage import DATA_DIR, LocalStorageBackend

CLOUD_NOT_CONFIGURED = "Cloud storage is not configured yet."


def _env_truthy(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


class StorageBackendFacade:
    def __init__(self) -> None:
        self.requested_mode = (os.getenv("BUILDER_STORAGE_MODE") or os.getenv("STORAGE_MODE") or "local").strip().lower()
        self.bucket_name = (os.getenv("GCS_BUCKET_NAME") or "").strip() or None
        self.project_id = (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "").strip() or None
        self.firestore_enabled = _env_truthy("FIRESTORE_ENABLED")
        self.backend: Any = LocalStorageBackend(DATA_DIR)
        self.storage_mode = "local"
        self.cloud_backend: str | None = None
        self.cloud_storage_configured = False
        self.local_fallback = True
        self.warning: str | None = None
        self.message = CLOUD_NOT_CONFIGURED

        self._initialize_cloud_if_configured()

    def _initialize_cloud_if_configured(self) -> None:
        should_use_firestore = self.requested_mode == "firestore" or (self.firestore_enabled and bool(self.project_id))
        should_use_gcs = self.requested_mode in {"cloud", "gcs"} or bool(self.bucket_name)

        if should_use_firestore and self.project_id:
            try:
                from app.storage.cloud_storage import FirestoreStorageBackend

                self.backend = FirestoreStorageBackend(project=self.project_id)
                self.storage_mode = "cloud"
                self.cloud_backend = "firestore"
                self.cloud_storage_configured = True
                self.local_fallback = False
                self.message = "Cloud storage is configured through existing Firestore settings."
                return
            except Exception as error:  # pragma: no cover - depends on Cloud Run credentials
                self.warning = f"Firestore storage could not initialize, using local fallback: {error}"

        if should_use_gcs and self.bucket_name:
            try:
                from app.storage.cloud_storage import CloudStorageBackend

                self.backend = CloudStorageBackend(bucket_name=self.bucket_name, project=self.project_id)
                self.storage_mode = "cloud"
                self.cloud_backend = "gcs"
                self.cloud_storage_configured = True
                self.local_fallback = False
                self.message = "Cloud storage is configured through Google Cloud Storage."
                return
            except Exception as error:  # pragma: no cover - depends on Cloud Run credentials
                self.warning = f"Google Cloud Storage could not initialize, using local fallback: {error}"

        if self.requested_mode in {"cloud", "gcs"} and not self.bucket_name:
            self.warning = "Cloud storage was requested but GCS_BUCKET_NAME is missing."
        elif self.requested_mode == "firestore" and not self.project_id:
            self.warning = "Firestore storage was requested but GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT is missing."

    def save_jsonl(self, collection_name: str, record: dict[str, Any]) -> dict[str, Any]:
        return self.backend.save_jsonl(collection_name, record)

    def read_recent_jsonl(self, collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.backend.read_recent_jsonl(collection_name, limit)

    def save_json(self, collection_name: str, object_id: str, record: dict[str, Any]) -> dict[str, Any]:
        return self.backend.save_json(collection_name, object_id, record)

    def read_json(self, collection_name: str, object_id: str) -> dict[str, Any] | None:
        return self.backend.read_json(collection_name, object_id)

    def status(self) -> dict[str, Any]:
        warnings = []
        if self.warning:
            warnings.append(self.warning)
        if self.storage_mode == "local":
            warnings.append(CLOUD_NOT_CONFIGURED)
        return {
            "storage_mode": self.storage_mode,
            "cloud_backend": self.cloud_backend,
            "requested_mode": self.requested_mode,
            "cloud_storage_configured": self.cloud_storage_configured,
            "bucket_name": self.bucket_name,
            "project_id": self.project_id,
            "firestore_enabled": self.firestore_enabled,
            "local_fallback": self.local_fallback,
            "local_data_dir": str(Path(DATA_DIR)),
            "message": self.message,
            "warnings": list(dict.fromkeys(warnings)),
        }


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackendFacade:
    return StorageBackendFacade()


def get_storage_status() -> dict[str, Any]:
    return get_storage_backend().status()


def save_jsonl(collection_name: str, record: dict[str, Any]) -> dict[str, Any]:
    return get_storage_backend().save_jsonl(collection_name, record)


def read_recent_jsonl(collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
    return get_storage_backend().read_recent_jsonl(collection_name, limit)


def save_json(collection_name: str, object_id: str, record: dict[str, Any]) -> dict[str, Any]:
    return get_storage_backend().save_json(collection_name, object_id, record)


def read_json(collection_name: str, object_id: str) -> dict[str, Any] | None:
    return get_storage_backend().read_json(collection_name, object_id)