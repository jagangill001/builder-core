from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.storage.storage_backend import read_json, read_recent_jsonl, save_json, save_jsonl


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
    _save_record(record)
    return record


def list_pending_approvals() -> list[dict[str, Any]]:
    records = _dedupe_latest(read_recent_jsonl("approvals", 500))
    return [record for record in records if record.get("status") == "pending"]


def decide_approval(approval_id: str, decision: str, note: str | None = None) -> dict[str, Any] | None:
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected.")

    record = read_json("approvals", approval_id)
    if record is None:
        for candidate in _dedupe_latest(read_recent_jsonl("approvals", 500)):
            if candidate.get("approval_id") == approval_id:
                record = candidate
                break
    if record is None:
        return None

    record["status"] = normalized_decision
    record["decision_note"] = note.strip() if note else None
    record["updated_at"] = _timestamp()
    _save_record(record)
    return record


def _save_record(record: dict[str, Any]) -> None:
    approval_id = str(record.get("approval_id") or "approval_missing")
    save_json("approvals", approval_id, record)
    save_jsonl("approvals", record)


def _dedupe_latest(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for record in records:
        approval_id = str(record.get("approval_id") or "")
        if approval_id and approval_id not in latest:
            latest[approval_id] = record
    return list(latest.values())


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()