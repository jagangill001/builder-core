from __future__ import annotations

from threading import RLock
from typing import Any

from app.auth.auth import AuthContext
from app.db.repository import repository
from app.tasks.task_models import utc_now

_AUDIT_FALLBACK: list[dict[str, Any]] = []
_LOCK = RLock()


def record_audit(
    *,
    action: str,
    route: str,
    success: bool,
    auth: AuthContext | None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    actor = _actor_label(auth)
    entry = {
        "timestamp": utc_now(),
        "action": action,
        "route": route,
        "success": success,
        "actor": actor,
        "warnings": warnings or [],
        "errors": errors or [],
    }
    persisted = repository.audit(action, actor, entry)
    entry["persisted"] = persisted
    if not persisted:
        with _LOCK:
            _AUDIT_FALLBACK.append(entry)
            del _AUDIT_FALLBACK[:-200]
    return entry


def read_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    db_entries = repository.list_audit_logs(limit=limit)
    if db_entries:
        return db_entries
    with _LOCK:
        return list(reversed(_AUDIT_FALLBACK[-max(1, min(limit, 200)) :]))


def _actor_label(auth: AuthContext | None) -> str:
    if auth is None:
        return "anonymous"
    if auth.authenticated:
        return f"{auth.role}_authenticated"
    return auth.role or "viewer"
