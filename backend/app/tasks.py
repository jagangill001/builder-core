from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

try:
    from app.bridge import BridgeService
    from app.learning import LearningService
    from app.storage import ProjectStorageService
    from app.services import AutomationTaskService
except ImportError:
    from bridge import BridgeService
    from learning import LearningService
    from services import AutomationTaskService
    from storage import ProjectStorageService


TASK_STAGES = [
    "received",
    "planning",
    "bridge_check",
    "codex_working",
    "testing",
    "deploy_check",
    "summary",
    "completed",
    "failed",
]

STAGE_PROGRESS = {
    "received": 1,
    "planning": 10,
    "bridge_check": 25,
    "codex_working": 45,
    "testing": 65,
    "deploy_check": 80,
    "summary": 90,
    "completed": 100,
}

MUTATING_KEYWORDS = (
    "build",
    "fix",
    "upgrade",
    "create",
    "add",
    "change",
    "modify",
    "delete",
    "remove",
    "refactor",
    "repair",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackendTaskRunner:
    def __init__(
        self,
        task_service: AutomationTaskService,
        project_storage: ProjectStorageService,
        learning_service: LearningService,
        bridge_service: BridgeService,
        repo_root: Path,
        route_provider: Callable[[], set[str]],
    ) -> None:
        self.task_service = task_service
        self.project_storage = project_storage
        self.learning_service = learning_service
        self.bridge_service = bridge_service
        self.repo_root = repo_root
        self.route_provider = route_provider
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def create_task(self, command: str, project_name: str = "Default Project") -> dict[str, Any]:
        item = self.task_service.create_task(
            command=command,
            project_name=project_name,
            status="received",
            current_stage="received",
            progress=STAGE_PROGRESS["received"],
            logs=["Task received by Builder Core."],
            errors=[],
            summary=None,
            bridge_status=self.bridge_service.build_bridge_status_payload(),
            files_changed=[],
        )
        self._start_background_run(item["id"])
        return item

    def manual_advance(self, task_id: str) -> Optional[dict[str, Any]]:
        task = self.task_service.get_task(task_id)
        if task is None:
            return None

        current_stage = str(task.get("stage") or task.get("current_stage") or "received")
        if current_stage in {"completed", "failed"}:
            return task

        next_stage = self._next_stage(current_stage)
        if next_stage is None:
            next_stage = "summary"

        updates = self._merge_stage_update(
            task,
            stage=next_stage,
            progress=STAGE_PROGRESS.get(next_stage, task.get("progress", 0)),
            status="running" if next_stage not in {"completed", "failed"} else next_stage,
            log_message="Manual debug advance requested from the frontend.",
        )
        return self.task_service.update_task(task_id, updates)

    def _start_background_run(self, task_id: str) -> None:
        thread = threading.Thread(target=self._run_task, args=(task_id,), daemon=True)
        with self._lock:
            self._threads[task_id] = thread
        thread.start()

    def _run_task(self, task_id: str) -> None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return

        command = str(task.get("command", "")).strip()
        project_name = str(task.get("project_name", "Default Project"))
        stages_completed: list[str] = ["received"]
        files_changed: list[str] = []
        bridge_status: dict[str, Any] = {}
        testing_result: dict[str, Any] = {}
        deploy_result: dict[str, Any] = {}
        final_status = "completed"
        summary_note = ""

        try:
            self._transition(
                task_id,
                "planning",
                "running",
                "Planning started for the new command.",
            )
            plan = self._build_plan(command)
            for step in plan:
                self._append_log(task_id, f"Plan step: {step}")
            stages_completed.append("planning")

            self._transition(
                task_id,
                "bridge_check",
                "running",
                "Checking GitHub and Codex bridge configuration.",
            )
            bridge_status = self.bridge_service.build_bridge_status_payload()
            self.task_service.update_task(
                task_id,
                {
                    "bridge_status": bridge_status,
                    "config_problems": bridge_status.get("missing", []),
                },
            )
            self.project_storage.save_latest_bridge_status(bridge_status)
            self.project_storage.save_known_environment_problems(
                list(bridge_status.get("missing", []))
            )
            self._append_log(task_id, bridge_status.get("message", "Bridge status checked."))
            stages_completed.append("bridge_check")

            repo_change_expected = self._command_requires_repo_change(command)
            bridge_ready = bool(bridge_status.get("ready_for_repo_work"))
            codex_mode = str(bridge_status.get("codex_mode", "disabled"))

            self._transition(
                task_id,
                "codex_working",
                "running",
                "Checking whether real repo work can start.",
            )
            if repo_change_expected:
                if not bridge_ready:
                    final_status = "failed"
                    summary_note = "No real repo changes were made because bridge credentials are missing."
                    self._append_error(task_id, bridge_status.get("message", "Bridge is not configured."))
                    self._append_log(task_id, summary_note)
                elif codex_mode == "disabled":
                    final_status = "failed"
                    summary_note = (
                        "No real repo changes were made because CODEX_MODE is disabled."
                    )
                    self._append_error(task_id, summary_note)
                else:
                    final_status = "failed"
                    summary_note = (
                        "Bridge credentials were found, but no real Codex execution client is implemented yet."
                    )
                    self._append_error(task_id, summary_note)
                    self._append_log(task_id, summary_note)
            else:
                self._append_log(
                    task_id,
                    "This command looks informational, so Builder Core did not need to change the repo.",
                )
            stages_completed.append("codex_working")

            self._transition(
                task_id,
                "testing",
                "running",
                "Running backend-safe validation checks.",
            )
            testing_result = self._run_testing_checks(task_id)
            self.task_service.update_task(task_id, {"testing_result": testing_result})
            stages_completed.append("testing")

            self._transition(
                task_id,
                "deploy_check",
                "running",
                "Checking GitHub workflow status and live service health.",
            )
            deploy_result = self.bridge_service.build_deploy_status_payload()
            self.task_service.update_task(
                task_id,
                {
                    "deploy_result": deploy_result,
                    "github_commit": (
                        deploy_result.get("latest_commit") or {}
                    ).get("short_sha"),
                    "workflow_status": deploy_result.get("summary"),
                },
            )
            self._append_deploy_logs(task_id, deploy_result)
            stages_completed.append("deploy_check")

            self._transition(
                task_id,
                "summary",
                "running",
                "Preparing the final task summary.",
            )
            summary = self._build_summary(
                task_id=task_id,
                command=command,
                final_status=final_status,
                project_name=project_name,
                stages_completed=stages_completed,
                bridge_status=bridge_status,
                testing_result=testing_result,
                deploy_result=deploy_result,
                files_changed=files_changed,
                summary_note=summary_note,
            )
            self.task_service.update_task(task_id, {"summary": summary})
            self.project_storage.save_latest_summary(summary)
            self.project_storage.save_project_memory(
                {
                    "type": "task_summary",
                    "task_id": task_id,
                    "command": command,
                    "status": final_status,
                    "summary": summary.get("message"),
                }
            )

            final_task = self.task_service.get_task(task_id) or {}
            final_task["summary"] = summary
            final_task["status"] = final_status
            self.learning_service.record_task_lesson(final_task)

            if final_status == "completed":
                self._finalize_task(task_id, "completed", STAGE_PROGRESS["completed"], "Task completed.")
            else:
                failed_progress = summary.get("final_progress", STAGE_PROGRESS["summary"])
                self._finalize_task(task_id, "failed", failed_progress, "Task finished with a blocking issue.")
        except Exception as exc:
            self._append_error(task_id, f"Internal task runner exception: {exc}")
            summary = self._build_summary(
                task_id=task_id,
                command=command,
                final_status="failed",
                project_name=project_name,
                stages_completed=stages_completed,
                bridge_status=bridge_status,
                testing_result=testing_result,
                deploy_result=deploy_result,
                files_changed=files_changed,
                summary_note="Builder Core stopped because of an internal backend exception.",
            )
            self.task_service.update_task(task_id, {"summary": summary})
            self.project_storage.save_latest_summary(summary)
            self.learning_service.record_task_lesson(self.task_service.get_task(task_id) or {"summary": summary})
            self._finalize_task(task_id, "failed", STAGE_PROGRESS["summary"], "Task failed.")
        finally:
            with self._lock:
                self._threads.pop(task_id, None)

    def _run_testing_checks(self, task_id: str) -> dict[str, Any]:
        route_paths = self.route_provider()
        required_routes = {
            "/system/status",
            "/tasks",
            "/tasks/{task_id}",
            "/memory",
            "/learning",
        }
        missing_routes = sorted(required_routes - route_paths)
        task_exists = self.task_service.get_task(task_id) is not None
        memory_health = self.project_storage.health_check()
        checks: list[str] = []

        if missing_routes:
            checks.append(f"Missing required routes: {', '.join(missing_routes)}")
            self._append_error(task_id, checks[-1])
        else:
            checks.append("Verified required backend routes exist.")
            self._append_log(task_id, checks[-1])

        if task_exists:
            checks.append("Verified the task record can be saved and loaded.")
            self._append_log(task_id, checks[-1])
        else:
            checks.append("Task storage check failed because the task record could not be reloaded.")
            self._append_error(task_id, checks[-1])

        if memory_health.get("ok"):
            checks.append("Verified project memory storage is writable.")
            self._append_log(task_id, checks[-1])
        else:
            checks.append("Project memory storage health check failed.")
            self._append_error(task_id, checks[-1])

        return {
            "checked_at": utc_now_iso(),
            "ok": not missing_routes and task_exists and bool(memory_health.get("ok")),
            "checks": checks,
            "missing_routes": missing_routes,
            "memory_health": memory_health,
        }

    def _append_deploy_logs(self, task_id: str, deploy_result: dict[str, Any]) -> None:
        summary = str(deploy_result.get("summary", "Deploy status checked."))
        next_step = str(deploy_result.get("next_step", "Review deployment status."))
        self._append_log(task_id, summary)
        self._append_log(task_id, next_step)

        backend_check = deploy_result.get("backend_check")
        if isinstance(backend_check, dict):
            backend_state = "healthy" if backend_check.get("healthy") else "not healthy"
            self._append_log(
                task_id,
                f"Backend health check: {backend_state} ({backend_check.get('url')}).",
            )

        frontend_check = deploy_result.get("frontend_check")
        if isinstance(frontend_check, dict):
            frontend_state = "reachable" if frontend_check.get("reachable") else "not reachable"
            self._append_log(
                task_id,
                f"Frontend reachability check: {frontend_state} ({frontend_check.get('url')}).",
            )

    def _build_summary(
        self,
        *,
        task_id: str,
        command: str,
        final_status: str,
        project_name: str,
        stages_completed: list[str],
        bridge_status: dict[str, Any],
        testing_result: dict[str, Any],
        deploy_result: dict[str, Any],
        files_changed: list[str],
        summary_note: str,
    ) -> dict[str, Any]:
        task = self.task_service.get_task(task_id) or {}
        logs = task.get("logs") if isinstance(task.get("logs"), list) else []
        errors = task.get("errors") if isinstance(task.get("errors"), list) else []
        manual_setup = self._build_manual_setup(final_status, bridge_status, deploy_result)
        what_completed = self._build_completed_items(stages_completed, testing_result, deploy_result)
        next_step = self._build_next_step(final_status, bridge_status, deploy_result)

        message = summary_note
        if not message:
            if final_status == "completed":
                message = "Builder Core completed the task lifecycle and recorded the summary."
            else:
                message = "Builder Core reached the summary stage, but the task still needs manual setup."

        return {
            "task_id": task_id,
            "original_command": command,
            "project_name": project_name,
            "final_status": final_status,
            "stages_completed": stages_completed,
            "files_changed": files_changed,
            "folder_used": str(self.repo_root),
            "backend_logs": logs,
            "errors": errors,
            "what_completed": what_completed,
            "what_still_needs_manual_setup": manual_setup,
            "next_recommended_step": next_step,
            "bridge_status": bridge_status,
            "testing_result": testing_result,
            "deploy_result": deploy_result,
            "message": message,
            "final_progress": STAGE_PROGRESS["summary"] if final_status == "failed" else STAGE_PROGRESS["completed"],
            "created_at": task.get("created_at"),
            "updated_at": utc_now_iso(),
        }

    def _build_manual_setup(
        self,
        final_status: str,
        bridge_status: dict[str, Any],
        deploy_result: dict[str, Any],
    ) -> list[str]:
        manual_setup: list[str] = []
        if final_status != "completed":
            missing = bridge_status.get("missing", [])
            if isinstance(missing, list) and missing:
                manual_setup.append(
                    "Add the missing bridge environment variables: " + ", ".join(missing)
                )
            if str(bridge_status.get("codex_mode")) == "disabled":
                manual_setup.append("Enable CODEX_MODE before expecting real Codex work.")

        if not deploy_result.get("connected"):
            manual_setup.append("Connect GITHUB_TOKEN so Builder Core can read GitHub workflow status.")

        if not deploy_result.get("backend_healthy"):
            manual_setup.append("Check the backend /system/status endpoint and Cloud Run logs.")

        if deploy_result.get("frontend_reachable") is False:
            manual_setup.append("Verify the frontend Cloud Run URL is live before refreshing the app.")

        if not manual_setup:
            manual_setup.append("No additional manual setup is required for this task summary.")

        return manual_setup

    def _build_completed_items(
        self,
        stages_completed: list[str],
        testing_result: dict[str, Any],
        deploy_result: dict[str, Any],
    ) -> list[str]:
        items = [f"Reached stage: {stage}" for stage in stages_completed]
        if testing_result.get("ok"):
            items.append("Completed backend-safe route and storage checks.")
        if deploy_result.get("connected"):
            items.append("Fetched live GitHub workflow status from the backend.")
        if deploy_result.get("backend_healthy"):
            items.append("Verified the backend /system/status endpoint is healthy.")
        if deploy_result.get("frontend_reachable"):
            items.append("Verified the frontend URL is reachable.")
        return items

    def _build_next_step(
        self,
        final_status: str,
        bridge_status: dict[str, Any],
        deploy_result: dict[str, Any],
    ) -> str:
        if final_status == "completed":
            return "Submit the next Builder Core command or review the saved lesson for follow-up work."

        if not bridge_status.get("github_configured"):
            return "Add GITHUB_TOKEN in Cloud Run environment variables and run the task again."

        if str(bridge_status.get("codex_mode")) == "disabled":
            return "Enable CODEX_MODE and add CODEX_API_KEY before retrying a repo-changing task."

        if deploy_result.get("connected") is False:
            return "Reconnect GitHub status tracking so Builder Core can see real workflow progress."

        return "Review the saved errors, finish the manual setup items, and retry the task."

    def _transition(self, task_id: str, stage: str, status: str, log_message: str) -> None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return

        updates = self._merge_stage_update(
            task,
            stage=stage,
            progress=STAGE_PROGRESS.get(stage, task.get("progress", 0)),
            status=status,
            log_message=log_message,
        )
        self.task_service.update_task(task_id, updates)

    def _finalize_task(self, task_id: str, stage: str, progress: int, log_message: str) -> None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return

        updates = self._merge_stage_update(
            task,
            stage=stage,
            progress=progress,
            status=stage,
            log_message=log_message,
        )
        self.task_service.update_task(task_id, updates)

    def _append_log(self, task_id: str, message: str) -> None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return

        logs = list(task.get("logs") or [])
        logs.append(message)
        self.task_service.update_task(task_id, {"logs": logs})

    def _append_error(self, task_id: str, message: str) -> None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return

        errors = list(task.get("errors") or [])
        errors.append(message)
        self.task_service.update_task(task_id, {"errors": errors})

    def _merge_stage_update(
        self,
        task: dict[str, Any],
        *,
        stage: str,
        progress: int,
        status: str,
        log_message: str,
    ) -> dict[str, Any]:
        stage_history = list(task.get("stage_history") or [])
        stage_history.append(
            {
                "stage": stage,
                "status": status,
                "progress": progress,
                "timestamp": utc_now_iso(),
                "message": log_message,
            }
        )
        logs = list(task.get("logs") or [])
        logs.append(log_message)
        return {
            "stage": stage,
            "current_stage": stage,
            "progress": progress,
            "status": status,
            "stage_history": stage_history,
            "logs": logs,
        }

    def _build_plan(self, command: str) -> list[str]:
        return [
            "Understand the command and identify whether it needs real repo changes.",
            "Check bridge configuration before attempting any GitHub or Codex work.",
            "Run backend-safe checks and record honest results.",
            "Save a final summary, memory entry, and learning lesson.",
        ]

    def _command_requires_repo_change(self, command: str) -> bool:
        text = command.lower()
        return any(keyword in text for keyword in MUTATING_KEYWORDS)

    def _next_stage(self, current_stage: str) -> Optional[str]:
        try:
            index = TASK_STAGES.index(current_stage)
        except ValueError:
            return None

        for next_stage in TASK_STAGES[index + 1 :]:
            if next_stage not in {"failed"}:
                return next_stage

        return None
