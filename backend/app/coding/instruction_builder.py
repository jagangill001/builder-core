from __future__ import annotations

from app.coding.context_builder import select_likely_files
from app.coding.repo_map import build_repo_map


def build_codex_task_package(instruction: str, repo: str) -> dict[str, object]:
    likely_files = select_likely_files(instruction)
    return {
        "repo": repo,
        "task_goal": instruction.strip(),
        "files_likely_involved": likely_files,
        "repo_map": build_repo_map(),
        "safety_notes": [
            "Do not hardcode secrets.",
            "Do not expose environment variable values.",
            "Do not claim external actions happened unless a real connector performed them.",
            "Keep edits scoped and branch-first.",
        ],
        "expected_output": [
            "Implemented code changes or an honest explanation of blockers.",
            "Files changed summary.",
            "Tests run and results.",
        ],
        "testing_instructions": [
            "Backend: python -m compileall app",
            "Backend: python -m unittest discover -s tests -v",
            "Frontend: npm run lint",
            "Frontend: npm run build",
        ],
        "final_summary_requirements": [
            "What changed.",
            "What remains placeholder.",
            "How to verify.",
        ],
    }
