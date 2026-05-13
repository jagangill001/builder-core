from __future__ import annotations

import json
from typing import Any

from app.db.database import database_connected, session_scope
from app.db.models import BuilderAuditLog, BuilderTask, BuilderTaskLog, BuilderTaskSummary, ProjectMemoryRecord
from app.tasks.task_models import TaskLog, TaskRecord, TaskSummary, model_to_dict, utc_now


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class BuilderRepository:
    def save_task(self, task: TaskRecord) -> bool:
        if not database_connected():
            return False
        try:
            with session_scope() as db:
                row = db.query(BuilderTask).filter(BuilderTask.task_id == task.task_id).first()
                payload = _dump(model_to_dict(task))
                if row is None:
                    db.add(
                        BuilderTask(
                            task_id=task.task_id,
                            payload_json=payload,
                            created_at=task.created_at,
                            updated_at=task.updated_at,
                        )
                    )
                else:
                    row.payload_json = payload
                    row.updated_at = task.updated_at
            return True
        except Exception:
            return False

    def get_task(self, task_id: str) -> TaskRecord | None:
        if not database_connected():
            return None
        try:
            with session_scope() as db:
                row = db.query(BuilderTask).filter(BuilderTask.task_id == task_id).first()
                if row is None:
                    return None
                return TaskRecord(**_load(row.payload_json, {}))
        except Exception:
            return None

    def append_task_log(self, task_id: str, log: TaskLog) -> bool:
        if not database_connected():
            return False
        try:
            with session_scope() as db:
                db.add(
                    BuilderTaskLog(
                        task_id=task_id,
                        payload_json=_dump(model_to_dict(log)),
                        timestamp=log.timestamp,
                    )
                )
            return True
        except Exception:
            return False

    def save_task_summary(self, task_id: str, summary: TaskSummary) -> bool:
        if not database_connected():
            return False
        try:
            with session_scope() as db:
                db.add(
                    BuilderTaskSummary(
                        task_id=task_id,
                        payload_json=_dump(model_to_dict(summary)),
                        created_at=utc_now(),
                    )
                )
            return True
        except Exception:
            return False

    def get_project_memory(self, key: str) -> dict[str, Any] | None:
        if not database_connected():
            return None
        try:
            with session_scope() as db:
                row = db.query(ProjectMemoryRecord).filter(ProjectMemoryRecord.key == key).first()
                if row is None:
                    return None
                return _load(row.payload_json, {})
        except Exception:
            return None

    def save_project_memory(self, key: str, payload: dict[str, Any]) -> bool:
        if not database_connected():
            return False
        try:
            with session_scope() as db:
                row = db.query(ProjectMemoryRecord).filter(ProjectMemoryRecord.key == key).first()
                payload_json = _dump(payload)
                if row is None:
                    db.add(ProjectMemoryRecord(key=key, payload_json=payload_json, updated_at=utc_now()))
                else:
                    row.payload_json = payload_json
                    row.updated_at = utc_now()
            return True
        except Exception:
            return False

    def audit(self, action: str, role: str, payload: dict[str, Any]) -> bool:
        if not database_connected():
            return False
        try:
            with session_scope() as db:
                db.add(
                    BuilderAuditLog(
                        action=action,
                        role=role,
                        payload_json=_dump(payload),
                        created_at=utc_now(),
                    )
                )
            return True
        except Exception:
            return False

    def list_audit_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        if not database_connected():
            return []
        try:
            with session_scope() as db:
                rows = (
                    db.query(BuilderAuditLog)
                    .order_by(BuilderAuditLog.id.desc())
                    .limit(max(1, min(limit, 200)))
                    .all()
                )
                return [
                    {
                        "timestamp": row.created_at,
                        "action": row.action,
                        "actor": row.role,
                        "payload": _load(row.payload_json, {}),
                    }
                    for row in rows
                ]
        except Exception:
            return []


repository = BuilderRepository()
