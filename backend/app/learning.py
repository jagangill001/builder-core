from __future__ import annotations

import os
import re
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

        if final_status.startswith("completed"):
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

    def extract_codex_summary_details(self, codex_summary: str) -> dict[str, Any]:
        lines = [line.strip() for line in codex_summary.splitlines() if line.strip()]
        files_changed: list[str] = []
        what_completed: list[str] = []
        what_remains: list[str] = []
        known_issues: list[str] = []

        section = "completed"
        file_pattern = re.compile(
            r"(?:backend|frontend|app|src|docs|tests|[A-Za-z0-9_.-]+)/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|tsx|ts|js|json|md|txt|css|mjs)"
        )

        for raw_line in lines:
            line = raw_line.lstrip("-*0123456789. ").strip()
            lowered = line.lower()

            if "file" in lowered and "changed" in lowered:
                section = "files"
            elif lowered.startswith("completed") or lowered.startswith("what was completed"):
                section = "completed"
                continue
            elif "remain" in lowered or "manual setup" in lowered or "still needs" in lowered:
                section = "remaining"
                continue
            elif "issue" in lowered or "error" in lowered or "warning" in lowered:
                section = "issues"
                continue

            for match in file_pattern.findall(raw_line.replace("\\", "/")):
                if match not in files_changed:
                    files_changed.append(match)

            if any(keyword in lowered for keyword in ("error", "failed", "warning", "blocked", "missing")):
                if line not in known_issues:
                    known_issues.append(line)

            if section == "files":
                continue

            if section == "remaining":
                if line and line not in what_remains:
                    what_remains.append(line)
                continue

            if section == "issues":
                if line and line not in known_issues:
                    known_issues.append(line)
                continue

            if line and line not in what_completed:
                what_completed.append(line)

        if not what_completed:
            what_completed = lines[:3]

        next_recommendation = (
            what_remains[0]
            if what_remains
            else "Review the saved Codex summary, verify the changed files, and decide the next safe Builder Core task."
        )

        return {
            "files_changed": files_changed[:20],
            "what_completed": what_completed[:12],
            "what_remains": what_remains[:10],
            "known_issues": known_issues[:10],
            "next_recommendation": next_recommendation,
        }

    def record_codex_summary_lesson(self, task: dict[str, Any], codex_summary: str) -> dict[str, Any]:
        extracted = self.extract_codex_summary_details(codex_summary)
        intelligence_mode = str(task.get("intelligence_mode") or "manual_codex")
        lesson = {
            "task_id": task.get("id"),
            "command": task.get("command"),
            "what_happened": extracted["what_completed"],
            "files_changed": extracted["files_changed"],
            "error": extracted["known_issues"][0] if extracted["known_issues"] else None,
            "lesson_learned": (
                f"Builder Core saved a manual Codex summary from {intelligence_mode} mode and turned it into project memory and a reusable lesson."
            ),
            "next_recommendation": extracted["next_recommendation"],
            "status": task.get("status", "completed_manual_codex"),
            "intelligence_mode": intelligence_mode,
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

        intelligence_history = self.storage.get_intelligence_history(12)
        recent_modes: list[str] = []
        for item in intelligence_history:
            mode = str(item.get("mode") or "").strip()
            if mode and mode not in recent_modes:
                recent_modes.append(mode)

        return {
            "storage_backend": self.storage.storage_backend,
            "storage_message": self.storage.storage_message,
            "project_structure_summary": project_structure,
            "lessons": self.get_lessons(12),
            "known_issues": self.get_known_issues(),
            "recommended_next_steps": self.get_recommended_next_steps(),
            "recent_intelligence_modes": recent_modes,
            "notes": [
                "Builder Core is learning from project history, stored summaries, and file scans.",
                "It is not training a new AI model in this phase.",
            ],
        }

    def _walk_repo(self):
        for root, directories, files in os.walk(self.repo_root):
            directories[:] = [item for item in directories if item not in IGNORED_DIRECTORIES]
            yield Path(root), directories, files
