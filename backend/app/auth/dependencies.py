from __future__ import annotations

from fastapi import Header, HTTPException

from app.auth.auth import AuthContext, authenticate_token


def get_auth_context(authorization: str | None = Header(default=None)) -> AuthContext:
    return authenticate_token(authorization)


def require_admin(authorization: str | None = Header(default=None)) -> AuthContext:
    context = authenticate_token(authorization)
    if not context.admin_configured:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "admin_not_configured",
                "message": "Admin actions require ADMIN_TOKEN to be configured on the backend.",
            },
        )
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"code": "admin_required", "message": "Admin token required."},
        )
    if context.role not in {"admin", "owner"}:
        raise HTTPException(
            status_code=403,
            detail={"code": "admin_required", "message": "Valid admin token required."},
        )
    return context
