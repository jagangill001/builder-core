"""Phase 3 connector package with compatibility for the legacy connector registry."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_legacy_path = Path(__file__).resolve().parent.parent / "connectors.py"
_legacy_spec = importlib.util.spec_from_file_location("app._legacy_connectors", _legacy_path)
_legacy_module = importlib.util.module_from_spec(_legacy_spec) if _legacy_spec and _legacy_spec.loader else None
if _legacy_module is not None and _legacy_spec is not None and _legacy_spec.loader is not None:
    _legacy_spec.loader.exec_module(_legacy_module)

CONNECTORS = getattr(_legacy_module, "CONNECTORS", [])
ConnectorRegistryService = getattr(_legacy_module, "ConnectorRegistryService", None)
list_available_connectors = getattr(_legacy_module, "list_available_connectors", None)

if ConnectorRegistryService is None:
    class ConnectorRegistryService:  # type: ignore[no-redef]
        def list_connectors(self) -> list[dict[str, Any]]:
            return []

        def get_status(self) -> dict[str, Any]:
            return {"total_connectors": 0, "available": 0, "future_ready": 0, "blocked": 0, "items": []}

if list_available_connectors is None:
    def list_available_connectors() -> list[dict[str, Any]]:
        return ConnectorRegistryService().list_connectors()

from app.connectors.search_connector import (  # noqa: E402
    LIVE_INTERNET_NOT_CONNECTED,
    SearchConnector,
    get_search_status,
)

__all__ = [
    "CONNECTORS",
    "ConnectorRegistryService",
    "list_available_connectors",
    "LIVE_INTERNET_NOT_CONNECTED",
    "SearchConnector",
    "get_search_status",
]