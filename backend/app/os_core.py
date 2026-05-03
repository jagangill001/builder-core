from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from app.platform_adapter import get_platform_status
except ImportError:
    from platform_adapter import get_platform_status


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BuilderCoreOSService:
    def __init__(
        self,
        storage: Any,
        tool_registry: Any,
        model_router: Any,
        platform_status_provider: Any = get_platform_status,
        security_monitor: Any | None = None,
    ) -> None:
        self.storage = storage
        self.tool_registry = tool_registry
        self.model_router = model_router
        self.platform_status_provider = platform_status_provider
        self.security_monitor = security_monitor

    def get_os_status(self) -> dict[str, Any]:
        storage_status = self.storage.get_storage_status()
        platform_status = self.platform_status_provider()
        tool_status = self.tool_registry.get_tool_status() if self.tool_registry else {}
        model_status = self.model_router.get_active_model_status() if self.model_router else {}
        security_summary = self.security_monitor.get_security_summary() if self.security_monitor else {}
        warnings = []
        warnings.extend(storage_status.get("warnings") or [])
        warnings.extend(platform_status.get("warnings") or [])
        warnings.extend(model_status.get("warnings") or [])
        warnings.append("Builder Core OS is a foundation-stage internal system, not AGI or human consciousness.")

        payload = {
            "system": "Builder Core OS",
            "version_stage": "foundation",
            "storage": "firestore" if storage_status.get("using_firestore") else "local",
            "agents_enabled": True,
            "tools_enabled": bool(tool_status.get("enabled_tools", 0)),
            "private_search_enabled": True,
            "security_monitor_enabled": bool(security_summary) or self.security_monitor is not None,
            "safety_mode": "human_approval_required",
            "high_risk_control": "blocked_by_default",
            "external_ai_required": False,
            "external_search_api_required": False,
            "portability": platform_status,
            "storage_status": storage_status,
            "tool_registry_status": tool_status,
            "model_router_status": model_status,
            "security_status": security_summary,
            "warnings": list(dict.fromkeys(str(item) for item in warnings if item)),
            "created_at": utc_now_iso(),
        }
        self.storage.save_record("os_status", payload)
        return payload
