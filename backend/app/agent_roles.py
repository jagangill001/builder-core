from __future__ import annotations

from typing import Any


COMMON_BLOCKED_ACTIONS = [
    "hack_back",
    "malware",
    "credential_theft",
    "doxxing",
    "dark_web_access",
    "captcha_bypass",
    "paywall_bypass",
    "autonomous_physical_control",
]

DECISION_SUPPORT_APPROVALS = [
    "external_account_action",
    "legal_filing",
    "medical_recommendation",
    "financial_decision",
    "make_trade",
    "deploy_app",
    "publish_content",
    "delete_data",
]


def _role(
    agent_id: str,
    name: str,
    purpose: str,
    allowed_tools: list[str],
    risk_level: str = "low",
    requires_approval_for: list[str] | None = None,
    disclaimer: str | None = None,
    human_approval_required: bool = False,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "name": name,
        "purpose": purpose,
        "allowed_tools": allowed_tools,
        "blocked_actions": COMMON_BLOCKED_ACTIONS,
        "requires_approval_for": requires_approval_for or [],
        "risk_level": risk_level,
        "disclaimer": disclaimer
        or "Internal planning role only. It does not perform external actions without the permission system.",
        "human_approval_required": human_approval_required,
    }


DEFAULT_AGENT_ROLES: list[dict[str, Any]] = [
    _role("ceo_agent", "CEO Agent", "Turns goals into company strategy, priorities, and operating plans.", ["private_search", "research_engine", "market_analyzer", "app_planner", "memory_manager", "self_improvement"], "medium", ["contracts", "payments", "hiring", "public_posting"]),
    _role("operations_manager_agent", "Operations Manager Agent", "Breaks work into operating checklists, tasks, and follow-up plans.", ["private_search", "research_engine", "memory_manager", "prompt_builder"], "low"),
    _role("research_agent", "Research Agent", "Researches saved/internal knowledge and identifies missing evidence.", ["private_search", "research_engine", "document_ingest", "web_ingest", "memory_manager"], "low"),
    _role("developer_agent", "Developer Agent", "Plans software changes and creates Codex-ready implementation prompts.", ["private_search", "app_planner", "prompt_builder", "storage", "self_improvement"], "medium", ["create_github_pr", "deploy_app", "modify_cloud_resources"]),
    _role("market_agent", "Market Agent", "Analyzes markets using saved knowledge and explicit assumptions.", ["private_search", "research_engine", "market_analyzer", "memory_manager"], "medium", ["financial_decision", "publish_content"]),
    _role("sales_agent", "Sales Agent", "Creates sales strategy, scripts, and customer workflows.", ["private_search", "research_engine", "prompt_builder", "memory_manager"], "medium", ["send_email", "publish_content", "external_account_action"]),
    _role("customer_support_agent", "Customer Support Agent", "Drafts support responses and internal customer-resolution steps.", ["private_search", "document_ingest", "memory_manager", "prompt_builder"], "medium", ["send_email", "customer_refund", "external_account_action"]),
    _role("teacher_agent", "Teacher Agent", "Explains concepts and builds study plans from saved knowledge.", ["private_search", "research_engine", "prompt_builder", "learning"], "low"),
    _role("cybersecurity_agent", "Cybersecurity Agent", "Provides defensive security review, monitoring, and hardening advice.", ["security_monitor", "private_search", "research_engine", "prompt_builder"], "high", ["block_ip", "change_security_policy", "modify_cloud_resources"], "Defensive only. It does not retaliate, test third-party targets, or identify people from IP data.", True),
    _role("finance_trading_analyst", "Finance Trading Analyst", "Decision-support analysis for financial topics with explicit uncertainty.", ["private_search", "research_engine", "market_analyzer"], "high", DECISION_SUPPORT_APPROVALS, "Decision-support only. It cannot place trades or make live financial decisions.", True),
    _role("legal_research_assistant", "Legal Research Assistant", "Legal research support with citations from saved sources when available.", ["private_search", "research_engine", "document_ingest"], "high", DECISION_SUPPORT_APPROVALS, "Legal information only, not legal advice or filings. A qualified professional must review real decisions.", True),
    _role("medical_info_assistant", "Medical Info Assistant", "General medical information support using saved/public user-provided sources.", ["private_search", "research_engine", "document_ingest"], "high", DECISION_SUPPORT_APPROVALS, "Medical information only, not diagnosis or treatment. A qualified clinician must review real decisions.", True),
    _role("engineering_planner", "Engineering Planner", "Plans technical systems, tradeoffs, and implementation milestones.", ["private_search", "research_engine", "app_planner", "prompt_builder"], "medium", ["deploy_app", "hardware_control"]),
    _role("firewall_defense_agent", "Firewall Defense Agent", "Reviews suspicious events and recommends defensive firewall hardening.", ["security_monitor", "private_search", "prompt_builder"], "high", ["block_ip", "change_security_policy", "modify_cloud_resources"], "Defensive only. Blocking or policy changes require human approval.", True),
    _role("incident_response_agent", "Incident Response Agent", "Summarizes incidents and creates response checklists from logged events.", ["security_monitor", "private_search", "prompt_builder"], "high", ["block_ip", "delete_data", "rotate_secrets", "change_security_policy"], "Incident response planning only unless a human approves external or destructive actions.", True),
    _role("simulation_safety_agent", "Simulation Safety Agent", "Plans safe simulations and evaluates risk boundaries.", ["private_search", "research_engine", "prompt_builder", "safety"], "high", ["vehicle_control", "aircraft_control", "defense_system_action", "hardware_control"], "Simulation and decision-support only. It cannot control real hardware, vehicles, aircraft, weapons, or medical systems.", True),
]


class AgentRoleService:
    def __init__(self) -> None:
        self._roles = {role["agent_id"]: dict(role) for role in DEFAULT_AGENT_ROLES}

    def list_roles(self) -> list[dict[str, Any]]:
        return list(self._roles.values())

    def get_role(self, agent_id: str) -> dict[str, Any] | None:
        return self._roles.get(agent_id)

    def count_roles(self) -> int:
        return len(self._roles)


def get_default_agent_roles() -> list[dict[str, Any]]:
    return [dict(role) for role in DEFAULT_AGENT_ROLES]


def get_agent_role(agent_id: str) -> dict[str, Any] | None:
    return {role["agent_id"]: role for role in DEFAULT_AGENT_ROLES}.get(agent_id)
