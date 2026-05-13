from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.auth import AuthContext
from app.auth.dependencies import get_auth_context

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status(context: AuthContext = Depends(get_auth_context)) -> dict[str, object]:
    return {
        "admin_configured": context.admin_configured,
        "role": context.role,
        "authenticated": context.authenticated,
        "auth_error": context.auth_error,
        "token_visible": False,
    }
