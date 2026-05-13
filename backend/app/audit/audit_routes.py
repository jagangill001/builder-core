from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.audit.audit_log import read_audit_logs
from app.auth.auth import AuthContext
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    _context: AuthContext = Depends(require_admin),
) -> dict[str, object]:
    return {"items": read_audit_logs(limit=limit)}
