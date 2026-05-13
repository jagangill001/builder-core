from __future__ import annotations

from app.tasks.task_models import TASK_STAGES, TaskRecord


STAGE_LABELS = {
    "received": "User Command",
    "safety_check": "Safety Check",
    "planning": "Planning",
    "routing": "Router",
    "executing": "Execution",
    "summarizing": "Summary",
    "completed": "Completed",
    "failed": "Failed",
}


def build_workflow_graph(task: TaskRecord) -> dict[str, object]:
    completed: list[str] = []
    failed: list[str] = []
    for stage in TASK_STAGES:
        if task.current_stage == "failed" and stage == "failed":
            failed.append(stage)
        elif task.progress >= _stage_progress(stage) and stage != "failed":
            completed.append(stage)

    nodes = [{"id": stage, "label": STAGE_LABELS.get(stage, stage.replace("_", " ").title())} for stage in TASK_STAGES]
    edges = [{"from": TASK_STAGES[index], "to": TASK_STAGES[index + 1]} for index in range(len(TASK_STAGES) - 2)]
    return {
        "nodes": nodes,
        "edges": edges,
        "current_node": task.current_stage,
        "completed_nodes": completed,
        "failed_nodes": failed,
    }


def _stage_progress(stage: str) -> int:
    return {
        "received": 0,
        "safety_check": 15,
        "planning": 30,
        "routing": 45,
        "executing": 70,
        "summarizing": 90,
        "completed": 100,
        "failed": 100,
    }.get(stage, 0)
