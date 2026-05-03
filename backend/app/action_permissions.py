from __future__ import annotations

from typing import Any


ACTION_LEVELS = [
    "read_only",
    "memory_write",
    "internal_write",
    "external_write_requires_confirmation",
    "high_risk_requires_confirmation",
    "destructive_action_blocked_by_default",
]

ALLOWED_ACTIONS = {
    "search_memory": "Search saved Builder Core memory.",
    "search_private_index": "Search the private index.",
    "save_memory": "Save memory when the user explicitly requested it.",
    "ingest_pasted_notes": "Ingest pasted notes.",
    "ingest_safe_public_url": "Ingest one user-provided safe public URL.",
    "create_internal_task": "Create an internal task.",
    "generate_plan": "Generate a plan.",
    "generate_codex_prompt": "Generate a Codex prompt.",
    "generate_incident_report": "Generate an incident report.",
    "normal_chat": "Answer using internal context.",
    "private_search": "Search saved private knowledge.",
    "document_ingest": "Ingest user-provided text.",
    "url_ingest": "Ingest one safe public URL.",
    "crawler_plan": "Create a crawler plan only.",
}

CONFIRMATION_ACTIONS = {
    "send_email",
    "post_online",
    "make_trade",
    "execute_financial_decision",
    "financial_decision",
    "create_legal_filing",
    "legal_filing",
    "provide_medical_recommendation",
    "medical_recommendation",
    "issue_customer_refund",
    "customer_refund",
    "deploy_app",
    "create_github_pr",
    "modify_cloud_resources",
    "block_ip",
    "delete_data",
    "rotate_secrets",
    "change_security_policy",
    "external_account_action",
    "hardware_control",
    "vehicle_control",
    "aircraft_control",
    "defense_system_action",
    "publish_content",
}

BLOCKED_ACTIONS = {
    "hacking",
    "hack_back",
    "malware",
    "data_theft",
    "bypass_login",
    "bypass_captcha",
    "scrape_private_pages",
    "access_dark_web",
    "steal_tokens",
    "steal_passwords",
    "credential_theft",
    "doxxing",
    "autonomous_weapon_action",
    "autonomous_weapons",
    "unsafe_vehicle_control",
    "unsafe_aircraft_control",
    "paywall_bypass",
    "hidden_surveillance",
}

BLOCKED_KEYWORDS = {
    "bypass captcha": "CAPTCHA bypass is blocked.",
    "captcha bypass": "CAPTCHA bypass is blocked.",
    "steal token": "Credential theft is blocked.",
    "steal password": "Credential theft is blocked.",
    "exfiltrate": "Data theft is blocked.",
    "malware": "Malware creation or deployment is blocked.",
    "ransomware": "Malware creation or deployment is blocked.",
    "hack back": "Hack-back and retaliation are blocked.",
    "dark web": "Dark web access is blocked.",
    ".onion": "Dark web access is blocked.",
    "dox": "Doxxing is blocked.",
    "bypass login": "Login bypass is blocked.",
    "paywall bypass": "Paywall bypass is blocked.",
    "private scraping": "Private-page scraping is blocked.",
}


def _normalize_action(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_").replace("-", "_")


def check_action_permission(action_type: str, action_description: str = "") -> dict[str, Any]:
    normalized = _normalize_action(action_type)
    lowered_description = (action_description or "").lower()

    if normalized in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "requires_confirmation": False,
            "blocked": True,
            "risk_level": "critical",
            "action_level": "destructive_action_blocked_by_default",
            "reason": "This action is blocked by default because it could enable harm, intrusion, deception, or unsafe control.",
        }

    for keyword, reason in BLOCKED_KEYWORDS.items():
        if keyword in lowered_description:
            return {
                "allowed": False,
                "requires_confirmation": False,
                "blocked": True,
                "risk_level": "critical",
                "action_level": "destructive_action_blocked_by_default",
                "reason": reason,
            }

    if normalized in CONFIRMATION_ACTIONS:
        return {
            "allowed": False,
            "requires_confirmation": True,
            "blocked": False,
            "risk_level": "high",
            "action_level": "high_risk_requires_confirmation",
            "reason": "This action affects external systems, money, accounts, safety, legal status, or data and requires human confirmation.",
        }

    if normalized in ALLOWED_ACTIONS:
        action_level = "read_only"
        if normalized in {"save_memory", "ingest_pasted_notes", "ingest_safe_public_url"}:
            action_level = "memory_write"
        if normalized in {"create_internal_task", "generate_codex_prompt", "generate_incident_report"}:
            action_level = "internal_write"
        return {
            "allowed": True,
            "requires_confirmation": False,
            "blocked": False,
            "risk_level": "low",
            "action_level": action_level,
            "reason": ALLOWED_ACTIONS[normalized],
        }

    if any(word in lowered_description for word in ["trade", "medical", "legal filing", "refund", "deploy", "delete"]):
        return {
            "allowed": False,
            "requires_confirmation": True,
            "blocked": False,
            "risk_level": "high",
            "action_level": "high_risk_requires_confirmation",
            "reason": "The description looks high-risk and needs human confirmation before any real-world action.",
        }

    return {
        "allowed": True,
        "requires_confirmation": False,
        "blocked": False,
        "risk_level": "medium",
        "action_level": "internal_write",
        "reason": "Unknown action types are limited to internal planning unless a stricter permission check is added.",
    }
