from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parents[2] / "runtime_data"
APPROVALS_PATH = DATA_DIR / "approval_requests.json"


def create_approval_request(*, command_id: str, action: str, reason: str, risk_level: str) -> dict[str, Any]:
    now = _timestamp()
    record = {
        "approval_id": f"approval_{uuid4().hex[:12]}",
        "command_id": command_id,
        "status": "pending",
        "action": action,
        "reason": reason,
        "risk_level": risk_level,
        "created_at": now,
        "updated_at": now,
        "decision_note": None,
    }
    records = _read_records()
    records.append(record)
    _write_records(records)
    return record


def list_pending_approvals() -> list[dict[str, Any]]:
    return [record for record in _read_records() if record.get("status") == "pending"]


def decide_approval(approval_id: str, decision: str, note: str | None = None) -> dict[str, Any] | None:
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected.")

    records = _read_records()
    updated_record: dict[str, Any] | None = None
    for record in records:
        if record.get("approval_id") == approval_id:
            record["status"] = normalized_decision
            record["decision_note"] = note.strip() if note else None
            record["updated_at"] = _timestamp()
            updated_record = record
            break

    if updated_record is None:
        return None

    _write_records(records)
    return updated_record


def _read_records() -> list[dict[str, Any]]:
    if not APPROVALS_PATH.exists():
        return []
    try:
        data = json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _write_records(records: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    APPROVALS_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()
