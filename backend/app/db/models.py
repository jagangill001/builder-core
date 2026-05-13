from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text

from app.database import Base
from app.tasks.task_models import utc_now


class BuilderTask(Base):
    __tablename__ = "builder_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), nullable=False, unique=True, index=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(String(40), nullable=False, default=utc_now)
    updated_at = Column(String(40), nullable=False, default=utc_now)


class BuilderTaskLog(Base):
    __tablename__ = "builder_task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    timestamp = Column(String(40), nullable=False, default=utc_now)


class BuilderTaskSummary(Base):
    __tablename__ = "builder_task_summaries"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(String(40), nullable=False, default=utc_now)


class ProjectMemoryRecord(Base):
    __tablename__ = "builder_project_memory"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), nullable=False, unique=True, index=True)
    payload_json = Column(Text, nullable=False)
    updated_at = Column(String(40), nullable=False, default=utc_now)


class BuilderAuditLog(Base):
    __tablename__ = "builder_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(120), nullable=False)
    role = Column(String(40), nullable=False, default="viewer")
    payload_json = Column(Text, nullable=False)
    created_at = Column(String(40), nullable=False, default=utc_now)
