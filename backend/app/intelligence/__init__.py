"""Phase 2 intelligence package with compatibility for the legacy intelligence module."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_legacy_path = Path(__file__).resolve().parent.parent / "intelligence.py"
_legacy_spec = importlib.util.spec_from_file_location("app._legacy_intelligence", _legacy_path)
_legacy_module = importlib.util.module_from_spec(_legacy_spec) if _legacy_spec and _legacy_spec.loader else None
if _legacy_module is not None and _legacy_spec is not None and _legacy_spec.loader is not None:
    _legacy_spec.loader.exec_module(_legacy_module)

build_intelligence_brief = getattr(_legacy_module, "build_intelligence_brief", None)
get_supported_modes = getattr(_legacy_module, "get_supported_modes", None)
INTELLIGENCE_MODES: dict[str, dict[str, Any]] = getattr(_legacy_module, "INTELLIGENCE_MODES", {})

if build_intelligence_brief is None:
    def build_intelligence_brief(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "summary": "Legacy intelligence brief builder is unavailable."}

if get_supported_modes is None:
    def get_supported_modes() -> list[str]:
        return []
