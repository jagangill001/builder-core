from __future__ import annotations

import os
from time import perf_counter
from urllib.error import URLError
from urllib.request import urlopen

from app.db.database import runtime_status


def deployment_status() -> dict[str, object]:
    backend_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
    frontend_url = os.getenv("FRONTEND_PUBLIC_URL", "").strip()
    return {
        "cloud_run": {
            "backend_service": backend_url or None,
            "frontend_service": frontend_url or None,
            "config_placeholder": True,
        },
        "github_actions": {
            "status": "placeholder",
            "message": "GitHub Actions status can be read when GitHub connector is configured.",
        },
        "backend_health": _check_url(backend_url),
        "frontend_health": _check_url(frontend_url),
        "environment_checklist": deployment_checklist(),
        "deploy_history": {
            "items": [],
            "placeholder": True,
            "message": "Deploy history is not connected yet.",
        },
        "rollback": {
            "implemented": False,
            "admin_required": True,
            "message": "Rollback is a safety placeholder. No Cloud Run rollback is executed.",
        },
    }


def deployment_checklist() -> list[dict[str, object]]:
    db_status = runtime_status()
    return [
        {"name": "ADMIN_TOKEN configured", "ok": bool(os.getenv("ADMIN_TOKEN", "").strip())},
        {"name": "FRONTEND_ORIGIN configured", "ok": bool(os.getenv("FRONTEND_ORIGIN", "").strip())},
        {"name": "BACKEND_PUBLIC_URL configured", "ok": bool(os.getenv("BACKEND_PUBLIC_URL", "").strip())},
        {"name": "FRONTEND_PUBLIC_URL configured", "ok": bool(os.getenv("FRONTEND_PUBLIC_URL", "").strip())},
        {
            "name": "GitHub vars configured",
            "ok": all(bool(os.getenv(name, "").strip()) for name in ("GITHUB_TOKEN", "GITHUB_REPO_OWNER", "GITHUB_REPO_NAME")),
        },
        {
            "name": "Database URL configured or default SQLite active",
            "ok": bool(db_status.get("connected")),
            "details": {
                "database_url_configured": db_status.get("database_url_configured"),
                "provider": db_status.get("provider"),
                "fallback_in_memory": db_status.get("fallback_in_memory"),
            },
        },
        {"name": "Rollback implementation connected", "ok": False, "placeholder": True},
    ]


def deployment_health() -> dict[str, object]:
    backend_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
    frontend_url = os.getenv("FRONTEND_PUBLIC_URL", "").strip()
    backend_health = _check_url(backend_url)
    frontend_health = _check_url(frontend_url)
    warnings: list[str] = []
    if not backend_health.get("reachable"):
        warnings.append("Backend public URL is not configured or not reachable.")
    if not frontend_health.get("reachable"):
        warnings.append("Frontend public URL is not configured or not reachable.")
    return {
        "backend": backend_health,
        "frontend": frontend_health,
        "environment_checklist": deployment_checklist(),
        "warnings": warnings,
    }


def _check_url(url: str) -> dict[str, object]:
    if not url:
        return {
            "url_configured": False,
            "reachable": False,
            "status_code": None,
            "response_time_ms": None,
            "error": "URL not configured.",
        }
    started = perf_counter()
    try:
        with urlopen(url, timeout=8) as response:
            elapsed = round((perf_counter() - started) * 1000, 2)
            return {
                "url_configured": True,
                "reachable": 200 <= response.status < 500,
                "status_code": response.status,
                "response_time_ms": elapsed,
                "error": None,
            }
    except URLError as exc:
        elapsed = round((perf_counter() - started) * 1000, 2)
        return {
            "url_configured": True,
            "reachable": False,
            "status_code": None,
            "response_time_ms": elapsed,
            "error": str(exc.reason)[:240],
        }
