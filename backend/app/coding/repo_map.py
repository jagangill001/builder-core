from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SKIP_DIRS = {".git", ".next", "node_modules", "__pycache__", "generated", "data"}


def build_repo_map(limit: int = 80) -> dict[str, object]:
    files: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if len(files) >= limit:
            break
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(str(path.relative_to(REPO_ROOT)).replace("\\", "/"))
    return {
        "repo_root": str(REPO_ROOT),
        "files_sample": files,
        "truncated": len(files) >= limit,
    }
