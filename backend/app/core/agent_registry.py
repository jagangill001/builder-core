from __future__ import annotations

from app.models.command_models import AgentDefinition, CommandIntent


AGENTS: dict[str, AgentDefinition] = {
    "manager_agent": AgentDefinition(
        name="manager_agent",
        purpose="Coordinates the request and combines results.",
        allowed_tasks=[
            "classify requests",
            "coordinate safe internal steps",
            "prepare final user-facing summaries",
        ],
        blocked_tasks=[
            "execute real-world actions without approval",
            "bypass security controls",
            "expose hidden system details",
        ],
        requires_approval_for=[
            "production deployment",
            "business-critical decisions",
            "database changes",
        ],
    ),
    "codex_builder_agent": AgentDefinition(
        name="codex_builder_agent",
        purpose="Prepares coding/build instructions.",
        allowed_tasks=[
            "prepare coding plans",
            "summarize implementation steps",
            "suggest safe file inspection",
        ],
        blocked_tasks=[
            "claim Codex direct execution when it is not connected",
            "hide secrets in frontend code",
            "write malware or credential theft code",
        ],
        requires_approval_for=[
            "production code deployment",
            "secret/admin key changes",
            "database changes",
            "deleting data",
        ],
    ),
    "research_agent": AgentDefinition(
        name="research_agent",
        purpose="Prepares research plans. Must say live search is not connected if no real search exists.",
        allowed_tasks=[
            "prepare research questions",
            "outline verification plans",
            "explain source-quality checks",
        ],
        blocked_tasks=[
            "invent sources",
            "create fake news",
            "run propaganda campaigns",
            "secretly manipulate public opinion",
        ],
        requires_approval_for=[
            "public policy analysis that affects real action",
            "finance-related actions",
            "business-critical decisions",
        ],
    ),
    "security_agent": AgentDefinition(
        name="security_agent",
        purpose="Checks security risks and unsafe requests.",
        allowed_tasks=[
            "explain security risks",
            "prepare safe review plans",
            "classify unsafe commands",
        ],
        blocked_tasks=[
            "steal credentials",
            "bypass security",
            "phishing",
            "unauthorized hacking",
            "malware",
        ],
        requires_approval_for=[
            "firewall changes",
            "cloud security changes",
            "secret/admin key changes",
        ],
    ),
    "cloud_agent": AgentDefinition(
        name="cloud_agent",
        purpose="Prepares cloud/deployment guidance. Real deploys require approval.",
        allowed_tasks=[
            "prepare deployment checklists",
            "explain cloud risks",
            "outline rollback planning",
        ],
        blocked_tasks=[
            "deploy without approval",
            "change cloud security without approval",
            "expose secrets",
        ],
        requires_approval_for=[
            "production deployment",
            "cloud security changes",
            "database changes",
            "spending money",
        ],
    ),
    "business_agent": AgentDefinition(
        name="business_agent",
        purpose="Provides business planning and analysis.",
        allowed_tasks=[
            "business planning",
            "market framing",
            "impact analysis",
            "scenario planning",
        ],
        blocked_tasks=[
            "manipulate voters or public opinion",
            "create fake engagement",
            "make final financial decisions",
        ],
        requires_approval_for=[
            "budget decisions",
            "business-critical decisions",
            "finance-related actions",
        ],
    ),
    "tutor_agent": AgentDefinition(
        name="tutor_agent",
        purpose="Explains topics and teaches step by step.",
        allowed_tasks=[
            "educational explanations",
            "step-by-step teaching",
            "safe examples",
        ],
        blocked_tasks=[
            "teach illegal evasion",
            "give unsafe professional decisions",
            "provide harmful operational instructions",
        ],
        requires_approval_for=[
            "medical action plans",
            "legal action plans",
            "financial action plans",
        ],
    ),
    "general_assistant_agent": AgentDefinition(
        name="general_assistant_agent",
        purpose="Handles general safe requests.",
        allowed_tasks=[
            "answer general questions",
            "prepare safe plans",
            "summarize user requests",
        ],
        blocked_tasks=[
            "illegal or harmful actions",
            "unsafe real-world control",
            "security bypasses",
        ],
        requires_approval_for=[
            "sending emails",
            "spending money",
            "deleting data",
        ],
    ),
}


INTENT_TO_AGENT: dict[CommandIntent, str] = {
    "coding": "codex_builder_agent",
    "research": "research_agent",
    "security": "security_agent",
    "cloud": "cloud_agent",
    "business": "business_agent",
    "teaching": "tutor_agent",
    "customer_service": "general_assistant_agent",
    "decision_analysis": "research_agent",
    "general": "general_assistant_agent",
}


def get_agent(agent_name: str) -> AgentDefinition:
    return AGENTS.get(agent_name, AGENTS["general_assistant_agent"])


def select_agent(intent: CommandIntent) -> AgentDefinition:
    return get_agent(INTENT_TO_AGENT.get(intent, "general_assistant_agent"))


def list_agents() -> list[AgentDefinition]:
    return list(AGENTS.values())

