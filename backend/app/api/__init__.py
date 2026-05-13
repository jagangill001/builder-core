from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.apps import router as apps_router
from app.api.chat import router as chat_router
from app.api.codex import router as codex_router
from app.api.projects import router as projects_router
from app.api.system import router as system_router
DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://builder-core-frontend-599596796788.us-central1.run.app",
)


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if configured_origins:
        return [
            origin.strip().rstrip("/")
            for origin in configured_origins.split(",")
            if origin.strip()
        ]

    return list(DEFAULT_ALLOWED_ORIGINS)


def create_app() -> FastAPI:
    app = FastAPI(title="Builder Core")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.get("/")
    def home():
        return {"status": "Builder Core Running"}

    app.include_router(chat_router)
    app.include_router(codex_router)
    app.include_router(projects_router)
    app.include_router(apps_router)
    app.include_router(system_router)
    return app


app = create_app()
