from __future__ import annotations

import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.audit.audit_routes import router as audit_router
from app.api.apps import router as legacy_apps_router
from app.api.chat import router as legacy_chat_router
from app.api.codex import router as legacy_codex_router
from app.api.projects import router as legacy_projects_router
from app.auth.auth import admin_token_configured
from app.auth.auth_routes import router as auth_router
from app.connectors.connector_routes import router as connector_router
from app.connectors.registry import configured_connector_map, integration_status
from app.core.audit_log import read_recent_audit_entries
from app.core.command_router import route_command
from app.db.database import initialize_database, runtime_status
from app.deployment.deployment_routes import router as deployment_router
from app.github.github_routes import router as github_router
from app.integrations.integration_routes import router as integration_router
from app.memory.project_memory import get_project_summary
from app.models.command_models import CommandRequest, CommandResponse, SystemStatus
from app.project.project_routes import router as project_router
from app.system.system_routes import router as system_router
from app.tasks.task_routes import router as task_router
from app.workers.worker import worker_status

DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://builder-core-frontend-599596796788.us-central1.run.app",
)


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS") or os.getenv("FRONTEND_ORIGIN")
    if configured_origins:
        return [
            origin.strip().rstrip("/")
            for origin in configured_origins.split(",")
            if origin.strip()
        ]
    return list(DEFAULT_ALLOWED_ORIGINS)


def create_app() -> FastAPI:
    database_ready = initialize_database()
    app = FastAPI(title="Builder Core", version="5.25.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/")
    def home() -> dict[str, str]:
        return {"status": "Builder Core Running"}

    @app.get("/system/status")
    def system_status() -> dict[str, object]:
        database = runtime_status()
        connectors = configured_connector_map()
        memory_loaded = bool(get_project_summary())
        return {
            "status": "ok",
            "service": "builder-core",
            "phase": "phase_5_to_25_command_os_foundation",
            "backend_online": True,
            "task_engine_ready": True,
            "project_memory_loaded": memory_loaded,
            "configured_connectors": connectors,
            "frontend_allowed_origins": get_allowed_origins(),
            "database_connected": bool(database.get("connected")) and database_ready,
            "database": database,
            "worker": worker_status(),
            "worker_enabled": bool(worker_status()["enabled"]),
            "auth_enabled": admin_token_configured(),
            "integration_status": integration_status(),
            "secrets_visible": False,
            "placeholders": [
                "search provider adapter",
                "weather provider adapter",
                "news provider adapter",
                "real Codex execution",
                "Cloud Run rollback execution",
                "external worker queue",
            ],
        }

    @app.get("/system/legacy-status", response_model=SystemStatus)
    def legacy_system_status() -> SystemStatus:
        return SystemStatus(
            status="ok",
            service="builder-core",
            phase="phase_1_core_command_system",
            live_search_connected=False,
            codex_direct_connection=False,
            security_firewall=True,
            audit_log=True,
        )

    @app.post("/command", response_model=CommandResponse)
    def command(payload: CommandRequest) -> CommandResponse:
        return route_command(payload)

    @app.get("/audit/recent")
    def recent_audit_entries(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        return {
            "limit": limit,
            "items": read_recent_audit_entries(limit=limit),
        }

    app.include_router(task_router)
    app.include_router(connector_router)
    app.include_router(integration_router)
    app.include_router(project_router)
    app.include_router(auth_router)
    app.include_router(audit_router)
    app.include_router(deployment_router)
    app.include_router(github_router)
    app.include_router(system_router)
    app.include_router(legacy_chat_router)
    app.include_router(legacy_codex_router)
    app.include_router(legacy_projects_router)
    app.include_router(legacy_apps_router)
    return app


app = create_app()
