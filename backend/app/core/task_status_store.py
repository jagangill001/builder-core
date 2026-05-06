from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "runtime_data"
TASK_STATUS_PATH = DATA_DIR / "task_status_records.json"

VALID_STATUS_STEPS = {
    "understanding",
    "security_check",
    "agent_selected",
    "waiting_for_approval",
    "research_not_connected",
    "completed",
    "blocked",
    "failed",
}


def save_task_status(record: dict[str, Any]) -> dict[str, Any]:
    records = _read_records()
    command_id = str(record.get("command_id") or "")
    record["updated_at"] = _timestamp()
    record["steps"] = [_normalize_step(step) for step in record.get("steps", [])]

    replaced = False
    for index, existing in enumerate(records):
        if existing.get("command_id") == command_id:
            records[index] = record
            replaced = True
            break
    if not replaced:
        records.append(record)

    _write_records(records[-500:])
    return record


def get_task_status(command_id: str) -> dict[str, Any] | None:
    for record in reversed(_read_records()):
        if record.get("command_id") == command_id:
            return record
    return None


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


def _read_records() -> list[dict[str, Any]]:
    if not TASK_STATUS_PATH.exists():
        return []
    try:
        data = json.loads(TASK_STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _write_records(records: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TASK_STATUS_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()
