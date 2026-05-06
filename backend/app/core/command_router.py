from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.agent_registry import select_agent
from app.core.audit_log import append_audit_entry
from app.core.response_builder import build_final_result
from app.core.security_firewall import check_risk
from app.models.command_models import CommandIntent, CommandRequest, CommandResponse, ProcessStep


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
        "research",
        (
            "research",
            "news",
            "fact-check",
            "fact check",
            "fake",
            "misinformation",
            "source",
            "internet",
            "search",
            "investigate",
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
        "decision_analysis",
        (
            "decision",
            "tradeoff",
            "trade-off",
            "scenario",
            "impact",
            "policy",
            "risk analysis",
            "analyze possible",
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


def route_command(payload: CommandRequest) -> CommandResponse:
    command_id = f"cmd_{uuid4().hex[:12]}"
    message = payload.message.strip()
    intent = classify_intent(message)
    decision = check_risk(message, intent)
    agent = select_agent(intent)
    final_result = build_final_result(intent, decision)

    needs_clarification = not bool(message)
    questions = ["What would you like Builder Core to do?"] if needs_clarification else []
    if needs_clarification:
        final_result.summary = "Builder Core needs a real command before it can classify and route the request."
        final_result.recommended_next_step = "Enter a clear command or question."

    process_steps = [
        ProcessStep(
            name="Understanding request",
            status="completed",
            summary=(
                "Needs a clearer request"
                if needs_clarification
                else f"Detected {intent.replace('_', ' ')} task"
            ),
        ),
        ProcessStep(
            name="Checking security",
            status="completed" if not decision.blocked else "blocked",
            summary=_security_summary(decision.blocked, decision.approval_required, decision.reason),
        ),
        ProcessStep(
            name="Selecting agent",
            status="completed",
            summary=f"Selected {agent.name}",
        ),
        ProcessStep(
            name="Preparing result",
            status="completed",
            summary="Prepared safe next step",
        ),
        ProcessStep(
            name="Saving audit log",
            status="completed",
            summary="Command logged",
        ),
    ]

    response = CommandResponse(
        command_id=command_id,
        needs_clarification=needs_clarification,
        questions=questions,
        process_steps=process_steps,
        final_result=final_result,
    )
    _save_audit_entry(response=response, message=message, intent=intent)
    return response


def classify_intent(message: str) -> CommandIntent:
    normalized = _normalize(message)
    for intent, keywords in INTENT_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return intent
    return "general"


def _save_audit_entry(response: CommandResponse, message: str, intent: CommandIntent) -> None:
    append_audit_entry(
        {
            "command_id": response.command_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "user_message": message,
            "detected_intent": intent,
            "selected_agent": response.final_result.selected_agent,
            "risk_level": response.final_result.risk_level,
            "approval_required": response.final_result.approval_required,
            "blocked": response.final_result.blocked,
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


def _normalize(message: str) -> str:
    return " ".join(message.lower().replace("-", " ").replace("_", " ").split())


def _model_to_dict(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[no-any-return, attr-defined]
    return model.dict()  # type: ignore[no-any-return, attr-defined]
