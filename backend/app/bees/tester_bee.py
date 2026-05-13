from __future__ import annotations

from app.core.context import WorkflowState
from app.services import builder_service
from app.services import tester_service


class TesterBee:
    name = "tester_bee"

    def run(self, state: WorkflowState) -> str:
        if state.plan_data.get("build_triggered"):
            state.test_result = tester_service.test_result(state.plan_data, state.files_changed)
            state.inspection = builder_service.inspect_project(state.project_name)
        elif state.intent == "inspect":
            summary = state.inspection.get("summary", {}) if state.inspection else {}
            state.test_result = {
                "status": "success",
                "summary": "Scout inspection is ready.",
                "checks": [
                    {
                        "name": "Project structure scanned",
                        "passed": True,
                        "detail": (
                            f"Observed {summary.get('module_count', 0)} module(s) "
                            f"and {summary.get('manifest_count', 0)} manifest file(s)."
                        ),
                    }
                ],
            }
        elif state.intent == "run":
            commands = state.run_info.get("commands", []) if state.run_info else []
            state.test_result = {
                "status": "success",
                "summary": "Run instructions prepared.",
                "checks": [
                    {
                        "name": "Run command set available",
                        "passed": bool(commands),
                        "detail": f"Prepared {len(commands)} command(s) for {state.project_name}.",
                    }
                ],
            }
        else:
            state.test_result = {
                "status": "skipped",
                "summary": "No build validation was required.",
                "checks": [
                    {
                        "name": "Conversation routing",
                        "passed": True,
                        "detail": "Stayed in observation mode for a chat-only request.",
                    }
                ],
            }

        note = (
            f"Tester finished with {state.test_result['status']} status: "
            f"{state.test_result['summary']}"
        )
        state.add_trace(self.name, note)
        return note
