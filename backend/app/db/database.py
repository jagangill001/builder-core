from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import text

from app.database import Base, SessionLocal, database_runtime_status, engine

DATABASE_READY: bool | None = None
DATABASE_LAST_ERROR: str | None = None


def initialize_database() -> bool:
    """Create all known SQLAlchemy tables and verify the connection."""
    global DATABASE_LAST_ERROR, DATABASE_READY
    try:
        import app.legacy_models  # noqa: F401
        import app.db.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        DATABASE_READY = True
        DATABASE_LAST_ERROR = None
        return True
    except Exception as exc:
        DATABASE_READY = False
        DATABASE_LAST_ERROR = _safe_error(exc)
        return False


def database_connected() -> bool:
    global DATABASE_LAST_ERROR, DATABASE_READY
    if DATABASE_READY is False:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        DATABASE_READY = True
        DATABASE_LAST_ERROR = None
        return True
    except Exception as exc:
        DATABASE_READY = False
        DATABASE_LAST_ERROR = _safe_error(exc)
        return False


def runtime_status() -> dict[str, object]:
    status = database_runtime_status()
    connected = database_connected()
    status["connected"] = connected
    status["fallback_in_memory"] = not connected
    status["last_error"] = DATABASE_LAST_ERROR
    return status


@contextmanager
def session_scope() -> Iterator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _safe_error(exc: Exception) -> str:
    message = str(exc).splitlines()[0].strip()
    if not message:
        return exc.__class__.__name__
    return message[:240]
