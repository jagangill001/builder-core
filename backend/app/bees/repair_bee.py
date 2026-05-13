from __future__ import annotations

from app.core.context import WorkflowState
from app.database import SessionLocal
from app.memory import repair_memory
from app.legacy_models import Project
from app.services import builder_service, project_service


class RepairBee:
    name = "repair_bee"

    def run(self, state: WorkflowState) -> str:
        if not state.plan_data.get("build_triggered"):
            note = "Skipped repair because no build context was active."
            state.add_trace(self.name, note)
            return note

        if state.repair_attempts >= state.max_repair_attempts:
            note = f"Stopped auto-repair after {state.repair_attempts} attempt(s)."
            state.add_trace(self.name, note)
            return note

        error_text = self._error_text(state)
        probable_cause = self._classify_issue(error_text)
        prior_success = self._recent_success(state.project_name, probable_cause)
        files_changed, fix_applied = self._apply_fix(state, probable_cause)

        if not fix_applied:
            attempt = {
                "attempt": state.repair_attempts,
                "error_text": error_text,
                "probable_cause": probable_cause,
                "fix_applied": "No automatic fix applied.",
                "files_changed": [],
                "attempted_fix": False,
                "success": False,
                "recorded": True,
            }
            state.repair_history.append(attempt)
            self._persist_case(state.project_name, attempt)
            note = f"Diagnosed {probable_cause}, but no safe automatic repair was available."
            state.add_trace(self.name, note)
            return note

        state.repair_attempts += 1
        attempt = {
            "attempt": state.repair_attempts,
            "error_text": error_text,
            "probable_cause": probable_cause,
            "fix_applied": fix_applied,
            "files_changed": files_changed,
            "attempted_fix": True,
            "success": None,
            "recorded": False,
        }
        if prior_success:
            attempt["reference_fix"] = prior_success["fix_applied"]

        state.repair_history.append(attempt)
        state.files_changed = list(dict.fromkeys(state.files_changed + files_changed))

        note = (
            f"Repair attempt {state.repair_attempts} targeted {probable_cause} "
            f"and changed {len(files_changed)} file(s)."
        )
        if prior_success:
            note += " Reused a previously successful fix pattern."
        state.add_trace(self.name, note)
        return note

    def record_result(self, state: WorkflowState) -> str | None:
        pending = next(
            (
                attempt
                for attempt in reversed(state.repair_history)
                if attempt.get("attempted_fix") and not attempt.get("recorded")
            ),
            None,
        )
        if pending is None:
            return None

        pending["success"] = state.test_result.get("status") == "success"
        pending["recorded"] = True
        self._persist_case(state.project_name, pending)

        note = (
            f"Recorded repair attempt {pending['attempt']} as "
            f"{'successful' if pending['success'] else 'unsuccessful'}."
        )
        state.add_trace(self.name, note)
        return note

    def _error_text(self, state: WorkflowState) -> str:
        failed_checks = [
            f"{check.get('name')}: {check.get('detail')}"
            for check in state.test_result.get("checks", [])
            if not check.get("passed")
        ]
        if failed_checks:
            return "; ".join(failed_checks)
        return state.test_result.get("summary", "Unknown tester failure.")

    def _classify_issue(self, error_text: str) -> str:
        text = error_text.lower()
        if any(keyword in text for keyword in ("generated files exist", "module route file exists", "manifest file updated")):
            return "missing_file"
        if any(keyword in text for keyword in ("module registry updated", "project shell preserved", "route")):
            return "route_mismatch"
        if "import" in text:
            return "import_error"
        if any(keyword in text for keyword in ("environment", "dependency", "package", "npm", "pythonpath")):
            return "environment_issue"
        return "unknown_issue"

    def _recent_success(self, project_name: str, probable_cause: str) -> dict | None:
        db = SessionLocal()
        try:
            project = (
                db.query(Project)
                .filter(Project.name == project_service.normalize_project_name(project_name))
                .first()
            )
            if project is None:
                return None
            return repair_memory.latest_success_for_cause(db, project, probable_cause)
        finally:
            db.close()

    def _apply_fix(self, state: WorkflowState, probable_cause: str) -> tuple[list[str], str | None]:
        plan_data = state.plan_data
        project_name = plan_data["project_name"]
        module_key = plan_data["module_key"]
        route_path = plan_data["route_path"]
        title = plan_data["title"]

        builder_service.ensure_project_scaffold(project_name)

        def rebuild_module(full_refresh: bool) -> tuple[list[str], str]:
            regenerated = builder_service.generate_module_files(project_name, module_key, state.message)
            registry_file = builder_service.update_module_registry(project_name, module_key, route_path, title)
            shell_files = builder_service.build_project_shell(project_name)
            manifest_file = builder_service.write_manifest(
                project_name=project_name,
                module_key=module_key,
                instruction=state.message,
                created_files=regenerated,
                plan=plan_data["plan"],
                route_path=route_path,
                title=title,
                intent=plan_data["intent"],
            )
            changed = regenerated + [registry_file, manifest_file] + shell_files
            fix = "Regenerated module files and refreshed registry, manifest, and shell."
            if full_refresh:
                fix = "Rebuilt the module package and refreshed the project scaffold."
            return list(dict.fromkeys(changed)), fix

        if probable_cause == "missing_file":
            return rebuild_module(full_refresh=False)

        if probable_cause == "route_mismatch":
            route_file = builder_service.route_file_path(project_name, route_path)
            changed_files: list[str] = []
            if not route_file.exists():
                changed_files.extend(builder_service.generate_module_files(project_name, module_key, state.message))
            changed_files.append(
                builder_service.update_module_registry(project_name, module_key, route_path, title)
            )
            changed_files.extend(builder_service.build_project_shell(project_name))
            changed_files.append(
                builder_service.write_manifest(
                    project_name=project_name,
                    module_key=module_key,
                    instruction=state.message,
                    created_files=list(dict.fromkeys(state.files_changed + changed_files)),
                    plan=plan_data["plan"],
                    route_path=route_path,
                    title=title,
                    intent=plan_data["intent"],
                )
            )
            return list(dict.fromkeys(changed_files)), "Re-synced route metadata and refreshed the shell."

        if probable_cause in {"import_error", "environment_issue"}:
            return rebuild_module(full_refresh=True)

        return [], None

    def _persist_case(self, project_name: str, attempt: dict) -> None:
        db = SessionLocal()
        try:
            project = project_service.get_or_create_project(db, project_name)
            repair_memory.record_case(
                db,
                project,
                error_text=attempt["error_text"],
                probable_cause=attempt["probable_cause"],
                fix_applied=attempt["fix_applied"],
                success=bool(attempt["success"]),
            )
            db.commit()
        finally:
            db.close()
