from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


TASK_STAGES = [
    "received",
    "safety_check",
    "planning",
    "routing",
    "executing",
    "summarizing",
    "completed",
    "failed",
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class SourceModel(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""
    rank: str = "unknown"
    reason: str = "No ranking reason recorded."


class TaskLog(BaseModel):
    timestamp: str = Field(default_factory=utc_now)
    stage: str
    level: str = "info"
    message: str


class TaskCreateRequest(BaseModel):
    message: str = Field(default="", max_length=12000)
    project_name: str = "Builder Core"
    priority: str = "normal"
    timeout_seconds: int = 60


class TaskSummary(BaseModel):
    what_user_asked: str
    workflow_used: str
    tools_connectors_used: list[str] = Field(default_factory=list)
    files_touched: list[str] = Field(default_factory=list)
    result: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_step: str = ""


class TaskRecord(BaseModel):
    task_id: str
    original_message: str
    normalized_message: str
    detected_intents: list[str] = Field(default_factory=list)
    workflow: str = "unknown"
    status: str = "received"
    progress: int = 0
    current_stage: str = "received"
    logs: list[TaskLog] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    sources: list[SourceModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    priority: str = "normal"
    timeout_seconds: int = 60
    queued: bool = False
    summary: TaskSummary | None = None


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
