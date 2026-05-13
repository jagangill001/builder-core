from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ConnectorStatus:
    name: str
    enabled: bool
    configured: bool
    provider: str = "none"
    required_env_vars: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    health: str = "unknown"
    last_error: str | None = None
    admin_required: bool = False
    placeholder: bool = False
    is_real_execution: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "configured": self.configured,
            "provider": self.provider,
            "required_env_vars": self.required_env_vars,
            "capabilities": self.capabilities,
            "health": self.health,
            "last_error": self.last_error,
            "admin_required": self.admin_required,
            "placeholder": self.placeholder,
            "is_real_execution": self.is_real_execution,
        }


class ConnectorInterface(Protocol):
    name: str

    def status(self) -> ConnectorStatus:
        ...

    def health_check(self) -> dict[str, Any]:
        ...

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class BaseConnector:
    name = "base"
    required_env_vars: list[str] = []
    capabilities: list[str] = []
    provider_env_var: str | None = None
    admin_required = False

    def configured(self) -> bool:
        return env_configured(*self.required_env_vars)

    def provider(self) -> str:
        if not self.provider_env_var:
            return "none"
        value = os.getenv(self.provider_env_var, "none").strip().lower()
        return value if value in {"none", "placeholder", "custom"} else "custom"

    def status(self) -> ConnectorStatus:
        configured = self.configured()
        provider = self.provider()
        real_execution = configured and provider == "custom" and self.has_real_adapter()
        return ConnectorStatus(
            name=self.name,
            enabled=configured,
            configured=configured,
            provider=provider,
            required_env_vars=self.required_env_vars,
            capabilities=self.capabilities,
            health=self._health(configured, provider, real_execution),
            last_error=self._last_error(configured, provider, real_execution),
            admin_required=self.admin_required,
            placeholder=not real_execution,
            is_real_execution=real_execution,
        )

    def health_check(self) -> dict[str, Any]:
        return self.status().as_dict()

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        status = self.status()
        if not status.configured:
            return {
                "ok": False,
                "code": "not_configured",
                "message": f"{self.name} connector is not configured.",
                "status": status.as_dict(),
            }
        return {
            "ok": False,
            "code": "provider_missing",
            "message": f"{self.name} connector provider '{status.provider}' is not implemented for real execution.",
            "status": status.as_dict(),
            "payload": payload,
        }

    def has_real_adapter(self) -> bool:
        return False

    def _health(self, configured: bool, provider: str, real_execution: bool) -> str:
        if not configured:
            return "not_configured"
        if real_execution:
            return "real"
        if provider in {"none", "placeholder", "custom"}:
            return "provider_missing"
        return "placeholder"

    def _last_error(self, configured: bool, provider: str, real_execution: bool) -> str | None:
        if not configured:
            missing = ", ".join(missing_env_vars(*self.required_env_vars))
            return f"Missing env vars: {missing}" if missing else "Connector is not configured."
        if not real_execution:
            return f"Provider '{provider}' is not implemented for real execution."
        return None


def env_configured(*names: str) -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in names)


def missing_env_vars(*names: str) -> list[str]:
    return [name for name in names if not os.getenv(name, "").strip()]
