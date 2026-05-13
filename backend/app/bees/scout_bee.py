from __future__ import annotations

from app.core.context import WorkflowState
from app.services import builder_service


class ScoutBee:
    name = "scout_bee"

    def run(self, state: WorkflowState) -> str:
        state.inspection = builder_service.inspect_project(state.project_name)
        summary = state.inspection.get("summary", {})
        routes = state.inspection.get("routes", [])

        if state.intent == "run":
            state.run_info = builder_service.get_run_info(state.project_name)

        route_preview = ", ".join(routes[:3]) if routes else "/"
        note = (
            f"Scanned {summary.get('module_count', 0)} module(s), "
            f"{summary.get('file_count', 0)} file(s), and routes {route_preview}."
        )
        if state.run_info:
            note += " Prepared run guidance from the generated project scaffold."

        state.add_trace(self.name, note)
        return note
