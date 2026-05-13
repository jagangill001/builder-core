from __future__ import annotations

import os
from typing import Any

from app.auth.auth import admin_token_configured
from app.connectors.base import ConnectorStatus, env_configured
from app.connectors.codex_bridge import CodexBridgeConnector
from app.connectors.github import GitHubConnector
from app.connectors.news import NewsConnector
from app.connectors.search import SearchConnector
from app.connectors.weather import WeatherConnector
from app.db.database import runtime_status


def connector_statuses() -> list[dict[str, Any]]:
    statuses = [
        SearchConnector().status(),
        WeatherConnector().status(),
        NewsConnector().status(),
        GitHubConnector().status(),
        CodexBridgeConnector().status(),
        _deployment_status(),
        _database_status(),
        _memory_status(),
        _future_placeholder("gmail", ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"]),
        _future_placeholder("drive", ["GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET"]),
        _future_placeholder("calendar", ["GOOGLE_CALENDAR_CLIENT_ID", "GOOGLE_CALENDAR_CLIENT_SECRET"]),
    ]
    return [status.as_dict() for status in statuses]


def get_connector_status(name: str) -> dict[str, Any] | None:
    normalized = name.strip().lower()
    for status in connector_statuses():
        if status["name"] == normalized:
            return status
    return None


def configured_connector_map() -> dict[str, bool]:
    return {status["name"]: bool(status["configured"]) for status in connector_statuses()}


def _deployment_status() -> ConnectorStatus:
    configured = env_configured("BACKEND_PUBLIC_URL", "FRONTEND_PUBLIC_URL")
    return ConnectorStatus(
        name="deployment",
        enabled=True,
        configured=configured,
        required_env_vars=["BACKEND_PUBLIC_URL", "FRONTEND_PUBLIC_URL"],
        capabilities=["health_check", "checklist", "rollback_placeholder"],
        health="ready_for_health_checks" if configured else "urls_not_configured",
        admin_required=True,
        placeholder=True,
    )


def _database_status() -> ConnectorStatus:
    status = runtime_status()
    connected = bool(status.get("connected"))
    provider = str(status.get("provider") or "memory")
    return ConnectorStatus(
        name="database",
        enabled=True,
        configured=connected,
        provider=provider if connected else "memory",
        required_env_vars=["DATABASE_URL"],
        capabilities=["task_storage", "memory_storage", "audit_storage"],
        health="connected" if connected else "in_memory_fallback",
        last_error=None if connected else str(status.get("last_error") or "Database unavailable; in-memory task store can still run."),
        is_real_execution=connected,
    )


def _memory_status() -> ConnectorStatus:
    return ConnectorStatus(
        name="memory",
        enabled=True,
        configured=True,
        required_env_vars=[],
        capabilities=["project_summary", "task_summaries", "lessons_learned"],
        health="ready",
        admin_required=False,
    )


def _future_placeholder(name: str, required_env_vars: list[str]) -> ConnectorStatus:
    configured = env_configured(*required_env_vars)
    return ConnectorStatus(
        name=name,
        enabled=False,
        configured=configured,
        required_env_vars=required_env_vars,
        capabilities=["future_connector_placeholder"],
        health="placeholder",
        last_error="Connector placeholder only. No live integration is implemented.",
        admin_required=True,
        placeholder=True,
    )


def integration_status() -> dict[str, Any]:
    return {
        "connectors": connector_statuses(),
        "admin": {
            "enabled": admin_token_configured(),
            "token_visible": False,
        },
    }
