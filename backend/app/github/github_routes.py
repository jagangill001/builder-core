from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.audit.audit_log import record_audit
from app.auth.auth import AuthContext
from app.auth.dependencies import require_admin
from app.connectors.github import GitHubConnector

router = APIRouter(prefix="/github", tags=["github"])


class IssueRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    task_id: str = "manual"


class BranchRequest(BaseModel):
    branch_name: str = Field(min_length=1)
    base_branch: str = "main"
    task_id: str = "manual"


class FileRequest(BaseModel):
    path: str = Field(min_length=1)
    content: str
    message: str = Field(min_length=1)
    branch: str
    allow_main_branch: bool = False


class PullRequestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    head: str
    base: str = "main"


class PlanChangeRequest(BaseModel):
    task_id: str = "manual"
    title: str = Field(min_length=1, max_length=200)
    files_planned: list[str] = []


@router.get("/repo")
def repo_info() -> dict[str, object]:
    return GitHubConnector().get_repo_info()


@router.get("/commits")
def commits(limit: int = 10) -> dict[str, object]:
    return GitHubConnector().list_recent_commits(limit)


@router.post("/issues")
def create_issue(payload: IssueRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_issue(payload.title, payload.body)
    record_audit(
        action="github_create_issue",
        route="/github/issues",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/branch")
def create_branch(payload: BranchRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_branch(payload.branch_name, payload.base_branch)
    record_audit(
        action="github_create_branch",
        route="/github/branch",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/file")
def create_or_update_file(payload: FileRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_or_update_file(
        path=payload.path,
        content=payload.content,
        message=payload.message,
        branch=payload.branch,
        allow_main_branch=payload.allow_main_branch,
    )
    record_audit(
        action="github_create_or_update_file",
        route="/github/file",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/pull-request")
def open_pull_request(payload: PullRequestRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().open_pull_request(payload.title, payload.body, payload.head, payload.base)
    record_audit(
        action="github_open_pull_request",
        route="/github/pull-request",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/plan-change")
def plan_change(payload: PlanChangeRequest) -> dict[str, object]:
    return GitHubConnector().plan_change(
        task_id=payload.task_id,
        title=payload.title,
        files=payload.files_planned,
    )


@router.post("/create-branch")
def create_task_branch(payload: PlanChangeRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_branch_for_task(task_id=payload.task_id, title=payload.title)
    record_audit(
        action="github_create_task_branch",
        route="/github/create-branch",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/create-file-change")
def create_task_file_change(payload: FileRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().create_file_change(
        path=payload.path,
        content=payload.content,
        message=payload.message,
        branch=payload.branch,
        allow_main_branch=payload.allow_main_branch,
    )
    record_audit(
        action="github_create_file_change",
        route="/github/create-file-change",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result


@router.post("/open-pr")
def open_task_pr(payload: PullRequestRequest, context: AuthContext = Depends(require_admin)) -> dict[str, object]:
    result = GitHubConnector().open_pr(title=payload.title, body=payload.body, head=payload.head, base=payload.base)
    record_audit(
        action="github_open_pr",
        route="/github/open-pr",
        success=bool(result.get("ok")),
        auth=context,
        warnings=[str(result.get("warning"))] if result.get("warning") else [],
        errors=[str(result.get("error"))] if result.get("error") else [],
    )
    return result
