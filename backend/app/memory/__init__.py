from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.legacy_models import MemoryEntry


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def load_json(value_json: str, default: Any) -> Any:
    try:
        return json.loads(value_json)
    except json.JSONDecodeError:
        return default


def append_entry(
    db: Session,
    *,
    memory_type: str,
    project_id: int,
    key: str,
    value: Any,
) -> MemoryEntry:
    entry = MemoryEntry(
        memory_type=memory_type,
        project_id=project_id,
        key=key,
        value_json=dump_json(value),
        created_at=timestamp(),
    )
    db.add(entry)
    db.flush()
    return entry


def upsert_entry(
    db: Session,
    *,
    memory_type: str,
    project_id: int,
    key: str,
    value: Any,
) -> MemoryEntry:
    entry = (
        db.query(MemoryEntry)
        .filter(
            MemoryEntry.memory_type == memory_type,
            MemoryEntry.project_id == project_id,
            MemoryEntry.key == key,
        )
        .first()
    )
    if entry is None:
        entry = MemoryEntry(
            memory_type=memory_type,
            project_id=project_id,
            key=key,
            value_json=dump_json(value),
            created_at=timestamp(),
        )
        db.add(entry)
    else:
        entry.value_json = dump_json(value)
        entry.created_at = timestamp()

    db.flush()
    return entry


def latest_entry(
    db: Session,
    *,
    memory_type: str,
    project_id: int,
    key: str,
) -> MemoryEntry | None:
    return (
        db.query(MemoryEntry)
        .filter(
            MemoryEntry.memory_type == memory_type,
            MemoryEntry.project_id == project_id,
            MemoryEntry.key == key,
        )
        .order_by(MemoryEntry.id.desc())
        .first()
    )


def recent_entries(
    db: Session,
    *,
    memory_type: str,
    project_id: int,
    limit: int = 10,
) -> list[MemoryEntry]:
    entries = (
        db.query(MemoryEntry)
        .filter(
            MemoryEntry.memory_type == memory_type,
            MemoryEntry.project_id == project_id,
        )
        .order_by(MemoryEntry.id.desc())
        .limit(limit)
        .all()
    )
    entries.reverse()
    return entries
