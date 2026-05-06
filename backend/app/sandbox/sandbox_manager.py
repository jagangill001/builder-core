from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.storage.storage_backend import save_json, save_jsonl

ALLOWED_SANDBOX_TYPES = {"code_test", "simulation", "security_check", "connector_test"}


def create_sandbox_record(*, command_id: str | None, sandbox_type: str, description: str) -> dict[str, Any]:
    normalized_type = sandbox_type.strip().lower() if sandbox_type else "simulation"
    if normalized_type not in ALLOWED_SANDBOX_TYPES:
        normalized_type = "simulation"
    now = datetime.now(UTC).isoformat()
    sandbox_id = f"sandbox_{uuid4().hex[:12]}"
    record = {
        "sandbox_id": sandbox_id,
        "command_id": command_id or None,
        "sandbox_type": normalized_type,
        "description": description.strip(),
        "status": "created",
        "execution_allowed": False,
        "message": "Sandbox record created. Real execution is not connected yet.",
        "requires_human_approval": True,
        "created_at": now,
        "updated_at": now,
        "safe_scope": [
            "Records the requested test safely.",
            "Does not execute shell commands from user input.",
            "Does not deploy or modify production resources.",
        ],
    }
    save_json("sandbox_runs", sandbox_id, record)
    save_jsonl("sandbox_runs", record)
    return record