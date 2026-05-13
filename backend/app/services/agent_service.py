from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services import builder_service


def classify_intent(message: str, memory: dict[str, Any] | None = None) -> str:
    text = message.lower().strip()
    if not text:
        return "chat"

    if any(
        phrase in text
        for phrase in (
            "how do i run",
            "run this app",
            "launch instructions",
            "prepare run command",
            "start the app",
        )
    ):
        return "run"

    if any(
        phrase in text
        for phrase in (
            "show project files",
            "inspect current module registry",
            "what routes exist",
            "inspect",
            "project structure",
            "module registry",
        )
    ):
        return "inspect"

    if any(keyword in text for keyword in ("modify", "update", "add ", "change", "extend", "edit", "improve", "fix ")):
        return "modify"

    if any(keyword in text for keyword in ("build", "create", "make", "generate")):
        return "build"

    if "current app" in text and memory and memory.get("latest_generated_module"):
        return "modify"

    return "chat"


def _build_steps(module_key: str, intent: str) -> list[str]:
    action = "Build" if intent == "build" else "Update"
    library = {
        "booking_page": [
            f"{action} the booking workflow UI",
            "Add appointment capture fields and a visible schedule list",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
        "notes_page": [
            f"{action} the notes module UI",
            "Support add, edit, and delete note interactions",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
        "vendor_dashboard": [
            f"{action} the vendor comparison dashboard",
            "Add filtering and quote comparison scaffolding",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
        "login_page": [
            f"{action} the login entry point",
            "Add a simple credential form scaffold",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
        "dashboard_page": [
            f"{action} the dashboard surface",
            "Add summary cards and activity chart placeholders",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
        "generic_module": [
            f"{action} the requested module scaffold",
            "Create or update the page starter",
            "Refresh the generated project shell navigation",
            "Write manifest and registry updates",
            "Run structural validation checks",
        ],
    }
    return library.get(module_key, library["generic_module"])


def create_plan(
    message: str,
    project_name: str,
    intent: str,
    memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memory = memory or {}

    if intent in {"chat", "inspect", "run"}:
        intent_steps = {
            "chat": [
                "Read the current request",
                "Use project-aware memory to answer naturally",
                "Return a clear assistant response",
            ],
            "inspect": [
                "Load project registry and generated files",
                "Collect routes and manifest context",
                "Return a concise inspection summary",
            ],
            "run": [
                "Load the generated project path",
                "Prepare install and dev commands",
                "Return run instructions",
            ],
        }
        return {
            "intent": intent,
            "project_name": project_name,
            "module_key": None,
            "route_path": None,
            "title": None,
            "plan": intent_steps[intent],
            "summary": f"Handled this as a {intent} request.",
            "build_triggered": False,
        }

    fallback_module_key = memory.get("latest_generated_module") if intent == "modify" else None
    blueprint = builder_service.resolve_module_blueprint(message, fallback_module_key)

    return {
        "intent": intent,
        "project_name": project_name,
        "module_key": blueprint["module_key"],
        "route_path": blueprint["route_path"],
        "title": blueprint["title"],
        "plan": _build_steps(blueprint["module_key"], intent),
        "summary": f"Prepared a {intent} plan for {blueprint['title']}.",
        "build_triggered": True,
    }


def generate_code(message: str, plan_data: dict[str, Any]) -> list[str]:
    if not plan_data.get("build_triggered"):
        return []

    project_name = plan_data["project_name"]
    module_key = plan_data["module_key"]
    route_path = plan_data["route_path"]
    title = plan_data["title"]

    created_files = builder_service.generate_module_files(project_name, module_key, message)
    registry_file = builder_service.update_module_registry(project_name, module_key, route_path, title)
    shell_files = builder_service.build_project_shell(project_name)
    manifest_file = builder_service.write_manifest(
        project_name=project_name,
        module_key=module_key,
        instruction=message,
        created_files=created_files,
        plan=plan_data["plan"],
        route_path=route_path,
        title=title,
        intent=plan_data["intent"],
    )

    all_files = created_files + [registry_file, manifest_file] + shell_files
    return list(dict.fromkeys(all_files))


def test_result(plan_data: dict[str, Any], files_created: list[str]) -> dict[str, Any]:
    if not plan_data.get("build_triggered"):
        return {
            "status": "skipped",
            "summary": "No build validation was needed.",
            "checks": [
                {
                    "name": "Workflow routing",
                    "passed": True,
                    "detail": "The request did not require code generation.",
                }
            ],
        }

    project_name = plan_data["project_name"]
    module_key = plan_data["module_key"]
    route_path = plan_data["route_path"]

    checks = []

    generated_files_ok = all(Path(file_path).exists() for file_path in files_created)
    checks.append(
        {
            "name": "Generated files exist",
            "passed": generated_files_ok,
            "detail": f"Verified {len(files_created)} file references.",
        }
    )

    route_file = builder_service.route_file_path(project_name, route_path)
    checks.append(
        {
            "name": "Module route file exists",
            "passed": route_file.exists(),
            "detail": str(route_file),
        }
    )

    registry = builder_service.read_registry(project_name)
    registry_ok = any(module.get("module_key") == module_key for module in registry.get("modules", []))
    checks.append(
        {
            "name": "Module registry updated",
            "passed": registry_ok,
            "detail": f"Registry contains {module_key}.",
        }
    )

    manifest_file = builder_service.manifest_path(project_name, module_key)
    checks.append(
        {
            "name": "Manifest file updated",
            "passed": manifest_file.exists(),
            "detail": str(manifest_file),
        }
    )

    shell_dir = builder_service.app_root(project_name, create=False)
    shell_ok = (shell_dir / "layout.tsx").exists() and (shell_dir / "page.tsx").exists()
    checks.append(
        {
            "name": "Project shell preserved",
            "passed": shell_ok,
            "detail": f"Checked shell files in {shell_dir}.",
        }
    )

    passed_checks = sum(1 for check in checks if check["passed"])
    status = "success" if passed_checks == len(checks) else "failed"
    return {
        "status": status,
        "summary": f"{passed_checks}/{len(checks)} structural checks passed.",
        "checks": checks,
    }


def compose_assistant_reply(
    message: str,
    plan_data: dict[str, Any],
    files_created: list[str],
    test_data: dict[str, Any],
    inspection: dict[str, Any] | None = None,
    run_info: dict[str, Any] | None = None,
    memory: dict[str, Any] | None = None,
) -> str:
    intent = plan_data["intent"]
    project_name = plan_data["project_name"]
    memory = memory or {}

    if intent == "chat":
        text = message.lower()
        if "what can you do" in text:
            return (
                "I can act as the chat, planner, coder, tester, and executor for Builder Core. "
                "Ask me to build, modify, inspect, or run a project and I will route the request, generate or update files, "
                "run structural checks, and report the result."
            )

        if "explain" in text or "understand" in text:
            latest_module = memory.get("latest_generated_module") or "no module yet"
            return (
                f"Builder Core is set up as a lightweight autonomous builder around the selected project {project_name}. "
                f"It keeps project memory, can inspect generated routes and files, and most recently worked with {latest_module}."
            )

        return (
            f"I treated this as a conversation request for {project_name}. "
            "Tell me what you want to build or change and I will route it through the planner, coder, tester, and executor workflow."
        )

    if intent == "inspect" and inspection is not None:
        summary = inspection.get("summary", {})
        routes = inspection.get("routes", [])
        return (
            f"I inspected {project_name}. I found {summary.get('module_count', 0)} registered module(s), "
            f"{summary.get('file_count', 0)} generated file(s), and routes such as {', '.join(routes[:5])}."
        )

    if intent == "run" and run_info is not None:
        return (
            f"I prepared run instructions for {project_name}. "
            "Use the listed commands to install dependencies and launch the generated Next.js app."
        )

    route_path = plan_data.get("route_path") or "/module"
    title = plan_data.get("title") or "module"
    action = "built" if intent == "build" else "updated"
    return (
        f"I classified this as a {intent} request for {project_name}, {action} the {title} module at {route_path}, "
        f"and verified the result with {test_data['summary'].lower()} I also refreshed the project shell and manifest."
    )
