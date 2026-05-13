from __future__ import annotations

from typing import Any

from app.services import builder_service


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
