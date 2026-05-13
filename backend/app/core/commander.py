from __future__ import annotations

import os
from typing import Any

from app.bees.coder_bee import CoderBee
from app.bees.memory_bee import MemoryBee
from app.bees.planner_bee import PlannerBee
from app.bees.repair_bee import RepairBee
from app.bees.reporter_bee import ReporterBee
from app.bees.scout_bee import ScoutBee
from app.bees.tester_bee import TesterBee
from app.core.context import WorkflowState, build_workflow_context
from app.core.queue import BeeQueue
from app.core.router import IntentRouter
from app.database import database_runtime_status
from app.services import codex_bridge_service, intent_classifier, memory_service


class BuilderCommander:
    def __init__(self) -> None:
        self.queue = BeeQueue()
        self.intent_router = IntentRouter()
        self.bees = {
            "scout_bee": ScoutBee(),
            "planner_bee": PlannerBee(),
            "coder_bee": CoderBee(),
            "tester_bee": TesterBee(),
            "repair_bee": RepairBee(),
            "memory_bee": MemoryBee(),
            "reporter_bee": ReporterBee(),
        }
        self.phase_name = "phase_2_memory_repair"

    def execute(
        self,
        message: str,
        project_name: str,
        forced_intent: str | None = None,
        worker_mode: str = "local",
    ) -> dict[str, Any]:
        task = self.queue.enqueue(project_name=project_name, message=message, forced_intent=forced_intent)
        state = build_workflow_context(
            task_id=task.task_id,
            message=message,
            project_name=project_name,
            forced_intent=forced_intent,
            worker_mode=worker_mode,
        )
        state.intent = forced_intent or intent_classifier.classify_intent(state.message, state.memory)

        route = self.intent_router.route(state.intent)
        self.queue.mark_started(task.task_id, state.intent)

        try:
            for bee_name in route.bees:
                if self._should_delegate_to_codex(state, bee_name):
                    note = self._submit_codex_task(state)
                    self.queue.note(task.task_id, "codex_bridge", note)
                    continue

                if self._should_skip_tester_for_codex(state, bee_name):
                    note = self._mark_codex_waiting(state)
                    self.queue.note(task.task_id, bee_name, note)
                    continue

                note = self.bees[bee_name].run(state)
                self.queue.note(task.task_id, bee_name, note)
                if bee_name == "tester_bee" and state.worker_mode != "codex":
                    self._run_repair_loop(state, task.task_id)
        except Exception as exc:
            failure_state = self._build_failure_state(state, exc)
            response = self.bees["reporter_bee"].build_response(failure_state)
            self.queue.mark_failed(task.task_id, response["test_result"]["summary"])
            return self._attach_memory_snapshot(failure_state, response, route.bees)

        response = self.bees["reporter_bee"].build_response(state)
        self.queue.mark_completed(task.task_id, response["test_result"]["summary"])
        return self._attach_memory_snapshot(state, response, route.bees)

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": "Builder Core v2",
            "phase": self.phase_name,
            "registered_bees": list(self.bees),
            "supported_intents": self.intent_router.supported_intents(),
            "queue": self.queue.snapshot(),
            "runtime": {
                "app_revision": os.getenv("APP_REVISION", "local-dev"),
                "frontend_public_url": os.getenv("FRONTEND_PUBLIC_URL"),
                "database": database_runtime_status(),
            },
        }

    def _attach_memory_snapshot(
        self,
        state: WorkflowState,
        response: dict[str, Any],
        route: tuple[str, ...],
    ) -> dict[str, Any]:
        memory_snapshot = state.memory_snapshot or memory_service.get_project_memory(state.project_name)
        response["memory"] = {
            "selected_project": state.project_name,
            "latest_generated_module": memory_snapshot.get("latest_generated_module"),
            "latest_plan": memory_snapshot.get("latest_plan", []),
            "latest_build_result": memory_snapshot.get("latest_build_result", {}),
            "latest_intent": memory_snapshot.get("latest_intent"),
            "recent_chat_history": memory_snapshot.get("recent_chat_history", []),
            "recent_patterns": memory_snapshot.get("recent_patterns", []),
            "recent_repairs": memory_snapshot.get("recent_repairs", []),
        }
        response["commander"] = {
            "task_id": state.task_id,
            "phase": self.phase_name,
            "bee_route": list(route),
        }
        return response

    @staticmethod
    def _should_delegate_to_codex(state: WorkflowState, bee_name: str) -> bool:
        return state.worker_mode == "codex" and state.intent in {"build", "modify"} and bee_name == "coder_bee"

    @staticmethod
    def _should_skip_tester_for_codex(state: WorkflowState, bee_name: str) -> bool:
        return state.worker_mode == "codex" and state.codex_task is not None and bee_name == "tester_bee"

    def _build_failure_state(self, state: WorkflowState, exc: Exception) -> WorkflowState:
        state.test_result = {
            "status": "failed",
            "summary": f"Commander halted after an unexpected error: {exc}",
            "checks": [
                {
                    "name": "Commander execution",
                    "passed": False,
                    "detail": str(exc),
                }
            ],
        }
        state.proposed_improvements = [
            "Route this failure through repair_bee once phase 3 is enabled.",
            "Keep the current low-risk bee set isolated until the failing step is reproduced safely.",
        ]
        reporter = self.bees["reporter_bee"]
        reporter.run(state)
        self.bees["memory_bee"].run(state)
        return state

    def _run_repair_loop(self, state: WorkflowState, task_id: str) -> None:
        if not state.plan_data.get("build_triggered"):
            return

        while state.test_result.get("status") == "failed" and state.repair_attempts < state.max_repair_attempts:
            repair_note = self.bees["repair_bee"].run(state)
            self.queue.note(task_id, "repair_bee", repair_note)

            pending_attempt = next(
                (
                    attempt
                    for attempt in reversed(state.repair_history)
                    if attempt.get("attempted_fix") and not attempt.get("recorded")
                ),
                None,
            )
            if pending_attempt is None:
                break

            test_note = self.bees["tester_bee"].run(state)
            self.queue.note(task_id, "tester_bee", test_note)

            record_note = self.bees["repair_bee"].record_result(state)
            if record_note:
                self.queue.note(task_id, "repair_bee", record_note)

            if state.test_result.get("status") == "success":
                break

    def _submit_codex_task(self, state: WorkflowState) -> str:
        state.codex_task = codex_bridge_service.create_task_from_workflow(
            project_name=state.project_name,
            intent=state.intent,
            user_message=state.message,
            plan=state.plan_data.get("plan", []),
            source_task_id=state.task_id,
        )
        task_status = state.codex_task.get("status", "queued")
        summary = state.codex_task.get("latest_summary", "Codex task submitted.")
        next_action = state.codex_task.get("next_action", "")
        mapped_status = "failed" if task_status in {"failed", "pending_setup"} else "pending"
        state.test_result = {
            "status": mapped_status,
            "summary": (
                "Codex task queued for branch-first implementation."
                if mapped_status != "failed"
                else "Codex bridge needs attention before this task can run."
            ),
            "checks": [
                {
                    "name": "Codex bridge",
                    "passed": mapped_status != "failed",
                    "detail": summary,
                },
                {
                    "name": "Next action",
                    "passed": True,
                    "detail": next_action,
                },
            ],
        }
        state.add_trace("codex_bridge", summary)
        return summary

    def _mark_codex_waiting(self, state: WorkflowState) -> str:
        note = "Tester bee deferred until Codex opens a branch or pull request and CI can run."
        state.add_trace("tester_bee", note)
        return note


commander = BuilderCommander()
