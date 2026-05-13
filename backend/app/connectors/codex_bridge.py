from __future__ import annotations

from typing import Any

from app.coding.instruction_builder import build_codex_task_package
from app.connectors.base import ConnectorStatus, env_configured


class CodexBridgeConnector:
    name = "codex_bridge"
    required_env_vars = ["CODEX_API_KEY"]

    def status(self) -> ConnectorStatus:
        configured = env_configured(*self.required_env_vars)
        return ConnectorStatus(
            name=self.name,
            enabled=configured,
            configured=configured,
            required_env_vars=self.required_env_vars,
            capabilities=["package_task", "execution_placeholder"],
            health="package_only" if configured else "not_configured",
            last_error=None if configured else "CODEX_API_KEY is not configured.",
            admin_required=True,
            placeholder=True,
        )

    def package_task(self, instruction: str, repo: str = "jagangill001/builder-core") -> dict[str, Any]:
        package = build_codex_task_package(instruction=instruction, repo=repo)
        return {
            "ok": True,
            "package": package,
            "executed": False,
            "message": "Codex package created, but real Codex execution is not configured.",
        }
