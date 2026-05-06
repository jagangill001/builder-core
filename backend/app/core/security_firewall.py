from __future__ import annotations

from dataclasses import dataclass

from app.models.command_models import CommandIntent, RiskLevel


GOVERNANCE_RULES = [
    "No secret manipulation or exposure, especially in frontend code.",
    "No fake evidence, fake citations, misinformation, disinformation, or hidden influence operations.",
    "No unsafe autonomous real-world action; risky actions require explicit human approval records first.",
    "Separate facts, claims, analysis, and predictions so uncertainty stays visible.",
    "Keep every command auditable through task status and audit log records.",
]


@dataclass(frozen=True, slots=True)
class FirewallDecision:
    risk_level: RiskLevel
    approval_required: bool
    blocked: bool
    reason: str
    recommended_next_step: str


BLOCKED_PATTERNS: tuple[tuple[str, str], ...] = (
    ("steal credential", "Credential theft is not allowed."),
    ("steal password", "Credential theft is not allowed."),
    ("phishing", "Phishing assistance is not allowed."),
    ("bypass security", "Bypassing security controls is not allowed."),
    ("disable security", "Disabling security controls is not allowed."),
    ("unauthorized hacking", "Unauthorized hacking is not allowed."),
    ("hack into", "Unauthorized hacking is not allowed."),
    ("malware", "Malware creation or operation is not allowed."),
    ("ransomware", "Malware creation or operation is not allowed."),
    ("keylogger", "Credential theft tooling is not allowed."),
    ("hide my admin key in frontend", "Secrets must never be hidden in frontend code."),
    ("hide admin key in frontend", "Secrets must never be hidden in frontend code."),
    ("put admin key in frontend", "Secrets must never be placed in frontend code."),
    ("api key in frontend", "Secrets must never be placed in frontend code."),
    ("create fake news", "Creating misinformation or fake news is not allowed."),
    ("write fake news", "Creating misinformation or fake news is not allowed."),
    ("generate fake news", "Creating misinformation or fake news is not allowed."),
    ("create misinformation", "Creating misinformation is not allowed."),
    ("create disinformation", "Creating disinformation is not allowed."),
    ("generate misinformation", "Creating misinformation is not allowed."),
    ("generate disinformation", "Creating disinformation is not allowed."),
    ("propaganda campaign", "Propaganda campaigns are not allowed."),
    ("create propaganda", "Creating propaganda is not allowed."),
    ("voter manipulation", "Voter manipulation is not allowed."),
    ("manipulate voters", "Voter manipulation is not allowed."),
    ("control election", "Election control or manipulation is not allowed."),
    ("control election results", "Election control or manipulation is not allowed."),
    ("change election results", "Election control or manipulation is not allowed."),
    ("rig election", "Election control or manipulation is not allowed."),
    ("secret influence operation", "Secret influence operations are not allowed."),
    ("secretly influence", "Secret influence operations are not allowed."),
    ("casino outcome", "Controlling gambling outcomes is not allowed."),
    ("gambling outcome", "Controlling gambling outcomes is not allowed."),
    ("bot amplification", "Bot amplification is not allowed."),
    ("fake engagement", "Fake engagement campaigns are not allowed."),
    ("fake viral comments", "Fake engagement campaigns are not allowed."),
    ("change people's mood", "Secret public mood manipulation is not allowed."),
    ("manipulate public mood", "Secret public mood manipulation is not allowed."),
    ("secret public mood", "Secret public mood manipulation is not allowed."),
    ("unsafe medical decision", "Unsafe medical decisions are not allowed."),
    ("unsafe legal decision", "Unsafe legal decisions are not allowed."),
    ("unsafe financial decision", "Unsafe financial decisions are not allowed."),
    ("control vehicle", "Unsafe vehicle control is not allowed."),
    ("pilot aircraft", "Unsafe aviation control is not allowed."),
    ("weapon control", "Weapon control is not allowed."),
)

APPROVAL_PATTERNS: tuple[tuple[str, str, RiskLevel], ...] = (
    ("deploy", "Real deployments require human approval.", "high"),
    ("production", "Production changes require human approval.", "high"),
    ("cloud security", "Cloud security changes require human approval.", "high"),
    ("cloud settings", "Cloud setting changes require human approval.", "high"),
    ("firewall change", "Firewall changes require human approval.", "high"),
    ("change firewall", "Firewall changes require human approval.", "high"),
    ("secret", "Secret/admin key changes require human approval.", "high"),
    ("admin key", "Secret/admin key changes require human approval.", "high"),
    ("database change", "Database changes require human approval.", "high"),
    ("database migration", "Database changes require human approval.", "high"),
    ("delete data", "Deleting data requires human approval.", "high"),
    ("drop table", "Deleting data requires human approval.", "high"),
    ("send email", "Sending emails requires human approval.", "medium"),
    ("spend money", "Spending money requires human approval.", "high"),
    ("pay for", "Spending money requires human approval.", "high"),
    ("budget decision", "Budget decisions require human approval.", "medium"),
    ("public policy recommendation", "Public policy recommendations that affect real action require human approval.", "medium"),
    ("recommend policy", "Public policy recommendations that affect real action require human approval.", "medium"),
    ("business-critical", "Business-critical decisions require human approval.", "high"),
    ("business critical", "Business-critical decisions require human approval.", "high"),
    ("buy stock", "Finance-related actions require human approval.", "high"),
    ("sell stock", "Finance-related actions require human approval.", "high"),
    ("transfer money", "Finance-related actions require human approval.", "high"),
    ("file lawsuit", "Legal actions require human approval.", "high"),
    ("submit government", "Government actions require human approval.", "high"),
    ("execute sandbox", "Sandbox execution beyond record creation requires human approval.", "medium"),
    ("run sandbox", "Sandbox execution beyond record creation requires human approval.", "medium"),
)

HIGH_RISK_ANALYSIS_TERMS: tuple[str, ...] = (
    "medical",
    "legal",
    "financial",
    "driving",
    "pilot",
    "aviation",
    "weapon",
    "government",
)

SAFE_RESEARCH_TERMS: tuple[str, ...] = (
    "fact check",
    "fact-check",
    "is this true",
    "verify this",
    "misinformation detection",
    "source comparison",
    "timeline",
    "what happened before",
    "what happened after",
    "public-risk analysis",
    "public risk analysis",
    "prevention planning",
)


def check_risk(message: str, intent: CommandIntent) -> FirewallDecision:
    normalized = _normalize(message)

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern in normalized:
            return FirewallDecision(
                risk_level="blocked",
                approval_required=False,
                blocked=True,
                reason=reason,
                recommended_next_step=(
                    "Use Builder Core for safe education, compliance planning, risk review, "
                    "misinformation detection, or defensive analysis instead."
                ),
            )

    for pattern, reason, risk_level in APPROVAL_PATTERNS:
        if pattern in normalized:
            return FirewallDecision(
                risk_level=risk_level,
                approval_required=True,
                blocked=False,
                reason=reason,
                recommended_next_step=(
                    "Review the safe plan, confirm scope and rollback steps, then give explicit "
                    "human approval before any real-world action. Approval records do not execute actions yet."
                ),
            )

    if any(term in normalized for term in SAFE_RESEARCH_TERMS):
        return FirewallDecision(
            risk_level="low",
            approval_required=False,
            blocked=False,
            reason="Safe analysis request detected. No real-world action will be executed.",
            recommended_next_step="Use the evidence structure for neutral analysis and verify with real sources when live internet/search is connected.",
        )

    if intent == "research" and any(term in normalized for term in ["fake", "misinformation", "disinformation", "propaganda"]):
        return FirewallDecision(
            risk_level="medium",
            approval_required=False,
            blocked=False,
            reason="Misinformation analysis is allowed as source-checking and risk analysis, but live internet/search is not connected.",
            recommended_next_step="Prepare source checks and verify claims with real sources outside Builder Core until live internet/search is connected.",
        )

    if intent == "decision_analysis" and any(term in normalized for term in HIGH_RISK_ANALYSIS_TERMS):
        return FirewallDecision(
            risk_level="medium",
            approval_required=False,
            blocked=False,
            reason="High-impact decision topics are limited to education, planning, and risk analysis.",
            recommended_next_step="Use the result as analysis only, then involve responsible humans before action.",
        )

    return FirewallDecision(
        risk_level="low",
        approval_required=False,
        blocked=False,
        reason="No blocked action detected.",
        recommended_next_step="Continue with safe planning or analysis.",
    )


def _normalize(message: str) -> str:
    return " ".join(message.lower().replace("-", " ").replace("_", " ").split())