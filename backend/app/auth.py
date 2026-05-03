from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Header, HTTPException, Request


ADMIN_KEY_HEADER = "X-Admin-Key"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _configured_admin_key() -> str:
    return str(os.environ.get("ADMIN_API_KEY") or "").strip()


def is_admin_auth_configured() -> bool:
    return bool(_configured_admin_key())


def get_admin_auth_status() -> dict[str, Any]:
    configured = is_admin_auth_configured()
    warnings = []
    if not configured:
        warnings.append(
            "ADMIN_API_KEY is not configured. Admin dashboard endpoints are protected but unavailable until the key is set."
        )
    return {
        "admin_auth_configured": configured,
        "protected_endpoints_enabled": True,
        "admin_key_header": ADMIN_KEY_HEADER,
        "warnings": warnings,
    }


def _record_auth_event(request: Request, status: str, reason: str) -> None:
    try:
        storage = getattr(request.app.state, "project_storage", None)
        if storage is None:
            return
        path = str(getattr(getattr(request, "url", None), "path", "") or "")
        method = str(getattr(request, "method", "") or "")
        client = getattr(request, "client", None)
        storage.save_record(
            "admin_auth_events",
            {
                "id": f"admin_auth_event_{uuid4().hex[:12]}",
                "status": status,
                "reason": reason,
                "path": path,
                "method": method,
                "ip_address": getattr(client, "host", None),
                "created_at": utc_now_iso(),
            },
        )
    except Exception:
        return


async def require_admin(
    request: Request,
    x_admin_key: str | None = Header(default=None, alias=ADMIN_KEY_HEADER),
) -> dict[str, Any]:
    expected = _configured_admin_key()
    if not expected:
        _record_auth_event(request, "blocked", "ADMIN_API_KEY is not configured.")
        raise HTTPException(status_code=403, detail="Admin authentication is not configured.")

    supplied = str(x_admin_key or "").strip()
    if not supplied:
        _record_auth_event(request, "missing", "Admin key header is missing.")
        raise HTTPException(status_code=401, detail="Admin key required.")

    if supplied != expected:
        _record_auth_event(request, "rejected", "Admin key was rejected.")
        raise HTTPException(status_code=403, detail="Admin key rejected.")

    _record_auth_event(request, "approved", "Admin key accepted.")
    return {"ok": True, "admin": True}
