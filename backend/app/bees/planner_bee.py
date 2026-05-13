from __future__ import annotations

from app.core.context import WorkflowState
from app.services import planner_service


class PlannerBee:
    name = "planner_bee"

    def run(self, state: WorkflowState) -> str:
        state.plan_data = planner_service.create_plan(
            message=state.message,
            project_name=state.project_name,
            intent=state.intent,
            memory=state.memory,
        )

        step_count = len(state.plan_data.get("plan", []))
        summary = state.plan_data.get("summary", "Prepared the next actions.")
        note = f"Prepared {step_count} step(s). {summary}"
        state.add_trace(self.name, note)
        return note
