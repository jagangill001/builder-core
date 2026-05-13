from __future__ import annotations

from typing import Any

from app.auth.auth import AuthContext
from app.brain.answer_brain import AnswerBrain
from app.brain.router import classify_command
from app.memory.lessons import record_task_failure
from app.memory.session_memory import summarize_task
from app.safety.safety_firewall import SafetyFirewall
from app.tasks.task_models import SourceModel, TaskCreateRequest, TaskRecord
from app.tasks.task_store import task_store
from app.workers.queue import internal_queue


class TaskEngine:
    def __init__(self) -> None:
        self.safety = SafetyFirewall()
        self.answer_brain = AnswerBrain()

    def create_and_process(self, payload: TaskCreateRequest, auth: AuthContext | None = None) -> TaskRecord:
        task = task_store.create(payload)
        queue_decision = internal_queue.submit(task.task_id)
        task.queued = queue_decision.queued
        task_store.save(task)
        task_store.advance(task.task_id, stage="received", progress=5, message=queue_decision.message, status="running")
        if queue_decision.queued:
            task_store.add_warning(task.task_id, "External worker queue is a placeholder; this task was processed immediately in this build.")
        return self.process(task.task_id, auth=auth)

    def process(self, task_id: str, auth: AuthContext | None = None) -> TaskRecord:
        auth_context = auth or AuthContext()
        task = task_store.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")

        task_store.advance(task_id, stage="safety_check", progress=15, message="Running safety firewall.")
        safety = self.safety.check(task.original_message)
        for warning in safety.warnings:
            task_store.add_warning(task_id, warning)
        for error in safety.errors:
            task_store.add_error(task_id, error)
        if safety.blocked:
            task_store.set_result(
                task_id,
                result={
                    "message": f"Task blocked: {safety.reason}",
                    "blocked": True,
                    "approval_required": safety.approval_required,
                    "connectors_used": [],
                    "next_step": "Rewrite the command without asking for secrets, unsafe automation, or hidden environment values.",
                },
                warnings=safety.warnings,
                errors=safety.errors,
            )
            failed_task = task_store.fail(task_id, summarize_task(task_store._require(task_id)))
            record_task_failure(task_id, failed_task.errors, failed_task.warnings)
            return failed_task

        task_store.advance(task_id, stage="planning", progress=30, message="Building simple execution plan.")
        route = classify_command(task.original_message)
        task = task_store._require(task_id)
        task.detected_intents = [route.intent]
        task.workflow = route.workflow
        task_store.save(task)

        task_store.advance(task_id, stage="routing", progress=45, message=f"Routed command to {route.intent}.")
        task_store.advance(task_id, stage="executing", progress=70, message="Executing backend-owned workflow.")
        answer = self.answer_brain.answer(task.original_message, route, auth_context)
        sources = _coerce_sources(answer.get("sources", []))
        task_store.set_result(
            task_id,
            result=answer,
            sources=sources,
            warnings=[str(item) for item in answer.get("warnings", [])],
            errors=[str(item) for item in answer.get("errors", [])],
        )

        task_store.advance(task_id, stage="summarizing", progress=90, message="Saving task summary.")
        task = task_store._require(task_id)
        summary = summarize_task(task)
        completed = task_store.complete(task_id, summary)
        if completed.errors:
            record_task_failure(task_id, completed.errors, completed.warnings)
        return completed


def _coerce_sources(raw_sources: Any) -> list[SourceModel]:
    sources: list[SourceModel] = []
    if not isinstance(raw_sources, list):
        return sources
    for source in raw_sources:
        if isinstance(source, SourceModel):
            sources.append(source)
        elif isinstance(source, dict):
            sources.append(SourceModel(**source))
    return sources


task_engine = TaskEngine()
