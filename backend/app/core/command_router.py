from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.agent_registry import select_agent
from app.core.approval_store import create_approval_request
from app.core.audit_log import append_audit_entry
from app.core.response_builder import LIVE_INTERNET_NOT_CONNECTED, build_final_result
from app.core.security_firewall import FirewallDecision, check_risk
from app.core.task_status_store import save_task_status
from app.intelligence.research_response_builder import build_research_response
from app.models.command_models import CommandIntent, CommandRequest, CommandResponse, FinalResult, ProcessStep


INTENT_KEYWORDS: tuple[tuple[CommandIntent, tuple[str, ...]], ...] = (
    (
        "security",
        (
            "security",
            "secret",
            "admin key",
            "api key",
            "credential",
            "password",
            "firewall",
            "auth",
            "permission",
            "malware",
            "phishing",
            "hack",
        ),
    ),
    (
        "cloud",
        (
            "deploy",
            "deployment",
            "production",
            "cloud",
            "server",
            "hosting",
            "cloud run",
            "domain",
            "database migration",
        ),
    ),
    (
        "research",
        (
            "research",
            "news",
            "fact-check",
            "fact check",
            "fake news",
            "fake",
            "verify this",
            "is this true",
            "what happened before",
            "what happened after",
            "before and after",
            "timeline",
            "election",
            "social media manipulation",
            "propaganda",
            "future effect",
            "impact of event",
            "policy effect",
            "misinformation",
            "disinformation",
            "source",
            "internet",
            "search",
            "investigate",
        ),
    ),
    (
        "decision_analysis",
        (
            "decision",
            "tradeoff",
            "trade-off",
            "scenario",
            "business impact",
            "policy impact",
            "school policy",
            "risk analysis",
            "analyze possible",
            "public risk",
        ),
    ),
    (
        "coding",
        (
            "code",
            "coding",
            "frontend",
            "backend",
            "bug",
            "fix",
            "repo",
            "component",
            "api",
            "endpoint",
            "fastapi",
            "next.js",
            "nextjs",
            "test",
            "build",
            "typescript",
            "python",
        ),
    ),
    (
        "customer_service",
        (
            "customer service",
            "support ticket",
            "refund",
            "complaint",
            "customer email",
            "reply to customer",
        ),
    ),
    (
        "business",
        (
            "business",
            "revenue",
            "pricing",
            "market",
            "competitor",
            "sales",
            "budget",
            "roi",
            "customer",
        ),
    ),
    (
        "teaching",
        (
            "teach",
            "explain",
            "learn",
            "lesson",
            "tutor",
            "how does",
            "what is",
        ),
    ),
)

LIVE_INTELLIGENCE_INTENTS: set[CommandIntent] = {"research", "decision_analysis"}


def route_command(payload: CommandRequest) -> CommandResponse:
    command_id = f"cmd_{uuid4().hex[:12]}"
    message = payload.message.strip()
    intent = classify_intent(message)
    decision = check_risk(message, intent)
    agent = select_agent(intent)
    needs_clarification = not bool(message)
    questions = ["What would you like Builder Core to do?"] if needs_clarification else []

    intelligence_result = None
    if message and should_use_live_search(message, intent) and not decision.blocked:
        intelligence_result = build_research_response(message)

    approval_request = None
    if message and decision.approval_required and not decision.blocked:
        approval_request = create_approval_request(
            command_id=command_id,
            action=_approval_action_for(message, intent),
            reason=decision.reason,
            risk_level=decision.risk_level,
        )

    final_result = build_final_result(
        intent=intent,
        decision=decision,
        intelligence_result=intelligence_result,
        approval_request=approval_request,
    )

    if needs_clarification:
        final_result.summary = "Builder Core needs a real command before it can classify and route the request."
        final_result.recommended_next_step = "Enter a clear command or question."

    process_steps = _build_process_steps(
        intent=intent,
        decision=decision,
        selected_agent=agent.name,
        needs_clarification=needs_clarification,
        intelligence_result=intelligence_result,
    )

    task_status = _build_task_status(
        command_id=command_id,
        message=message,
        intent=intent,
        decision=decision,
        selected_agent=agent.name,
        intelligence_result=intelligence_result,
        approval_request=approval_request,
        needs_clarification=needs_clarification,
        final_result=final_result,
    )
    save_task_status(task_status)

    response = CommandResponse(
        command_id=command_id,
        needs_clarification=needs_clarification,
        questions=questions,
        process_steps=process_steps,
        final_result=final_result,
        task_status=task_status,
    )
    _save_audit_entry(response=response, message=message, intent=intent, task_status=task_status)
    return response


def classify_intent(message: str) -> CommandIntent:
    normalized = _normalize(message)
    for intent, keywords in INTENT_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "general"


def _build_process_steps(
    *,
    intent: CommandIntent,
    decision: FirewallDecision,
    selected_agent: str,
    needs_clarification: bool,
    intelligence_result: dict | None,
) -> list[ProcessStep]:
    steps = [
        ProcessStep(
            name="Understanding request",
            status="completed",
            summary="Needs a clearer request" if needs_clarification else f"Detected {intent.replace('_', ' ')} task",
        ),
        ProcessStep(
            name="Checking security",
            status="completed" if not decision.blocked else "blocked",
            summary=_security_summary(decision.blocked, decision.approval_required, decision.reason),
        ),
        ProcessStep(
            name="Selecting agent",
            status="completed",
            summary=f"Selected {selected_agent}",
        ),
    ]

    if intelligence_result is not None:
        live_search_connected = bool(intelligence_result.get("search_connected") or intelligence_result.get("live_search_connected"))
        steps.append(
            ProcessStep(
                name="Searching DuckDuckGo",
                status="completed",
                summary="Search completed" if live_search_connected else LIVE_INTERNET_NOT_CONNECTED,
            )
        )
        sources = list(intelligence_result.get("sources") or [])
        opened_count = len([source for source in sources if isinstance(source, dict) and source.get("opened")])
        steps.append(
            ProcessStep(
                name="Reading allowed sources",
                status="completed",
                summary=f"Opened {opened_count} allowed source page(s)" if sources else "No source pages available to open",
            )
        )
        steps.append(
            ProcessStep(
                name="Saving safe memory",
                status="completed",
                summary="Memory saved" if intelligence_result.get("memory_saved") else "No memory saved",
            )
        )

    if decision.approval_required and not decision.blocked:
        steps.append(
            ProcessStep(
                name="Waiting for approval",
                status="completed",
                summary="Approval record created. No action executed.",
            )
        )

    steps.extend(
        [
            ProcessStep(
                name="Preparing result",
                status="completed",
                summary="Prepared safe next step",
            ),
            ProcessStep(
                name="Saving status",
                status="completed",
                summary="Command status saved",
            ),
            ProcessStep(
                name="Saving audit log",
                status="completed",
                summary="Command logged",
            ),
        ]
    )
    return steps


def _build_task_status(
    *,
    command_id: str,
    message: str,
    intent: CommandIntent,
    decision: FirewallDecision,
    selected_agent: str,
    intelligence_result: dict | None,
    approval_request: dict | None,
    needs_clarification: bool,
    final_result: FinalResult,
) -> dict:
    now = datetime.now(UTC).isoformat()
    current_status = "completed"
    if needs_clarification:
        current_status = "failed"
    elif decision.blocked:
        current_status = "blocked"
    elif approval_request:
        current_status = "waiting_for_approval"
    elif intelligence_result is not None and not (intelligence_result.get("search_connected") or intelligence_result.get("live_search_connected")):
        current_status = "search_unavailable"

    steps = [
        {"code": "received", "status": "received", "summary": "Command received by backend.", "at": now},
        {"code": "understanding", "status": "completed", "summary": f"Detected {intent.replace('_', ' ')} task", "at": now},
        {"code": "security_check", "status": "blocked" if decision.blocked else "completed", "summary": decision.reason, "at": now},
        {"code": "agent_selected", "status": "completed", "summary": selected_agent, "at": now},
    ]
    if approval_request:
        steps.append({"code": "waiting_for_approval", "status": "waiting_for_approval", "summary": approval_request["approval_id"], "at": now})
    if intelligence_result is not None:
        if intelligence_result.get("search_connected") or intelligence_result.get("live_search_connected"):
            steps.append({"code": "search_answer", "status": "completed", "summary": "DuckDuckGo search answer prepared.", "at": now})
        else:
            steps.append({"code": "search_unavailable", "status": "search_unavailable", "summary": LIVE_INTERNET_NOT_CONNECTED, "at": now})
    steps.append({"code": current_status, "status": current_status, "summary": "No fake progress percentages are used.", "at": now})

    return {
        "command_id": command_id,
        "status": current_status,
        "message": message,
        "detected_intent": intent,
        "selected_agent": selected_agent,
        "approval_required": bool(approval_request),
        "approval_id": approval_request.get("approval_id") if approval_request else None,
        "blocked": decision.blocked,
        "created_at": now,
        "updated_at": now,
        "steps": steps,
        "final_result": _model_to_dict(final_result),
    }


def _save_audit_entry(response: CommandResponse, message: str, intent: CommandIntent, task_status: dict) -> None:
    append_audit_entry(
        {
            "command_id": response.command_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "user_message": message,
            "detected_intent": intent,
            "selected_agent": response.final_result.selected_agent,
            "risk_level": response.final_result.risk_level,
            "approval_required": response.final_result.approval_required,
            "approval_id": response.final_result.approval_request.get("approval_id") if response.final_result.approval_request else None,
            "blocked": response.final_result.blocked,
            "task_status": task_status.get("status"),
            "process_steps": [_model_to_dict(step) for step in response.process_steps],
            "final_summary": response.final_result.summary,
        }
    )


def _security_summary(blocked: bool, approval_required: bool, reason: str) -> str:
    if blocked:
        return f"Blocked unsafe action: {reason}"
    if approval_required:
        return f"Approval required: {reason}"
    return reason


def _approval_action_for(message: str, intent: CommandIntent) -> str:
    normalized = _normalize(message)
    if "deploy" in normalized or "production" in normalized:
        return "deploy_to_production"
    if "database" in normalized or "delete data" in normalized:
        return "database_or_data_change"
    if "secret" in normalized or "admin key" in normalized or "api key" in normalized:
        return "secret_or_admin_key_change"
    if "spend" in normalized or "budget" in normalized or "finance" in normalized:
        return "finance_or_budget_action"
    if "sandbox" in normalized:
        return "sandbox_execution_review"
    return f"{intent}_approval"


def should_use_live_search(message: str, intent: CommandIntent) -> bool:
    normalized = _normalize(message)
    if not normalized:
        return False
    if intent in LIVE_INTELLIGENCE_INTENTS:
        return True

    research_markers = (
        "latest",
        "current",
        "today",
        "recent",
        "new docs",
        "documentation",
        "docs",
        "release",
        "version",
        "what happened",
        "verify",
        "source check",
        "fact check",
        "is this true",
        "fake news",
        "research",
    )
    if any(marker in normalized for marker in research_markers):
        return True

    question_starters = (
        "what is",
        "who is",
        "when did",
        "when is",
        "where is",
        "why is",
        "how does",
        "how do",
        "explain",
    )
    if normalized.endswith("?") and any(normalized.startswith(starter) for starter in question_starters):
        return True

    if intent in {"coding", "teaching", "business", "general"} and normalized.endswith("?"):
        return True

    return False


def _normalize(message: str) -> str:
    return " ".join(message.lower().replace("-", " ").replace("_", " ").split())


def _model_to_dict(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[no-any-return, attr-defined]
    return model.dict()  # type: ignore[no-any-return, attr-defined]
