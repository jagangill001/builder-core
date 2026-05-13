from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.audit.audit_log import record_audit
from app.auth.auth import AuthContext
from app.auth.dependencies import require_admin
from app.connectors.codex_bridge import CodexBridgeConnector
from app.connectors.github import GitHubConnector
from app.connectors.registry import integration_status

router = APIRouter(prefix="/integrations", tags=["integrations"])


class IssueRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""


class CodexPackageRequest(BaseModel):
    instruction: str = Field(min_length=1)
    repo: str = "jagangill001/builder-core"


@router.get("/status")
def status() -> dict[str, object]:
    return integration_status()


@router.post("/github/create-issue")
def create_github_issue(payload: IssueRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_issue(payload.title, payload.body)
    record_audit(
        action="integration_github_create_issue",
        route="/integrations/github/create-issue",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return {
        "ok": bool(result.get("ok")),
        "result": result,
        "message": "GitHub issue created." if result.get("ok") else "GitHub issue was not created.",
    }


@router.post("/codex/package-task")
def package_codex_task(payload: CodexPackageRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = CodexBridgeConnector().package_task(payload.instruction, repo=payload.repo)
    record_audit(
        action="integration_codex_package_task",
        route="/integrations/codex/package-task",
        success=bool(result.get("ok")),
        auth=context,
        warnings=["Codex package created; real Codex execution is not configured."],
        errors=[],
    )
    return result
