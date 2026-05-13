from __future__ import annotations

from dataclasses import dataclass

from app.models.command_models import CommandIntent, RiskLevel


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
    ("create fake news", "Fake news creation is not allowed."),
    ("write fake news", "Fake news creation is not allowed."),
    ("generate fake news", "Fake news creation is not allowed."),
    ("propaganda campaign", "Propaganda campaigns are not allowed."),
    ("voter manipulation", "Voter manipulation is not allowed."),
    ("manipulate voters", "Voter manipulation is not allowed."),
    ("control election", "Election control or manipulation is not allowed."),
    ("control election results", "Election control or manipulation is not allowed."),
    ("change election results", "Election control or manipulation is not allowed."),
    ("rig election", "Election control or manipulation is not allowed."),
    ("casino outcome", "Controlling gambling outcomes is not allowed."),
    ("gambling outcome", "Controlling gambling outcomes is not allowed."),
    ("bot amplification", "Bot amplification is not allowed."),
    ("fake engagement", "Fake engagement campaigns are not allowed."),
    ("fake viral comments", "Fake engagement campaigns are not allowed."),
    ("change people's mood", "Secret public mood manipulation is not allowed."),
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
    ("business-critical", "Business-critical decisions require human approval.", "high"),
    ("buy stock", "Finance-related actions require human approval.", "high"),
    ("sell stock", "Finance-related actions require human approval.", "high"),
    ("transfer money", "Finance-related actions require human approval.", "high"),
    ("file lawsuit", "Legal actions require human approval.", "high"),
    ("submit government", "Government actions require human approval.", "high"),
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
                    "or defensive analysis instead."
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
                    "human approval before any real-world action."
                ),
            )

    if intent == "research" and ("fake" in normalized or "misinformation" in normalized):
        return FirewallDecision(
            risk_level="medium",
            approval_required=False,
            blocked=False,
            reason="Misinformation analysis is allowed as research planning, but live search is not connected.",
            recommended_next_step="Prepare source checks and verify claims with real sources outside Builder Core.",
        )

    if intent == "decision_analysis" and any(term in normalized for term in HIGH_RISK_ANALYSIS_TERMS):
        return FirewallDecision(
            risk_level="medium",
            approval_required=False,
            blocked=False,
            reason="High-impact decision topics are limited to education, planning, and risk analysis.",
            recommended_next_step="Use the result as analysis only, then involve qualified humans before action.",
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
