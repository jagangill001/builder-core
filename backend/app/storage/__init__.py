"""Phase 3 storage package with compatibility for the legacy storage module."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_legacy_path = Path(__file__).resolve().parent.parent / "storage.py"
_legacy_spec = importlib.util.spec_from_file_location("app._legacy_storage", _legacy_path)
_legacy_module = importlib.util.module_from_spec(_legacy_spec) if _legacy_spec and _legacy_spec.loader else None
if _legacy_module is not None and _legacy_spec is not None and _legacy_spec.loader is not None:
    _legacy_spec.loader.exec_module(_legacy_module)

ProjectStorageService = getattr(_legacy_module, "ProjectStorageService", None)
COLLECTION_NAMES = getattr(_legacy_module, "COLLECTION_NAMES", [])
COLLECTION_LIMITS = getattr(_legacy_module, "COLLECTION_LIMITS", {})

if ProjectStorageService is None:
    class ProjectStorageService:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Legacy ProjectStorageService is unavailable.")

from app.storage.storage_backend import (  # noqa: E402
    get_storage_backend,
    get_storage_status,
    read_json,
    read_recent_jsonl,
    save_json,
    save_jsonl,
)

__all__ = [
    "ProjectStorageService",
    "COLLECTION_NAMES",
    "COLLECTION_LIMITS",
    "get_storage_backend",
    "get_storage_status",
    "save_jsonl",
    "read_recent_jsonl",
    "save_json",
    "read_json",
]