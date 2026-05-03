from __future__ import annotations

import re
from typing import Any

try:
    from app.message_normalizer import normalize_message, remove_domains_from_message
except ImportError:
    from message_normalizer import normalize_message, remove_domains_from_message


def route_user_message(message: str, context: dict[str, Any]) -> dict[str, Any]:
    normalization = normalize_message(message)
    normalized_message = str(normalization.get("normalized_message") or message or "")
    lowered = normalized_message.lower()
    domain = str(normalization.get("domain") or "")
    domain_search_requested = bool(normalization.get("learned_domain_request") or normalization.get("learned_domain_list_request"))
    intent_text = remove_domains_from_message(normalized_message).lower()
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
    if re.search(r"\b(exam|study plan|syllabus|revision)\b", intent_text):
        intents.append("exam_planning")
    url_found = bool(re.search(r"https?://[^\s<>\"]+", normalized_message or ""))
    memory_prefixes = [
        "remember this:",
        "learn this:",
        "learn this note:",
        "save this:",
        "save this to memory:",
        "add this to knowledge:",
        "study this:",
        "teach yourself this:",
        "ingest this note:",
    ]
    knowledge_search_phrases = [
        "search your knowledge for",
        "what do you know about",
        "use your knowledge to",
        "build knowledge about",
    ]
    url_learning_phrases = [
        "learn this url",
        "learn this http",
        "learn this https",
        "ingest this url",
        "remember this website",
        "save this url",
        "study this page",
    ]

    if domain_search_requested:
        intents.append("domain_search")
        intents.append("knowledge_search")
    if any(token in lowered for token in ["memory", "remember", "save this"]):
        intents.append("memory_save")
    if any(prefix in lowered for prefix in memory_prefixes):
        intents.append("knowledge_add")
    if any(phrase in lowered for phrase in knowledge_search_phrases):
        intents.append("knowledge_search")
    if not domain_search_requested and any(token in lowered for token in ["learn from", "lesson", "update learning"]):
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
    if url_found and any(phrase in lowered for phrase in url_learning_phrases):
        intents.append("url_learning")
    if any(token in lowered for token in ["crawl", "crawler", "max pages", "seed urls"]):
        intents.append("crawler_plan")
    if any(token in lowered for token in ["code", "backend", "frontend", "route", "typescript", "python"]):
        intents.append("coding")
    security_phrases = [
        "check security",
        "protect builder core",
        "protect system",
        "system safety",
        "security report",
        "security status",
        "security monitor",
        "security events",
        "harden system",
        "firewall",
        "rate limiter",
        "incident report",
        "protect my backend",
        "protect my app",
    ]
    if any(token in lowered for token in security_phrases) or ("security" in lowered and any(token in lowered for token in ["check", "protect", "protected", "status", "report"])):
        intents.append("security_check")
    if any(token in lowered for token in ["protect builder core", "protect system", "system safety", "protect my backend", "protect my app", "system is protected"]):
        intents.append("system_protection")
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
    if any(token in lowered for token in ["roadmap", "next update", "next updates", "what are next updates", "what are next update"]):
        intents.append("roadmap_request")

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
        "system_protection",
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
    elif "security_check" in unique_intents or "system_protection" in unique_intents:
        workflow = "incident_report" if "incident_report" in unique_intents else "security_check"
    elif "domain_search" in unique_intents:
        workflow = "domain_search"
    elif "url_learning" in unique_intents:
        workflow = "url_learning"
    elif "knowledge_add" in unique_intents:
        workflow = "knowledge_add"
    elif "knowledge_search" in unique_intents:
        workflow = "knowledge_search"
    elif "roadmap_request" in unique_intents:
        workflow = "roadmap"
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
    if "security_check" in unique_intents:
        primary_intent = "security_check"
    elif "knowledge_add" in unique_intents:
        primary_intent = "knowledge_add"
    elif "domain_search" in unique_intents:
        primary_intent = "domain_search"
    elif "knowledge_search" in unique_intents:
        primary_intent = "knowledge_search"
    elif "url_learning" in unique_intents:
        primary_intent = "url_learning"
    elif "roadmap_request" in unique_intents:
        primary_intent = "roadmap_request"
    elif "market_analysis" in unique_intents:
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
        "confidence": "high" if workflow in {"security_check", "knowledge_add", "knowledge_search", "url_learning", "domain_search"} else "medium",
        "actions": actions,
        "original_message": normalization.get("original_message", message),
        "normalized_message": normalized_message,
        "normalization": normalization,
        "domain": domain,
    }
