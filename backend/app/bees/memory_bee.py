from __future__ import annotations

from app.core.context import WorkflowState
from app.services import memory_service


class MemoryBee:
    name = "memory_bee"

    def run(self, state: WorkflowState) -> str:
        state.memory_snapshot = memory_service.remember_workflow(
            project_name=state.project_name,
            task_id=state.task_id,
            user_message=state.message,
            assistant_reply=state.assistant_reply or state.test_result.get("summary", ""),
            intent=state.intent,
            plan=state.plan_data.get("plan", []),
            build_result=state.test_result,
            module_key=state.plan_data.get("module_key"),
            files_created=state.files_changed,
            inspection=state.inspection,
            version_snapshot=state.version_snapshot,
        )

        pattern_count = len(state.memory_snapshot.get("recent_patterns", []))
        repair_count = len(state.memory_snapshot.get("recent_repairs", []))
        note = (
            f"Stored workflow memory for {state.project_name}. "
            f"Known patterns: {pattern_count}. Known repair cases: {repair_count}."
        )
        state.add_trace(self.name, note)
        return note
