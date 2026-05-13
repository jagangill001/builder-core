import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WORKSPACE_DB_PATH = DATA_DIR / "builder_core.db"
DEFAULT_SQLITE_URL = "sqlite:///./data/builder_core.db"
DATABASE_CONFIGURED_FROM_ENV = bool(os.getenv("DATABASE_URL", "").strip())


def _is_onedrive_path(path: Path) -> bool:
    return any(part.lower().startswith("onedrive") for part in path.resolve().parts)


def _choose_local_sqlite_path() -> Path:
    configured_dir = os.getenv("BUILDER_CORE_SQLITE_DIR", "").strip()
    if configured_dir:
        return Path(configured_dir).expanduser() / "builder_core.db"
    if os.getenv("BUILDER_CORE_FORCE_WORKSPACE_DB", "").strip().lower() in {"1", "true", "yes"}:
        return WORKSPACE_DB_PATH
    if _is_onedrive_path(BASE_DIR):
        return Path(tempfile.gettempdir()) / "BuilderCore" / "data" / "builder_core.db"
    return WORKSPACE_DB_PATH


DB_PATH = WORKSPACE_DB_PATH if DATABASE_CONFIGURED_FROM_ENV else _choose_local_sqlite_path()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOCAL_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)

ENGINE_OPTIONS = (
    {"connect_args": {"check_same_thread": False}, "pool_pre_ping": True}
    if DATABASE_URL.startswith("sqlite")
    else {"pool_pre_ping": True}
)

engine = create_engine(DATABASE_URL, **ENGINE_OPTIONS)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=MEMORY")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def database_runtime_status() -> dict[str, object]:
    url = make_url(DATABASE_URL)
    driver = url.drivername
    provider = "sqlite" if driver.startswith("sqlite") else "postgres" if driver.startswith("postgres") else driver
    is_local_sqlite = driver.startswith("sqlite") and str(url.database or "").endswith("builder_core.db")
    return {
        "driver": driver,
        "provider": provider,
        "configured_from_env": DATABASE_CONFIGURED_FROM_ENV,
        "database_url_configured": DATABASE_CONFIGURED_FROM_ENV,
        "default_sqlite_url": DEFAULT_SQLITE_URL,
        "workspace_default_path": str(WORKSPACE_DB_PATH),
        "database_path": str(DB_PATH) if is_local_sqlite else None,
        "one_drive_workspace": _is_onedrive_path(BASE_DIR),
        "workspace_sqlite_warning": (
            "Workspace is inside OneDrive; default local SQLite is stored in a non-synced app data directory."
            if _is_onedrive_path(BASE_DIR) and not DATABASE_CONFIGURED_FROM_ENV
            else None
        ),
        "uses_local_disk": is_local_sqlite,
        "mode": "local_sqlite" if is_local_sqlite and not DATABASE_CONFIGURED_FROM_ENV else "external_database",
    }
