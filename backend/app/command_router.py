from __future__ import annotations

from typing import Any


def route_user_message(message: str, context: dict[str, Any]) -> dict[str, Any]:
    lowered = (message or "").lower()
    mode_hint = str(context.get("mode") or "auto").strip().lower()
    intents: list[str] = []

    if any(
        token in lowered
        for token in [
            "files changed",
            "what completed",
            "remaining:",
            "codex summary",
            "summary received",
            "commit hash",
            "codex final summary",
        ]
    ):
        intents.append("summary_save")
    if any(token in lowered for token in ["research", "investigate", "study", "analyze", "analyse"]):
        intents.append("research")
    if any(token in lowered for token in ["act as", "agent role", "ceo agent", "research agent", "teacher agent", "cybersecurity agent"]):
        intents.append("agent_role_request")
    if any(token in lowered for token in ["business", "profit", "virtual company", "company employees"]):
        intents.append("business_planning")
    if any(token in lowered for token in ["market", "competitor", "industry", "trend", "dispatch", "trucking"]):
        intents.append("market_analysis")
    if any(token in lowered for token in ["build app", "create app", "app idea", "mvp", "build an app"]):
        intents.append("app_builder")
    if any(token in lowered for token in ["codex prompt", "prompt", "implement", "build feature", "fix bug"]):
        intents.append("codex_prompt")
    if any(token in lowered for token in ["law", "legal", "policy", "compliance", "contract"]):
        intents.append("law_research")
    if any(token in lowered for token in ["exam", "study plan", "syllabus", "revision"]):
        intents.append("exam_planning")
    if any(token in lowered for token in ["memory", "remember", "save this"]):
        intents.append("memory_save")
    if any(token in lowered for token in ["learn from", "lesson", "update learning"]):
        intents.append("learning_update")
    if any(token in lowered for token in ["improve", "preference", "what worked", "what failed"]):
        intents.append("self_improvement")
    if any(token in lowered for token in ["storage", "firestore", "cloud storage"]):
        intents.append("storage_status")
        intents.append("cloud_storage_setup")
    if any(token in lowered for token in ["search", "find in memory", "private search"]):
        intents.append("private_search")
    if any(token in lowered for token in ["account agent", "authorized sources", "search my memory", "my sources"]):
        intents.append("account_agent_search")
    if any(token in lowered for token in ["ingest document", "save document", "document text"]):
        intents.append("document_ingest")
    if any(token in lowered for token in ["ingest url", "save url", "crawl page", "fetch page", "learn this url", "learn url"]):
        intents.append("url_ingest")
    if any(token in lowered for token in ["crawl", "crawler", "max pages", "seed urls"]):
        intents.append("crawler_plan")
    if any(token in lowered for token in ["code", "backend", "frontend", "route", "typescript", "python"]):
        intents.append("coding")
    if any(token in lowered for token in ["check security", "protect builder core", "protect system", "under attack", "security report"]):
        intents.append("security_check")
    if any(token in lowered for token in ["attack detection", "am i under attack"]):
        intents.append("attack_detection")
    if any(token in lowered for token in ["firewall", "harden firewall", "hardening"]):
        intents.append("firewall_hardening")
    if "incident report" in lowered:
        intents.append("incident_report")
    if any(token in lowered for token in ["teach me", "teacher agent", "learn python", "study python"]):
        intents.append("teaching")
    if any(token in lowered for token in ["medical", "diagnosis", "treatment"]):
        intents.append("medical_info_support")
    if any(token in lowered for token in ["finance", "trading", "investment"]):
        intents.append("finance_analysis_support")
    if any(token in lowered for token in ["engineering plan", "engineering planner", "architecture plan"]):
        intents.append("engineering_planning")

    mode_intent_map = {
        "coding": "coding",
        "research": "research",
        "market": "market_analysis",
        "law": "law_research",
        "exam": "exam_planning",
        "project": "app_builder",
        "creative": "chat",
    }
    hinted_intent = mode_intent_map.get(mode_hint)
    if hinted_intent and hinted_intent not in intents:
        intents.insert(0, hinted_intent)

    if not intents:
        intents.append("chat")

    unique_intents = list(dict.fromkeys(intents))

    workflow = "normal_chat"
    os_agent_intents = {
        "agent_role_request",
        "business_planning",
        "security_check",
        "attack_detection",
        "firewall_hardening",
        "incident_report",
        "account_agent_search",
        "teaching",
        "medical_info_support",
        "finance_analysis_support",
        "engineering_planning",
        "url_ingest",
        "crawler_plan",
    }

    if "summary_save" in unique_intents:
        workflow = "save_summary"
    elif any(intent in unique_intents for intent in os_agent_intents):
        workflow = "agent_os"
    elif "research" in unique_intents and "market_analysis" in unique_intents and "app_builder" in unique_intents:
        workflow = "research_to_app_plan"
    elif "market_analysis" in unique_intents and "app_builder" in unique_intents:
        workflow = "research_to_app_plan"
    elif "app_builder" in unique_intents:
        workflow = "app_builder"
    elif "market_analysis" in unique_intents:
        workflow = "market_analysis"
    elif "research" in unique_intents or "law_research" in unique_intents or "exam_planning" in unique_intents:
        workflow = "research_only"
    elif "codex_prompt" in unique_intents:
        workflow = "codex_prompt_only"
    elif "private_search" in unique_intents:
        workflow = "private_search"
    elif "document_ingest" in unique_intents:
        workflow = "document_ingest"
    elif "url_ingest" in unique_intents:
        workflow = "url_ingest"
    elif "crawler_plan" in unique_intents:
        workflow = "crawler_plan"
    elif "cloud_storage_setup" in unique_intents:
        workflow = "cloud_storage_setup"

    primary_intent = unique_intents[0]
    if "market_analysis" in unique_intents:
        primary_intent = "market_analysis"
    elif "app_builder" in unique_intents:
        primary_intent = "app_builder"
    elif "research" in unique_intents:
        primary_intent = "research"

    actions = [
        f"Use workflow: {workflow}",
        "Load memory and learning before responding.",
        "Save the command and important outcomes.",
    ]

    return {
        "primary_intent": primary_intent,
        "intents": unique_intents,
        "workflow": workflow,
        "confidence": "medium",
        "actions": actions,
    }
