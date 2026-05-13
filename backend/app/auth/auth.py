from __future__ import annotations

import hmac
import os
from dataclasses import dataclass


ROLES = ("viewer", "user", "admin", "owner")


@dataclass(frozen=True, slots=True)
class AuthContext:
    role: str = "viewer"
    authenticated: bool = False
    admin_configured: bool = False
    auth_error: str | None = None


def admin_token_configured() -> bool:
    return bool(os.getenv("ADMIN_TOKEN", "").strip())


def authenticate_token(raw_header: str | None) -> AuthContext:
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    configured = bool(expected)
    if not raw_header:
        return AuthContext(admin_configured=configured)

    token = _extract_token(raw_header)
    if not configured:
        return AuthContext(admin_configured=False, auth_error="admin_not_configured")
    if not token:
        return AuthContext(admin_configured=True, auth_error="missing_bearer_token")
    if hmac.compare_digest(token, expected):
        return AuthContext(role="admin", authenticated=True, admin_configured=True)
    return AuthContext(admin_configured=True, auth_error="invalid_admin_token")


def _extract_token(raw_header: str) -> str:
    value = raw_header.strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value
