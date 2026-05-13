from __future__ import annotations

from fastapi import APIRouter, Depends

from app.audit.audit_log import record_audit
from app.auth.auth import AuthContext
from app.auth.dependencies import require_admin
from app.deployment.deployment_status import deployment_checklist, deployment_health, deployment_status

router = APIRouter(prefix="/deployment", tags=["deployment"])


@router.get("/status")
def get_deployment_status() -> dict[str, object]:
    return deployment_status()


@router.get("/checklist")
def get_deployment_checklist() -> dict[str, object]:
    return {"items": deployment_checklist()}


@router.get("/health")
def get_deployment_health() -> dict[str, object]:
    return deployment_health()


@router.post("/rollback")
def rollback_placeholder(context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = {
        "ok": False,
        "implemented": False,
        "message": "Rollback requires admin, and real rollback execution is not implemented yet.",
        "action_taken": False,
    }
    record_audit(
        action="deployment_rollback_placeholder",
        route="/deployment/rollback",
        success=False,
        auth=context,
        warnings=["Rollback is a placeholder. No Cloud Run action was executed."],
        errors=[],
    )
    return result
