from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from app.database import SessionLocal
from app.legacy_models import CodexTaskRecord, Project
from app.services import project_service

DEFAULT_TRIGGER_MENTION = "@codex"
PULL_REQUEST_PATTERN = re.compile(r"https://github\.com/[^\s/]+/[^\s/]+/pull/\d+")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _bridge_repo() -> tuple[str, str]:
    return os.getenv("GITHUB_OWNER", "").strip(), os.getenv("GITHUB_REPO", "").strip()


def bridge_status() -> dict[str, Any]:
    owner, repo = _bridge_repo()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    missing: list[str] = []
    if not owner:
        missing.append("GITHUB_OWNER")
    if not repo:
        missing.append("GITHUB_REPO")
    if not token:
        missing.append("GITHUB_TOKEN")

    return {
        "enabled": not missing,
        "mode": "github-issue",
        "repository": f"{owner}/{repo}" if owner and repo else None,
        "trigger": DEFAULT_TRIGGER_MENTION,
        "missing": missing,
    }


def create_task_from_workflow(
    *,
    project_name: str,
    intent: str,
    user_message: str,
    plan: list[str],
    source_task_id: str | None = None,
) -> dict[str, Any]:
    clean_project_name = project_service.normalize_project_name(project_name)
    title = _build_issue_title(clean_project_name, user_message)

    db = SessionLocal()
    try:
        project = project_service.get_or_create_project(db, clean_project_name)
        task = CodexTaskRecord(
            task_id=uuid4().hex[:12],
            project_id=project.id,
            source_task_id=source_task_id,
            intent=intent,
            worker_mode="codex",
            status="queued",
            title=title,
            user_message=user_message.strip(),
            plan_json=json.dumps(plan),
            latest_summary="Queued for Codex bridge submission.",
            updated_at=_timestamp(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        status = bridge_status()
        if not status["enabled"]:
            task.status = "pending_setup"
            task.latest_summary = "Codex bridge is waiting for GitHub runtime configuration."
            task.last_error = "Missing runtime settings: " + ", ".join(status["missing"])
            task.updated_at = _timestamp()
            db.commit()
            db.refresh(task)
            return _serialize_task(task)

        try:
            issue = _create_issue(
                title=title,
                body=_build_issue_body(
                    project_name=clean_project_name,
                    intent=intent,
                    user_message=user_message,
                    plan=plan,
                    source_task_id=source_task_id,
                ),
            )
            task.status = "submitted"
            task.github_issue_number = issue["number"]
            task.github_issue_url = issue["html_url"]
            task.github_issue_state = issue["state"]
            task.latest_summary = "Submitted to GitHub for Codex pickup."
            task.last_error = None
        except CodexBridgeError as exc:
            task.status = "failed"
            task.last_error = str(exc)
            task.latest_summary = "Codex bridge could not open the GitHub issue."

        task.updated_at = _timestamp()
        db.commit()
        db.refresh(task)
        return _serialize_task(task)
    finally:
        db.close()


def get_task_status(task_id: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        task = db.query(CodexTaskRecord).filter(CodexTaskRecord.task_id == task_id).first()
        if task is None:
            return None
        _refresh_from_github(db, task)
        return _serialize_task(task)
    finally:
        db.close()


def list_task_statuses(project_name: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(CodexTaskRecord).order_by(CodexTaskRecord.id.desc())
        if project_name:
            clean_project_name = project_service.normalize_project_name(project_name)
            query = query.join(Project).filter(Project.name == clean_project_name)

        tasks = query.limit(limit).all()
        for task in tasks:
            _refresh_from_github(db, task)
        return [_serialize_task(task) for task in tasks]
    finally:
        db.close()


def _refresh_from_github(db, task: CodexTaskRecord) -> None:
    if not task.github_issue_number or not bridge_status()["enabled"]:
        return

    try:
        issue = _github_request("GET", f"/issues/{task.github_issue_number}")
        comments = _github_request("GET", f"/issues/{task.github_issue_number}/comments?per_page=5")
    except CodexBridgeError:
        return

    latest_body = ""
    if comments:
        latest_body = (comments[-1].get("body") or "").strip()

    task.github_issue_state = issue.get("state") or task.github_issue_state
    task.pull_request_url = _extract_pull_request_url(
        latest_body,
        issue.get("body", ""),
        task.pull_request_url or "",
    )
    task.latest_summary = _summarize_activity(latest_body or issue.get("body", ""))
    task.status = _resolve_task_status(task.github_issue_state, bool(comments), bool(task.pull_request_url))
    task.updated_at = _timestamp()
    db.commit()
    db.refresh(task)


def _resolve_task_status(issue_state: str | None, has_comments: bool, has_pull_request: bool) -> str:
    if issue_state == "closed":
        return "completed" if has_pull_request else "closed"
    if has_pull_request or has_comments:
        return "running"
    return "submitted"


def _build_issue_title(project_name: str, user_message: str) -> str:
    short_message = " ".join(user_message.strip().split())
    if len(short_message) > 80:
        short_message = short_message[:77].rstrip() + "..."
    return f"Builder Core Codex Task: {project_name} - {short_message}"


def _build_issue_body(
    *,
    project_name: str,
    intent: str,
    user_message: str,
    plan: list[str],
    source_task_id: str | None,
) -> str:
    plan_lines = "\n".join(f"{index}. {step}" for index, step in enumerate(plan, start=1)) or "1. Inspect the repo and choose the smallest safe implementation path."

    return (
        f"{DEFAULT_TRIGGER_MENTION}\n\n"
        "Builder Core submitted this coding task from the phone/cloud assistant flow.\n"
        "Please work from a branch or pull request first and do not push directly to `main`.\n\n"
        f"- Project: {project_name}\n"
        f"- Intent: {intent}\n"
        f"- Source task id: {source_task_id or 'n/a'}\n"
        "- Follow the repo root `AGENTS.md` and any nested agent rules.\n"
        "- Prefer fresh, repo-specific implementations.\n"
        "- Avoid recognizable third-party boilerplate.\n"
        "- Keep backend and frontend Cloud Run deployment working.\n\n"
        "Requested task:\n"
        f"{user_message.strip()}\n\n"
        "Planner outline:\n"
        f"{plan_lines}\n\n"
        "Success criteria:\n"
        "1. Keep the current branch/PR workflow intact.\n"
        "2. Add or update tests when behavior changes.\n"
        "3. Summarize what changed and any remaining risk in the PR.\n"
    )


def _create_issue(*, title: str, body: str) -> dict[str, Any]:
    payload = {
        "title": title,
        "body": body,
    }
    return _github_request("POST", "/issues", payload)


def _github_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    owner, repo = _bridge_repo()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not owner or not repo or not token:
        raise CodexBridgeError("GitHub bridge settings are incomplete.")

    url = f"https://api.github.com/repos/{owner}/{repo}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url=url, data=data, method=method)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("User-Agent", "builder-core-codex-bridge")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        request.add_header("Content-Type", "application/json")

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise CodexBridgeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise CodexBridgeError(f"Could not reach the GitHub API: {exc.reason}") from exc


def _extract_pull_request_url(*candidates: str) -> str | None:
    for candidate in candidates:
        match = PULL_REQUEST_PATTERN.search(candidate or "")
        if match:
            return match.group(0)
    return None


def _summarize_activity(text: str) -> str:
    clean_text = " ".join((text or "").strip().split())
    if not clean_text:
        return "Waiting for Codex activity in GitHub."
    if len(clean_text) <= 240:
        return clean_text
    return clean_text[:237].rstrip() + "..."


def _serialize_task(task: CodexTaskRecord) -> dict[str, Any]:
    plan = json.loads(task.plan_json or "[]")
    return {
        "task_id": task.task_id,
        "source_task_id": task.source_task_id,
        "project_name": task.project.name if task.project else None,
        "intent": task.intent,
        "worker_mode": task.worker_mode,
        "status": task.status,
        "title": task.title,
        "message": task.user_message,
        "plan": plan,
        "github_issue_number": task.github_issue_number,
        "github_issue_url": task.github_issue_url,
        "github_issue_state": task.github_issue_state,
        "pull_request_url": task.pull_request_url,
        "latest_summary": task.latest_summary,
        "last_error": task.last_error,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "next_action": _next_action(task),
    }


def _next_action(task: CodexTaskRecord) -> str:
    if task.status == "pending_setup":
        return "Add the GitHub bridge runtime settings to the backend service, then retry."
    if task.status == "failed":
        return "Review the bridge error, fix the GitHub settings, and submit the task again."
    if task.pull_request_url:
        return "Review the linked pull request, wait for checks, then merge to main to deploy."
    if task.github_issue_url:
        return "Open the GitHub issue and wait for @codex to respond or open a pull request."
    return "Wait for the bridge to submit this task to GitHub."


class CodexBridgeError(RuntimeError):
    pass
