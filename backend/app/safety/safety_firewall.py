from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    blocked: bool
    approval_required: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    reason: str = "No safety issue detected."


SECRET_PATTERNS = (
    re.compile(r"(?i)\b(show|print|reveal|display|expose|dump)\b.*\b(env|environment|secret|token|api key|password|credential)s?\b"),
    re.compile(r"(?i)\b(admin_token|github_token|search_api_key|weather_api_key|news_api_key|codex_api_key)\b"),
    re.compile(r"(?i)\b(api[_\s-]?key|secret|password|credential|token)\s*[:=]"),
)

DESTRUCTIVE_PATTERNS = (
    "delete production",
    "drop database",
    "drop table",
    "wipe database",
    "erase all",
    "reset --hard",
    "force push",
    "delete branch",
)

UNSAFE_AUTOMATION_PATTERNS = (
    "bypass security",
    "steal token",
    "steal password",
    "phishing",
    "malware",
    "ransomware",
    "control election",
    "fake engagement",
)


class SafetyFirewall:
    def check(self, message: str) -> SafetyDecision:
        normalized = " ".join(message.lower().split())
        if not normalized:
            return SafetyDecision(
                blocked=True,
                approval_required=False,
                errors=["invalid_command"],
                reason="The command is empty.",
            )

        for pattern in SECRET_PATTERNS:
            if pattern.search(message):
                return SafetyDecision(
                    blocked=True,
                    approval_required=False,
                    errors=["secret_exposure_blocked"],
                    warnings=["Builder Core never shows secrets or environment variable values."],
                    reason="The request appears to ask for hidden secret or environment values.",
                )

        if any(term in normalized for term in UNSAFE_AUTOMATION_PATTERNS):
            return SafetyDecision(
                blocked=True,
                approval_required=False,
                errors=["unsafe_request_blocked"],
                reason="The request matches unsafe automation or harmful activity.",
            )

        if any(term in normalized for term in DESTRUCTIVE_PATTERNS):
            return SafetyDecision(
                blocked=False,
                approval_required=True,
                warnings=["This looks destructive and needs explicit admin approval before any real action."],
                reason="Potentially destructive action detected.",
            )

        if any(term in normalized for term in ("deploy", "rollback", "create issue", "open pull request", "commit changes")):
            return SafetyDecision(
                blocked=False,
                approval_required=True,
                warnings=["This action may require admin mode before Builder Core performs real external writes."],
                reason="Real-world write action detected.",
            )

        return SafetyDecision(blocked=False, approval_required=False)
