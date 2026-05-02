from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    "node_modules",
    "venv",
    "__pycache__",
    "runtime_data",
    "dist",
    "build",
    "out",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningService:
    def __init__(self, repo_root: Path, storage: ProjectStorageService) -> None:
        self.repo_root = repo_root
        self.storage = storage

    def scan_project_structure(self) -> dict[str, Any]:
        sample_tree: list[str] = []
        top_level_folders: list[str] = []
        important_files: list[str] = []

        for child in sorted(self.repo_root.iterdir(), key=lambda path: path.name.lower()):
            if child.is_dir() and child.name not in IGNORED_DIRECTORIES:
                top_level_folders.append(child.name)
            elif child.is_file():
                important_files.append(child.name)

        for root, directories, files in self._walk_repo():
            relative_root = root.relative_to(self.repo_root)
            depth = len(relative_root.parts)

            if depth == 0:
                continue

            if depth > 3:
                directories[:] = []
                continue

            display_root = str(relative_root).replace("\\", "/")
            sample_tree.append(f"{display_root}/")

            for filename in sorted(files)[:4]:
                sample_tree.append(f"{display_root}/{filename}")

            if len(sample_tree) >= 60:
                break

        summary = {
            "scanned_at": utc_now_iso(),
            "root": str(self.repo_root),
            "top_level_folders": top_level_folders,
            "important_files": important_files[:20],
            "sample_tree": sample_tree[:60],
            "notes": [
                "This is a file and folder summary only.",
                "Builder Core is learning from project history and structure, not training a new AI model.",
            ],
        }
        self.storage.save_project_structure_summary(summary)
        return summary

    def record_task_lesson(self, task: dict[str, Any]) -> dict[str, Any]:
        summary = task.get("summary") if isinstance(task.get("summary"), dict) else {}
        errors = task.get("errors") if isinstance(task.get("errors"), list) else []
        files_changed = task.get("files_changed") if isinstance(task.get("files_changed"), list) else []
        final_status = str(task.get("status", "unknown"))
        bridge_status = task.get("bridge_status") if isinstance(task.get("bridge_status"), dict) else {}

        if final_status == "completed":
            lesson_learned = "This task completed through the backend task runner and produced a saved summary."
            next_recommendation = summary.get(
                "next_recommended_step",
                "Review the summary and choose the next small safe upgrade.",
            )
        elif bridge_status.get("ready_for_repo_work") is False:
            lesson_learned = "Builder Core still needs bridge credentials or an enabled Codex mode before it can make real repo changes."
            next_recommendation = "Add the missing GitHub and Codex environment variables in Cloud Run, then retry the task."
        elif errors:
            lesson_learned = "The task failed during backend processing and needs a focused fix before retrying."
            next_recommendation = "Review the latest error and fix the smallest blocking issue first."
        else:
            lesson_learned = "The task ended early without a clear success signal."
            next_recommendation = "Review the latest logs and confirm the next safe manual step."

        lesson = {
            "task_id": task.get("id"),
            "command": task.get("command"),
            "what_happened": summary.get("what_completed") if isinstance(summary.get("what_completed"), list) else task.get("stage"),
            "files_changed": files_changed,
            "error": errors[0] if errors else None,
            "lesson_learned": lesson_learned,
            "next_recommendation": next_recommendation,
            "status": final_status,
            "created_at": utc_now_iso(),
        }
        return self.storage.save_lesson(lesson)

    def get_lessons(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.storage.get_lessons(limit)

    def get_known_issues(self) -> list[str]:
        issues: list[str] = []
        for lesson in self.storage.get_lessons(30):
            error = lesson.get("error")
            if isinstance(error, str) and error and error not in issues:
                issues.append(error)

        for problem in self.storage.get_known_environment_problems():
            if problem not in issues:
                issues.append(problem)

        return issues[:10]

    def get_recommended_next_steps(self) -> list[str]:
        steps: list[str] = []
        if not self.storage.get_project_structure_summary():
            steps.append("Run a project scan so Builder Core has a fresh structure summary.")

        bridge_status = self.storage.get_latest_bridge_status() or {}
        if isinstance(bridge_status, dict) and bridge_status.get("ready_for_repo_work") is False:
            steps.append("Add GitHub and Codex bridge credentials before expecting real repo changes.")

        latest_summary = self.storage.get_latest_summary() or {}
        if isinstance(latest_summary, dict):
            manual_setup = latest_summary.get("what_still_needs_manual_setup", [])
            if isinstance(manual_setup, list):
                for item in manual_setup:
                    text = str(item)
                    if text and text not in steps:
                        steps.append(text)

        if not steps:
            steps.append("Submit another task and compare the new lesson with the previous run.")

        return steps[:8]

    def build_learning_payload(self) -> dict[str, Any]:
        project_structure = self.storage.get_project_structure_summary()
        if project_structure is None:
            project_structure = self.scan_project_structure()

        return {
            "storage_backend": self.storage.storage_backend,
            "storage_message": self.storage.storage_message,
            "project_structure_summary": project_structure,
            "lessons": self.get_lessons(12),
            "known_issues": self.get_known_issues(),
            "recommended_next_steps": self.get_recommended_next_steps(),
            "notes": [
                "Builder Core is learning from project history, stored summaries, and file scans.",
                "It is not training a new AI model in this phase.",
            ],
        }

    def _walk_repo(self):
        for root, directories, files in os.walk(self.repo_root):
            directories[:] = [item for item in directories if item not in IGNORED_DIRECTORIES]
            yield Path(root), directories, files
