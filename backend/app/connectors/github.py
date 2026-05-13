from __future__ import annotations

import base64
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.connectors.base import ConnectorStatus, env_configured, missing_env_vars


class GitHubConnector:
    name = "github"
    required_env_vars = ["GITHUB_TOKEN", "GITHUB_REPO_OWNER", "GITHUB_REPO_NAME"]

    def status(self) -> ConnectorStatus:
        configured = env_configured(*self.required_env_vars)
        missing = missing_env_vars(*self.required_env_vars)
        return ConnectorStatus(
            name=self.name,
            enabled=configured,
            configured=configured,
            required_env_vars=self.required_env_vars,
            capabilities=[
                "get_repo_info",
                "list_recent_commits",
                "create_issue",
                "create_branch",
                "read_file",
                "create_or_update_file",
                "open_pull_request",
                "list_recent_pull_requests",
                "list_recent_workflow_runs",
            ],
            health="ready" if configured else "not_configured",
            last_error=None if configured else f"Missing env vars: {', '.join(missing)}",
            admin_required=True,
            provider="github",
            is_real_execution=configured and not self.dry_run_enabled(),
        )

    def get_repo_info(self) -> dict[str, Any]:
        return self._request("GET", "")

    def list_recent_commits(self, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", f"/commits?per_page={max(1, min(limit, 30))}")

    def list_files(self, path: str = "") -> dict[str, Any]:
        encoded_path = quote(path.strip("/"))
        suffix = f"/contents/{encoded_path}" if encoded_path else "/contents"
        return self._request("GET", suffix)

    def read_file(self, path: str, ref: str | None = None) -> dict[str, Any]:
        suffix = f"/contents/{quote(path.strip('/'))}"
        if ref:
            suffix += f"?ref={quote(ref)}"
        result = self._request("GET", suffix)
        if not result.get("ok") or not isinstance(result.get("data"), dict):
            return result
        data = result["data"]
        content = data.get("content", "")
        if data.get("encoding") == "base64" and content:
            try:
                data["decoded_content"] = base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                data["decoded_content"] = ""
        return result

    def create_issue(self, title: str, body: str) -> dict[str, Any]:
        if self.dry_run_enabled():
            return self._planned("create_issue", branch=None, files_planned=[], payload={"title": title, "body": body})
        return self._request("POST", "/issues", {"title": title, "body": body})

    def create_branch(self, branch_name: str, base_branch: str = "main") -> dict[str, Any]:
        if self.dry_run_enabled():
            return self._planned("create_branch", branch=branch_name, files_planned=[], payload={"base_branch": base_branch})
        base_ref = self._request("GET", f"/git/ref/heads/{quote(base_branch)}")
        if not base_ref.get("ok"):
            return base_ref
        try:
            sha = base_ref["data"]["object"]["sha"]
        except Exception:
            return {"ok": False, "error": "Could not read base branch SHA from GitHub response."}
        return self._request("POST", "/git/refs", {"ref": f"refs/heads/{branch_name}", "sha": sha})

    def create_or_update_file(
        self,
        *,
        path: str,
        content: str,
        message: str,
        branch: str,
        allow_main_branch: bool = False,
    ) -> dict[str, Any]:
        if branch in {"main", "master"} and not allow_main_branch:
            return {
                "ok": False,
                "action": "create_or_update_file",
                "dry_run": self.dry_run_enabled(),
                "branch": branch,
                "files_planned": [path],
                "warning": "Direct main/master branch file writes are blocked by default. Use a task branch.",
            }
        if self.dry_run_enabled():
            return self._planned("create_or_update_file", branch=branch, files_planned=[path], payload={"message": message})
        encoded_path = quote(path.strip("/"))
        existing = self._request("GET", f"/contents/{encoded_path}?ref={quote(branch)}")
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if existing.get("ok") and isinstance(existing.get("data"), dict):
            sha = existing["data"].get("sha")
            if sha:
                payload["sha"] = sha
        return self._request("PUT", f"/contents/{encoded_path}", payload)

    def open_pull_request(self, title: str, body: str, head: str, base: str = "main") -> dict[str, Any]:
        if self.dry_run_enabled():
            return self._planned("open_pull_request", branch=head, files_planned=[], payload={"title": title, "base": base})
        return self._request("POST", "/pulls", {"title": title, "body": body, "head": head, "base": base})

    def dry_run_enabled(self) -> bool:
        return os.getenv("GITHUB_DRY_RUN", "false").strip().lower() in {"1", "true", "yes"}

    def branch_name_for_task(self, task_id: str, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "change"
        safe_task = re.sub(r"[^a-zA-Z0-9_-]+", "-", task_id).strip("-")[:32] or "manual"
        return f"builder-core/task-{safe_task}-{slug}"

    def plan_change(self, *, task_id: str, title: str, files: list[str]) -> dict[str, Any]:
        branch = self.branch_name_for_task(task_id, title)
        return {
            "ok": True,
            "action": "plan_change",
            "dry_run": True,
            "branch": branch,
            "files_planned": files,
            "github_url": None,
            "warning": "Planning only. No GitHub network request was made.",
        }

    def create_branch_for_task(self, *, task_id: str, title: str, base_branch: str = "main") -> dict[str, Any]:
        branch = self.branch_name_for_task(task_id, title)
        result = self.create_branch(branch, base_branch=base_branch)
        return self._with_write_fields(result, action="create_branch", branch=branch, files_planned=[])

    def create_file_change(self, *, path: str, content: str, message: str, branch: str, allow_main_branch: bool = False) -> dict[str, Any]:
        result = self.create_or_update_file(
            path=path,
            content=content,
            message=message,
            branch=branch,
            allow_main_branch=allow_main_branch,
        )
        return self._with_write_fields(result, action="create_file_change", branch=branch, files_planned=[path])

    def open_pr(self, *, title: str, body: str, head: str, base: str = "main") -> dict[str, Any]:
        result = self.open_pull_request(title, body, head, base)
        return self._with_write_fields(result, action="open_pr", branch=head, files_planned=[])

    def list_recent_pull_requests(self, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", f"/pulls?state=all&per_page={max(1, min(limit, 30))}")

    def list_recent_workflow_runs(self, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", f"/actions/runs?per_page={max(1, min(limit, 30))}")

    def _planned(self, action: str, branch: str | None, files_planned: list[str], payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "action": action,
            "dry_run": True,
            "branch": branch,
            "files_planned": files_planned,
            "github_url": None,
            "planned_payload": payload,
            "warning": "GITHUB_DRY_RUN is enabled. No GitHub write request was made.",
        }

    def _with_write_fields(self, result: dict[str, Any], *, action: str, branch: str | None, files_planned: list[str]) -> dict[str, Any]:
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        output = dict(result)
        output.setdefault("action", action)
        output.setdefault("dry_run", self.dry_run_enabled())
        output.setdefault("branch", branch)
        output.setdefault("files_planned", files_planned)
        output.setdefault("github_url", data.get("html_url") if isinstance(data, dict) else None)
        return output

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        status = self.status()
        if not status.configured:
            return {
                "ok": False,
                "error": "GitHub connector not configured.",
                "missing": missing_env_vars(*self.required_env_vars),
            }

        owner = os.getenv("GITHUB_REPO_OWNER", "").strip()
        repo = os.getenv("GITHUB_REPO_NAME", "").strip()
        token = os.getenv("GITHUB_TOKEN", "").strip()
        suffix = path if path.startswith("/") or path == "" else f"/{path}"
        url = f"https://api.github.com/repos/{owner}/{repo}{suffix}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url=url, data=data, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("User-Agent", "builder-core")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
                return {"ok": True, "data": json.loads(body) if body else {}}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return {"ok": False, "error": f"GitHub API returned HTTP {exc.code}.", "detail": detail}
        except URLError as exc:
            return {"ok": False, "error": f"Could not reach GitHub API: {exc.reason}"}
