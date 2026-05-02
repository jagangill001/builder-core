from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest


DEFAULT_GITHUB_OWNER = "jagangill001"
DEFAULT_GITHUB_REPO = "builder-core"
DEFAULT_GITHUB_BRANCH = "main"
DEFAULT_GITHUB_CHECKS_WORKFLOW = "Repo Checks"
DEFAULT_GITHUB_DEPLOY_WORKFLOW = "Deploy Cloud Run"
DEFAULT_BACKEND_URL = "https://builder-core-599596796788.us-central1.run.app"
DEFAULT_FRONTEND_URL = "https://builder-core-frontend-599596796788.us-central1.run.app"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BridgeService:
    def get_repo_config(self) -> dict[str, str]:
        owner = (os.environ.get("GITHUB_OWNER") or DEFAULT_GITHUB_OWNER).strip() or DEFAULT_GITHUB_OWNER
        repo = (
            os.environ.get("GITHUB_REPO")
            or f"{DEFAULT_GITHUB_OWNER}/{DEFAULT_GITHUB_REPO}"
        ).strip() or f"{DEFAULT_GITHUB_OWNER}/{DEFAULT_GITHUB_REPO}"
        branch = (
            os.environ.get("GITHUB_BRANCH")
            or os.environ.get("GITHUB_DEFAULT_BRANCH")
            or DEFAULT_GITHUB_BRANCH
        ).strip() or DEFAULT_GITHUB_BRANCH
        token = (os.environ.get("GITHUB_TOKEN") or "").strip()
        checks_workflow = (
            os.environ.get("GITHUB_CHECKS_WORKFLOW_NAME") or DEFAULT_GITHUB_CHECKS_WORKFLOW
        ).strip() or DEFAULT_GITHUB_CHECKS_WORKFLOW
        deploy_workflow = (
            os.environ.get("GITHUB_DEPLOY_WORKFLOW_NAME") or DEFAULT_GITHUB_DEPLOY_WORKFLOW
        ).strip() or DEFAULT_GITHUB_DEPLOY_WORKFLOW

        if "/" in repo:
            resolved_owner, resolved_repo = repo.split("/", 1)
        else:
            resolved_owner, resolved_repo = owner, repo

        return {
            "owner": resolved_owner,
            "repo": resolved_repo,
            "repo_label": f"{resolved_owner}/{resolved_repo}",
            "branch": branch,
            "token": token,
            "checks_workflow": checks_workflow,
            "deploy_workflow": deploy_workflow,
        }

    def get_public_urls(self) -> dict[str, str]:
        backend_url = (
            os.environ.get("BACKEND_URL")
            or os.environ.get("BACKEND_PUBLIC_URL")
            or DEFAULT_BACKEND_URL
        ).strip().rstrip("/")
        frontend_url = (
            os.environ.get("FRONTEND_URL")
            or os.environ.get("FRONTEND_PUBLIC_URL")
            or DEFAULT_FRONTEND_URL
        ).strip().rstrip("/")
        return {
            "backend": backend_url,
            "frontend": frontend_url,
        }

    def build_bridge_status_payload(self) -> dict[str, Any]:
        config = self.get_repo_config()
        urls = self.get_public_urls()
        codex_mode = (os.environ.get("CODEX_MODE") or "disabled").strip().lower() or "disabled"
        codex_api_key = (os.environ.get("CODEX_API_KEY") or "").strip()

        missing: list[str] = []
        notes: list[str] = []

        if not config["token"]:
            missing.append("GITHUB_TOKEN")

        if not config["repo_label"]:
            missing.append("GITHUB_REPO")

        if not config["branch"]:
            missing.append("GITHUB_BRANCH")

        if codex_mode == "disabled":
            notes.append("CODEX_MODE is disabled.")
        elif not codex_api_key:
            missing.append("CODEX_API_KEY")

        ready_for_repo_work = bool(config["token"] and codex_mode != "disabled" and codex_api_key)

        if missing:
            message = (
                "Backend is online, but GitHub/Codex bridge is not configured yet. "
                f"Add {', '.join(missing)} in Cloud Run environment variables."
            )
        elif codex_mode == "disabled":
            message = (
                "Backend is online, but real Codex execution is disabled. "
                "Enable CODEX_MODE and provide CODEX_API_KEY before expecting repo changes."
            )
        else:
            message = "GitHub and Codex bridge credentials are present, but repo execution still needs an explicit worker implementation."

        return {
            "ready_for_repo_work": ready_for_repo_work,
            "github_configured": bool(config["token"]),
            "codex_mode": codex_mode,
            "codex_configured": bool(codex_api_key),
            "missing": missing,
            "notes": notes,
            "message": message,
            "repo": config["repo_label"],
            "branch": config["branch"],
            "frontend_url": urls["frontend"],
            "backend_url": urls["backend"],
            "checked_at": utc_now_iso(),
        }

    def build_github_status_payload(self) -> dict[str, Any]:
        config = self.get_repo_config()

        if not config["token"]:
            return {
                "ok": False,
                "connected": False,
                "repo": config["repo_label"],
                "branch": config["branch"],
                "configured_with_token": False,
                "latest_commit": None,
                "checks_workflow": None,
                "deploy_workflow": None,
                "summary": "GitHub status not connected",
                "next_step": "Add GITHUB_TOKEN in Cloud Run environment variables to enable real GitHub tracking.",
                "error": "GITHUB_TOKEN is missing.",
                "updated_at": utc_now_iso(),
            }

        try:
            latest_commit = self._fetch_latest_commit(config)
            checks_workflow, deploy_workflow = self._fetch_workflow_runs(config)
        except Exception as exc:  # pragma: no cover - network or API failure path
            return {
                "ok": False,
                "connected": False,
                "repo": config["repo_label"],
                "branch": config["branch"],
                "configured_with_token": True,
                "latest_commit": None,
                "checks_workflow": None,
                "deploy_workflow": None,
                "summary": "GitHub status tracking could not reach the GitHub API.",
                "next_step": "Check GitHub token permissions and network access from the backend runtime.",
                "error": str(exc),
                "updated_at": utc_now_iso(),
            }

        return {
            "ok": True,
            "connected": True,
            "repo": config["repo_label"],
            "branch": config["branch"],
            "configured_with_token": True,
            "latest_commit": latest_commit,
            "checks_workflow": checks_workflow,
            "deploy_workflow": deploy_workflow,
            "summary": self._build_github_summary(checks_workflow, deploy_workflow),
            "next_step": self._build_github_next_step(checks_workflow, deploy_workflow),
            "updated_at": utc_now_iso(),
        }

    def build_deploy_status_payload(self) -> dict[str, Any]:
        github_status = self.build_github_status_payload()
        urls = self.get_public_urls()
        backend_check = self.check_public_service(f"{urls['backend']}/system/status", expect_status_json=True)
        frontend_check = self.check_public_service(urls["frontend"])
        deploy_workflow = github_status.get("deploy_workflow") if isinstance(github_status, dict) else None

        deploy_running = self._workflow_running(deploy_workflow)
        deploy_succeeded = self._workflow_succeeded(deploy_workflow)
        backend_healthy = bool(backend_check.get("healthy"))
        frontend_reachable = frontend_check.get("reachable")
        ready_to_refresh = bool(deploy_succeeded and backend_healthy and frontend_reachable)

        summary = github_status.get("summary") if isinstance(github_status, dict) else "Deploy status unavailable."
        next_step = github_status.get("next_step") if isinstance(github_status, dict) else "Review deployment settings."

        if deploy_running:
            summary = "GitHub Actions running"
            next_step = "Wait for the deploy workflow to finish before refreshing the app."
        elif deploy_succeeded and backend_healthy and frontend_reachable:
            summary = "Cloud Run is live"
            next_step = "Ready to refresh"
        elif deploy_succeeded and not backend_healthy:
            summary = "Deploy succeeded, but backend health still needs attention."
            next_step = "Check the backend /system/status response and Cloud Run logs."
        elif deploy_succeeded and not frontend_reachable:
            summary = "Deploy succeeded, but the frontend URL is not reachable yet."
            next_step = "Wait for the frontend revision to go live, then refresh the app."

        return {
            **github_status,
            "deploy_running": deploy_running,
            "deploy_succeeded": deploy_succeeded,
            "backend_healthy": backend_healthy,
            "frontend_reachable": frontend_reachable,
            "ready_to_refresh": ready_to_refresh,
            "backend_check": backend_check,
            "frontend_check": frontend_check,
            "summary": summary,
            "next_step": next_step,
            "updated_at": utc_now_iso(),
        }

    def check_public_service(self, url: str, expect_status_json: bool = False) -> dict[str, Any]:
        if not url:
            return {
                "url": url,
                "reachable": False,
                "healthy": False,
                "status_code": None,
                "error": "URL not configured.",
            }

        request = urlrequest.Request(url, headers={"User-Agent": "builder-core-bridge"})
        try:
            with urlrequest.urlopen(request, timeout=8) as response:
                status_code = getattr(response, "status", response.getcode())
                body = response.read().decode("utf-8", errors="replace")
                reachable = 200 <= status_code < 400
                payload = {
                    "url": url,
                    "reachable": reachable,
                    "healthy": reachable,
                    "status_code": status_code,
                }

                if expect_status_json:
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        payload["healthy"] = False
                        payload["error"] = "Invalid JSON response."
                        return payload

                    reported_status = str(data.get("status", ""))
                    payload["reported_status"] = reported_status
                    payload["healthy"] = reachable and reported_status == "ok"

                return payload
        except urlerror.HTTPError as exc:
            return {
                "url": url,
                "reachable": False,
                "healthy": False,
                "status_code": exc.code,
                "error": f"HTTP {exc.code}",
            }
        except Exception as exc:  # pragma: no cover - network failure path
            return {
                "url": url,
                "reachable": False,
                "healthy": False,
                "status_code": None,
                "error": str(exc),
            }

    def _fetch_latest_commit(self, config: dict[str, str]) -> dict[str, Any]:
        encoded_branch = urlparse.quote(config["branch"], safe="")
        url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/commits/{encoded_branch}"
        payload = self._request_json(url, config["token"])
        sha = str(payload.get("sha", ""))
        commit = payload.get("commit", {}) if isinstance(payload.get("commit"), dict) else {}
        author = commit.get("author", {}) if isinstance(commit.get("author"), dict) else {}
        return {
            "sha": sha,
            "short_sha": sha[:7] if sha else None,
            "message": commit.get("message"),
            "url": payload.get("html_url"),
            "author": author.get("name"),
            "timestamp": author.get("date"),
        }

    def _fetch_workflow_runs(self, config: dict[str, str]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        encoded_branch = urlparse.quote(config["branch"], safe="")
        url = (
            f"https://api.github.com/repos/{config['owner']}/{config['repo']}/actions/runs"
            f"?per_page=20&branch={encoded_branch}"
        )
        payload = self._request_json(url, config["token"])
        workflow_runs = payload.get("workflow_runs", [])
        if not isinstance(workflow_runs, list):
            workflow_runs = []

        checks = self._match_workflow(workflow_runs, config["checks_workflow"])
        deploy = self._match_workflow(workflow_runs, config["deploy_workflow"])
        return checks, deploy

    def _match_workflow(self, runs: list[dict[str, Any]], workflow_name: str) -> dict[str, Any] | None:
        for run in runs:
            if str(run.get("name", "")) != workflow_name:
                continue

            sha = str(run.get("head_sha", ""))
            return {
                "name": run.get("name"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "url": run.get("html_url"),
                "event": run.get("event"),
                "branch": run.get("head_branch"),
                "sha": sha,
                "short_sha": sha[:7] if sha else None,
                "updated_at": run.get("updated_at"),
            }

        return None

    def _request_json(self, url: str, token: str) -> dict[str, Any]:
        headers = {
            "User-Agent": "builder-core-bridge",
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
        }
        request = urlrequest.Request(url, headers=headers)
        with urlrequest.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
        return json.loads(body)

    def _workflow_running(self, workflow: dict[str, Any] | None) -> bool:
        if not workflow:
            return False
        return str(workflow.get("status")) in {"queued", "in_progress", "waiting"}

    def _workflow_succeeded(self, workflow: dict[str, Any] | None) -> bool:
        if not workflow:
            return False
        return str(workflow.get("conclusion")) == "success"

    def _build_github_summary(self, checks: dict[str, Any] | None, deploy: dict[str, Any] | None) -> str:
        if self._workflow_running(deploy):
            return "GitHub Actions running"

        if self._workflow_succeeded(deploy):
            return "Deploy succeeded"

        if self._workflow_running(checks):
            return "Repo Checks running"

        if checks and str(checks.get("conclusion")) == "failure":
            return "Repo Checks failed"

        if deploy and str(deploy.get("conclusion")) == "failure":
            return "Deploy workflow failed"

        return "GitHub status connected"

    def _build_github_next_step(self, checks: dict[str, Any] | None, deploy: dict[str, Any] | None) -> str:
        if self._workflow_running(deploy):
            return "Wait for the deploy workflow to finish."

        if self._workflow_succeeded(deploy):
            return "Check whether Cloud Run is live and refresh the app when it is healthy."

        if checks and str(checks.get("conclusion")) == "failure":
            return "Open the failing Repo Checks workflow and fix the blocking issue."

        if deploy and str(deploy.get("conclusion")) == "failure":
            return "Open the deploy workflow logs and fix the deployment error before retrying."

        return "Submit a task or wait for the next GitHub workflow update."
