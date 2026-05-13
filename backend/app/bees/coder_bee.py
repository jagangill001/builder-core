from __future__ import annotations

from app.core.context import WorkflowState
from app.services import builder_service
from app.services import version_service


class CoderBee:
    name = "coder_bee"

    def run(self, state: WorkflowState) -> str:
        if not state.plan_data.get("build_triggered"):
            note = "Skipped code changes because this route does not require generation."
            state.add_trace(self.name, note)
            return note

        project_name = state.plan_data["project_name"]
        module_key = state.plan_data["module_key"]
        route_path = state.plan_data["route_path"]
        title = state.plan_data["title"]

        state.version_snapshot = version_service.create_snapshot(
            project_name,
            message=state.message,
            plan_data=state.plan_data,
        )
        created_files = builder_service.generate_module_files(project_name, module_key, state.message)
        registry_file = builder_service.update_module_registry(project_name, module_key, route_path, title)
        shell_files = builder_service.build_project_shell(project_name)
        manifest_file = builder_service.write_manifest(
            project_name=project_name,
            module_key=module_key,
            instruction=state.message,
            created_files=created_files,
            plan=state.plan_data["plan"],
            route_path=route_path,
            title=title,
            intent=state.plan_data["intent"],
        )

        all_files = created_files + [registry_file, manifest_file] + shell_files
        state.files_changed = list(dict.fromkeys(all_files))
        note = (
            f"Created snapshot {state.version_snapshot['version_id']} and changed "
            f"{len(state.files_changed)} file(s) while updating {title}."
        )
        state.add_trace(self.name, note)
        return note
