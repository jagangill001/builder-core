from __future__ import annotations

from typing import Any

from app.core.agent_registry import select_agent
from app.core.security_firewall import FirewallDecision
from app.models.command_models import CommandIntent, FinalResult

LIVE_INTERNET_NOT_CONNECTED = "DuckDuckGo search is not available right now."


def build_final_result(
    intent: CommandIntent,
    decision: FirewallDecision,
    intelligence_result: dict[str, Any] | None = None,
    approval_request: dict[str, Any] | None = None,
) -> FinalResult:
    agent = select_agent(intent)

    if decision.blocked:
        return FinalResult(
            type=intent,
            summary=f"Builder Core cannot help with that action. {decision.reason}",
            selected_agent=agent.name,
            risk_level="blocked",
            approval_required=False,
            blocked=True,
            recommended_next_step=decision.recommended_next_step,
        )

    if intelligence_result is not None:
        answer = str(intelligence_result.get("answer") or intelligence_result.get("summary") or LIVE_INTERNET_NOT_CONNECTED)
        return FinalResult(
            type=intent,
            summary=answer,
            selected_agent=agent.name,
            risk_level=decision.risk_level,
            approval_required=decision.approval_required,
            blocked=False,
            recommended_next_step=str(intelligence_result.get("recommended_next_step") or decision.recommended_next_step),
            approval_request=approval_request,
            sources=list(intelligence_result.get("sources", [])),
            facts=list(intelligence_result.get("facts", [])),
            claims=list(intelligence_result.get("claims", [])),
            unknowns=list(intelligence_result.get("unknowns", [])),
            timeline=dict(intelligence_result.get("timeline") or {}),
            manipulation_risk=dict(intelligence_result.get("manipulation_risk") or {}),
            future_scenarios=list(intelligence_result.get("future_scenarios", [])),
            confidence=str(intelligence_result.get("confidence") or "low"),
            missing_data=[str(item) for item in intelligence_result.get("missing_data", [])],
            answer=answer,
            search_connected=bool(intelligence_result.get("search_connected") or intelligence_result.get("live_search_connected")),
            warnings=[str(item) for item in intelligence_result.get("warnings", [])],
            memory_saved=bool(intelligence_result.get("memory_saved")),
        )

    if decision.approval_required:
        return FinalResult(
            type=intent,
            summary=(
                f"{_intent_label(intent)} request received. {decision.reason} "
                "Builder Core created an approval record and did not execute the action."
            ),
            selected_agent=agent.name,
            risk_level=decision.risk_level,
            approval_required=True,
            blocked=False,
            recommended_next_step=decision.recommended_next_step,
            approval_request=approval_request,
        )

    summary, next_step = _safe_result_text(intent)
    return FinalResult(
        type=intent,
        summary=summary,
        selected_agent=agent.name,
        risk_level=decision.risk_level,
        approval_required=False,
        blocked=False,
        recommended_next_step=next_step,
    )


def _safe_result_text(intent: CommandIntent) -> tuple[str, str]:
    if intent == "coding":
        return (
            "This is a coding task. Builder Core prepared safe instructions for the coding agent.",
            "Use Codex to inspect the relevant files and create a real fix.",
        )
    if intent == "research":
        return (
            "This is a research task. DuckDuckGo search is not available right now, so Builder Core can only prepare a research plan and source-checking approach.",
            "Verify claims with real sources outside Builder Core until DuckDuckGo search is available.",
        )
    if intent == "security":
        return (
            "This is a security task. Builder Core can explain risks and prepare safe defensive review steps.",
            "Review the security concern without exposing secrets or bypassing controls.",
        )
    if intent == "cloud":
        return (
            "This is a cloud task. Builder Core can prepare deployment guidance, but real cloud actions require approval.",
            "Review environment, secrets, rollback, and cost impact before approving any cloud action.",
        )
    if intent == "business":
        return (
            "This is a business planning task. Builder Core prepared a safe analysis response.",
            "Use the result for planning and involve a human before business-critical decisions.",
        )
    if intent == "teaching":
        return (
            "This is a teaching task. Builder Core prepared an educational explanation path.",
            "Continue with a step-by-step explanation or ask for examples.",
        )
    if intent == "customer_service":
        return (
            "This is a customer service task. Builder Core can prepare draft guidance, but it will not send messages without approval.",
            "Review the draft or plan before any customer-facing action.",
        )
    if intent == "decision_analysis":
        return (
            "This is a decision analysis task. Builder Core prepared a safe planning and risk-analysis response.",
            "Use the analysis as support only and involve responsible humans before action.",
        )
    return (
        "This is a general safe request. Builder Core prepared an assistant-style response.",
        "Continue with safe planning, explanation, or analysis.",
    )


def _intent_label(intent: CommandIntent) -> str:
    return intent.replace("_", " ")
