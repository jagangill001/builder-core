from __future__ import annotations


LIKELY_FILES = {
    "frontend": ["frontend/src/app/page.tsx", "frontend/src/lib/api.ts", "frontend/src/types.ts"],
    "backend": ["backend/app/main.py", "backend/app/tasks/task_engine.py", "backend/app/connectors/registry.py"],
    "github": ["backend/app/connectors/github.py", ".github/workflows/deploy-cloud-run.yml"],
    "deployment": ["backend/app/deployment/deployment_routes.py", ".github/workflows/deploy-cloud-run.yml"],
    "memory": ["backend/app/memory/project_memory.py", "backend/app/memory/lessons.py"],
    "auth": ["backend/app/auth/auth.py", "backend/app/auth/dependencies.py"],
}


def select_likely_files(instruction: str) -> list[str]:
    normalized = instruction.lower()
    selected: list[str] = []
    for keyword, files in LIKELY_FILES.items():
        if keyword in normalized:
            selected.extend(files)
    if not selected:
        selected = [
            "backend/app/main.py",
            "backend/app/tasks/task_engine.py",
            "frontend/src/app/page.tsx",
        ]
    return list(dict.fromkeys(selected))
