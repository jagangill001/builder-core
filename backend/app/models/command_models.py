from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CommandIntent = Literal[
    "coding",
    "research",
    "security",
    "cloud",
    "business",
    "teaching",
    "customer_service",
    "decision_analysis",
    "general",
]

RiskLevel = Literal["low", "medium", "high", "blocked"]
ProcessStatus = Literal["pending", "running", "completed", "blocked", "failed"]


class CommandRequest(BaseModel):
    message: str = Field(default="", max_length=8000)


class ProcessStep(BaseModel):
    name: str
    status: ProcessStatus
    summary: str


class FinalResult(BaseModel):
    type: CommandIntent
    summary: str
    selected_agent: str
    risk_level: RiskLevel
    approval_required: bool
    blocked: bool
    recommended_next_step: str


class CommandResponse(BaseModel):
    command_id: str
    needs_clarification: bool
    questions: list[str]
    process_steps: list[ProcessStep]
    final_result: FinalResult


class AgentDefinition(BaseModel):
    name: str
    purpose: str
    allowed_tasks: list[str]
    blocked_tasks: list[str]
    requires_approval_for: list[str]


class AuditEntry(BaseModel):
    command_id: str
    timestamp: str
    user_message: str
    detected_intent: CommandIntent
    selected_agent: str
    risk_level: RiskLevel
    approval_required: bool
    blocked: bool
    process_steps: list[ProcessStep]
    final_summary: str


class SystemStatus(BaseModel):
    status: Literal["ok"]
    service: Literal["builder-core"]
    phase: Literal["phase_1_core_command_system"]
    live_search_connected: bool
    codex_direct_connection: bool
    security_firewall: bool
    audit_log: bool
