from __future__ import annotations

from typing import Any

from app.services import agent_service, builder_service, intent_classifier, memory_service, planner_service, tester_service


def execute_workflow(
    message: str,
    project_name: str,
    forced_intent: str | None = None,
) -> dict[str, Any]:
    clean_message = message.strip()
    clean_project_name = project_name.strip() or "Default Project"

    memory = memory_service.get_project_memory(clean_project_name)
    intent = forced_intent or intent_classifier.classify_intent(clean_message, memory)
    plan_data = planner_service.create_plan(clean_message, clean_project_name, intent, memory)

    files_created: list[str] = []
    inspection: dict[str, Any] | None = None
    run_info: dict[str, Any] | None = None

    if intent == "inspect":
        inspection = builder_service.inspect_project(clean_project_name)
        test_data = {
            "status": "success",
            "summary": "Collected project structure and route context.",
            "checks": [
                {
                    "name": "Inspection completed",
                    "passed": True,
                    "detail": f"Reviewed generated context for {clean_project_name}.",
                }
            ],
        }
    elif intent == "run":
        run_info = builder_service.get_run_info(clean_project_name)
        test_data = {
            "status": "success",
            "summary": "Prepared run commands and script paths.",
            "checks": [
                {
                    "name": "Run instructions prepared",
                    "passed": True,
                    "detail": f"Prepared commands for {clean_project_name}.",
                }
            ],
        }
    elif intent == "chat":
        test_data = {
            "status": "skipped",
            "summary": "No build action was triggered.",
            "checks": [
                {
                    "name": "Conversation only",
                    "passed": True,
                    "detail": "Returned a direct assistant response.",
                }
            ],
        }
    else:
        files_created = agent_service.generate_code(clean_message, plan_data)
        test_data = tester_service.test_result(plan_data, files_created)

    assistant_reply = agent_service.compose_assistant_reply(
        message=clean_message,
        plan_data=plan_data,
        files_created=files_created,
        test_data=test_data,
        inspection=inspection,
        run_info=run_info,
        memory=memory,
    )

    memory_snapshot = memory_service.remember_workflow(
        project_name=clean_project_name,
        task_id=f"legacy-{intent}",
        user_message=clean_message,
        assistant_reply=assistant_reply,
        intent=intent,
        plan=plan_data["plan"],
        build_result=test_data,
        module_key=plan_data.get("module_key"),
        files_created=files_created,
        inspection=inspection,
    )

    return {
        "ok": True,
        "assistant_reply": assistant_reply,
        "intent": intent,
        "project_name": clean_project_name,
        "plan": plan_data["plan"],
        "files_created": files_created,
        "test_result": test_data,
        "build_triggered": plan_data["build_triggered"],
        "module_key": plan_data.get("module_key"),
        "route_path": plan_data.get("route_path"),
        "title": plan_data.get("title"),
        "inspection": inspection,
        "run_info": run_info,
        "memory": {
            "selected_project": clean_project_name,
            "latest_generated_module": memory_snapshot.get("latest_generated_module"),
            "latest_plan": memory_snapshot.get("latest_plan", []),
            "latest_build_result": memory_snapshot.get("latest_build_result", {}),
            "latest_intent": memory_snapshot.get("latest_intent"),
            "recent_chat_history": memory_snapshot.get("recent_chat_history", []),
            "recent_patterns": memory_snapshot.get("recent_patterns", []),
            "recent_repairs": memory_snapshot.get("recent_repairs", []),
        },
    }
