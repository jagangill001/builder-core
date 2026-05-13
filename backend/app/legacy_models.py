from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

    requests = relationship("BuildRequestRecord", back_populates="project", cascade="all, delete-orphan")
    memory_entries = relationship("MemoryEntry", back_populates="project", cascade="all, delete-orphan")
    repair_cases = relationship("RepairCase", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("VersionRecord", back_populates="project", cascade="all, delete-orphan")
    codex_tasks = relationship("CodexTaskRecord", back_populates="project", cascade="all, delete-orphan")


class BuildRequestRecord(Base):
    __tablename__ = "build_requests"

    id = Column(Integer, primary_key=True, index=True)
    instruction = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="requests")
    plans = relationship("PlanStep", back_populates="request", cascade="all, delete-orphan")
    files = relationship("CreatedFile", back_populates="request", cascade="all, delete-orphan")


class PlanStep(Base):
    __tablename__ = "plan_steps"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("build_requests.id"), nullable=False)
    step_text = Column(Text, nullable=False)

    request = relationship("BuildRequestRecord", back_populates="plans")


class CreatedFile(Base):
    __tablename__ = "created_files"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("build_requests.id"), nullable=False)
    file_path = Column(Text, nullable=False)

    request = relationship("BuildRequestRecord", back_populates="files")


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(String(50), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    key = Column(String(255), nullable=False)
    value_json = Column(Text, nullable=False)
    created_at = Column(String(40), nullable=False, default=_timestamp)

    project = relationship("Project", back_populates="memory_entries")


class RepairCase(Base):
    __tablename__ = "repair_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    error_text = Column(Text, nullable=False)
    probable_cause = Column(Text, nullable=False)
    fix_applied = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    created_at = Column(String(40), nullable=False, default=_timestamp)

    project = relationship("Project", back_populates="repair_cases")


class VersionRecord(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    snapshot_note = Column(Text, nullable=False)
    created_at = Column(String(40), nullable=False, default=_timestamp)

    project = relationship("Project", back_populates="versions")


class CodexTaskRecord(Base):
    __tablename__ = "codex_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(40), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_task_id = Column(String(40), nullable=True)
    intent = Column(String(50), nullable=False)
    worker_mode = Column(String(20), nullable=False, default="codex")
    status = Column(String(50), nullable=False, default="queued")
    title = Column(String(255), nullable=False)
    user_message = Column(Text, nullable=False)
    plan_json = Column(Text, nullable=False, default="[]")
    github_issue_number = Column(Integer, nullable=True)
    github_issue_url = Column(Text, nullable=True)
    github_issue_state = Column(String(50), nullable=True)
    pull_request_url = Column(Text, nullable=True)
    latest_summary = Column(Text, nullable=False, default="")
    last_error = Column(Text, nullable=True)
    created_at = Column(String(40), nullable=False, default=_timestamp)
    updated_at = Column(String(40), nullable=False, default=_timestamp)

    project = relationship("Project", back_populates="codex_tasks")
