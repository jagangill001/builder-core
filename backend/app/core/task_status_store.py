from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.storage.storage_backend import read_json, save_json, save_jsonl

VALID_STATUS_STEPS = {
    "received",
    "understanding",
    "security_check",
    "agent_selected",
    "waiting_for_approval",
    "research_not_connected",
    "sandbox_created",
    "completed",
    "blocked",
    "failed",
}


def save_task_status(record: dict[str, Any]) -> dict[str, Any]:
    command_id = str(record.get("command_id") or "")
    if not command_id:
        command_id = "cmd_missing"
        record["command_id"] = command_id
    record["updated_at"] = _timestamp()
    record["steps"] = [_normalize_step(step) for step in record.get("steps", [])]
    save_json("task_status", command_id, record)
    save_jsonl("task_status", record)
    return record


def get_task_status(command_id: str) -> dict[str, Any] | None:
    return read_json("task_status", command_id)


def _normalize_step(step: dict[str, Any]) -> dict[str, Any]:
    code = str(step.get("code") or "completed")
    if code not in VALID_STATUS_STEPS:
        code = "completed"
    return {
        "code": code,
        "status": str(step.get("status") or code),
        "summary": str(step.get("summary") or ""),
        "at": step.get("at") or _timestamp(),
    }


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()