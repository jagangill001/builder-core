from __future__ import annotations

from typing import Any


REPO_URL = "https://github.com/jagangill001/builder-core"
MAIN_FOLDERS = ["backend/", "frontend/"]
MAIN_FILES = [
    "backend/app/main.py",
    "backend/app/tasks.py",
    "backend/app/storage.py",
    "backend/app/bridge.py",
    "backend/app/chat_assistant.py",
    "backend/app/command_router.py",
    "backend/app/orchestrator.py",
    "backend/app/private_search.py",
    "backend/app/document_ingest.py",
    "backend/app/web_ingest.py",
    "backend/app/crawler_plan.py",
    "backend/app/research_engine.py",
    "backend/app/market_analyzer.py",
    "backend/app/app_planner.py",
    "backend/app/model_router.py",
    "backend/app/safety.py",
    "backend/app/tool_registry.py",
    "backend/app/research_tasks.py",
    "backend/app/self_improvement.py",
    "backend/app/learning.py",
    "backend/app/services/task_service.py",
    "frontend/src/app/page.tsx",
    "README.md",
    "COMMAND_CENTER.md",
    "PROJECT_PROGRESS.md",
]


def get_project_context(project_structure_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    context = {
        "project_name": "Builder Core",
        "repo": REPO_URL,
        "main_folders": MAIN_FOLDERS,
        "main_files": MAIN_FILES,
    }

    if project_structure_summary:
        context["project_structure_summary"] = {
            "top_level_folders": project_structure_summary.get("top_level_folders", [])[:10],
            "important_files": project_structure_summary.get("important_files", [])[:15],
            "sample_tree": project_structure_summary.get("sample_tree", [])[:20],
            "notes": project_structure_summary.get("notes", []),
        }

    return context


def build_legal_safe_instructions() -> list[str]:
    return [
        "Write the code yourself.",
        "Do not copy external copyrighted code.",
        "Do not add secrets or credentials to the code.",
        "Do not fake success.",
        "Keep the implementation simple, readable, and beginner-friendly.",
        "Do not remove working frontend, backend, memory, learning, or storage systems unless the task requires it.",
    ]


def build_summary_requirements() -> list[str]:
    return [
        "List the exact files changed.",
        "Explain what was completed.",
        "Explain what still needs manual setup.",
        "Explain any backend, frontend, storage, or bridge limits.",
        "Include the exact local test commands you ran or could not run.",
        "State clearly if no real repo changes were made.",
    ]


def build_acceptance_checks() -> list[str]:
    return [
        "Backend: GET /system/status",
        "Backend: GET /tools",
        "Backend: GET /assistant/model-status",
        "Backend: GET /search/status",
        "Backend: POST /search/add",
        "Backend: POST /search/query",
        "Backend: POST /search/rebuild",
        "Backend: POST /documents/ingest-text",
        "Backend: POST /search/ingest-url",
        "Backend: POST /crawler/plan",
        "Backend: POST /command",
        "Backend: GET /storage/status",
        "Backend: POST /storage/test",
        "Backend: POST /assistant/chat",
        "Backend: GET /assistant/history",
        "Backend: POST /assistant/idea",
        "Backend: POST /research/tasks",
        "Backend: GET /research/tasks",
        "Backend: GET /research/tasks/{research_id}",
        "Backend: GET /self-improvement",
        "Backend: POST /self-improvement",
        "Backend: POST /intelligence/plan",
        "Backend: GET /intelligence",
        "Backend: POST /prompts/codex",
        "Backend: GET /prompts/latest",
        "Backend: POST /tasks/{task_id}/codex-summary",
        "Backend: GET /memory",
        "Backend: GET /learning",
        "Frontend: one main command chat works without tabs",
        "Frontend: one message can trigger combined workflow output",
        "Frontend: user can copy the Codex prompt when present",
        "Frontend: internal tools panel is collapsed by default",
        "Frontend: storage/model/search debug panels are collapsed by default",
        "Frontend: user can chat with Builder Core Assistant",
        "Frontend: user can copy the prompt",
        "Frontend: user can paste and save a Codex summary",
        "Frontend: memory, learning, self-improvement, research, and latest prompt panels refresh correctly",
    ]


def build_codex_prompt(
    command: str,
    project_context: dict[str, Any],
    memory: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    known_issues: list[str] | None = None,
    intelligence_brief: dict[str, Any] | None = None,
) -> str:
    memory_lines = _format_memory(memory)
    lesson_lines = _format_lessons(lessons)
    issue_lines = [f"- {item}" for item in (known_issues or [])] or ["- No known issues were saved yet."]
    project_structure = project_context.get("project_structure_summary", {})

    prompt_lines = [
        "You are continuing an existing project. Do not treat this as a new beginner project.",
        "",
        f"PROJECT NAME: {project_context['project_name']}",
        f"REPO: {project_context['repo']}",
        "",
        "MAIN FOLDERS:",
        *[f"- {item}" for item in project_context["main_folders"]],
        "",
        "MAIN FILES:",
        *[f"- {item}" for item in project_context["main_files"]],
        "",
        "USER COMMAND:",
        command,
        "",
        "CURRENT KNOWN PROJECT MEMORY:",
        *memory_lines,
        "",
        "RECENT LESSONS:",
        *lesson_lines,
        "",
        "KNOWN ISSUES:",
        *issue_lines,
        "",
        "PROJECT STRUCTURE CONTEXT:",
        *[f"- {item}" for item in project_structure.get("top_level_folders", [])[:10]],
    ]

    if project_structure.get("sample_tree"):
        prompt_lines.extend(
            [
                "",
                "RECENT PROJECT STRUCTURE SAMPLE:",
                *[f"- {item}" for item in project_structure.get("sample_tree", [])[:15]],
            ]
        )

    if intelligence_brief:
        firewall = intelligence_brief.get("safety_firewall", {})
        prompt_lines.extend(
            [
                "",
                "INTELLIGENCE CENTER MODE:",
                f"- {intelligence_brief.get('title', 'Safe Research')}",
                f"- Overview: {intelligence_brief.get('overview', 'No overview provided.')}",
                f"- Status: {intelligence_brief.get('status_message', 'No status message provided.')}",
                "",
                "SAFETY FIREWALL:",
                f"- Risk level: {firewall.get('risk_level', 'moderate')}",
                *[f"- Do: {item}" for item in firewall.get("do", [])[:6]],
                *[f"- Do not: {item}" for item in firewall.get("do_not", [])[:6]],
                *[f"- Manual limit: {item}" for item in firewall.get("manual_limits", [])[:6]],
                "",
                "INTELLIGENCE RESEARCH STEPS:",
                *[f"- {item}" for item in intelligence_brief.get("research_steps", [])[:8]],
                "",
                "INTELLIGENCE EVIDENCE CHECKLIST:",
                *[f"- {item}" for item in intelligence_brief.get("evidence_checklist", [])[:8]],
                "",
                "INTELLIGENCE NEXT QUESTIONS:",
                *[f"- {item}" for item in intelligence_brief.get("next_questions", [])[:8]],
                "",
                "INTELLIGENCE OUTPUT OUTLINE:",
                *[f"- {item}" for item in intelligence_brief.get("output_outline", [])[:8]],
                "",
                "INTELLIGENCE MEMORY SIGNALS:",
                *[f"- {item}" for item in intelligence_brief.get("memory_signals", [])[:6]],
                "",
                "INTELLIGENCE LESSON SIGNALS:",
                *[f"- {item}" for item in intelligence_brief.get("lesson_signals", [])[:6]],
            ]
        )

    prompt_lines.extend(
        [
            "",
            "TASK INSTRUCTIONS:",
            "- Inspect the existing repo structure before editing.",
            "- Keep current Builder Core backend, frontend, memory, learning, and storage systems working.",
            "- Prefer extending the current project instead of rewriting everything.",
            "- Keep Cloud Run deployment compatibility.",
            "- Update documentation after code changes.",
            "",
            "LEGAL AND SAFETY INSTRUCTIONS:",
            *[f"- {item}" for item in build_legal_safe_instructions()],
            "",
            "TESTING INSTRUCTIONS:",
            "- Run frontend build if possible.",
            "- Run backend syntax or import checks if possible.",
            "- Do not claim tests passed if they were not run.",
            "",
            "REQUIRED ACCEPTANCE CHECKS:",
            *[f"- {item}" for item in build_acceptance_checks()],
            "",
            "REQUIRED FINAL SUMMARY FORMAT:",
            *[f"- {item}" for item in build_summary_requirements()],
        ]
    )

    return "\n".join(prompt_lines)


def _format_memory(memory: list[dict[str, Any]]) -> list[str]:
    if not memory:
        return ["- No project memory entries were saved yet."]

    lines: list[str] = []
    for entry in memory[:6]:
        note = str(entry.get("note") or entry.get("command") or "Saved memory")
        entry_type = str(entry.get("type") or "memory")
        lines.append(f"- [{entry_type}] {note}")
    return lines


def _format_lessons(lessons: list[dict[str, Any]]) -> list[str]:
    if not lessons:
        return ["- No lessons were saved yet."]

    lines: list[str] = []
    for lesson in lessons[:6]:
        command = str(lesson.get("command") or "Unknown task")
        lesson_text = str(lesson.get("lesson_learned") or "No lesson text saved.")
        next_step = str(lesson.get("next_recommendation") or "No next recommendation saved.")
        lines.append(f"- Command: {command}")
        lines.append(f"  Lesson: {lesson_text}")
        lines.append(f"  Next: {next_step}")
    return lines
