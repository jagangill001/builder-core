from __future__ import annotations

from typing import Any, Literal

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
ApprovalDecision = Literal["approved", "rejected"]
SandboxType = Literal["code_test", "simulation", "security_check", "connector_test"]


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
    approval_request: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    timeline: dict[str, Any] | None = None
    manipulation_risk: dict[str, Any] | None = None
    future_scenarios: list[dict[str, Any]] = Field(default_factory=list)
    confidence: str | None = None
    missing_data: list[str] = Field(default_factory=list)


class CommandResponse(BaseModel):
    command_id: str
    needs_clarification: bool
    questions: list[str]
    process_steps: list[ProcessStep]
    final_result: FinalResult
    task_status: dict[str, Any] | None = None


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
    service: str
    phase: str
    live_search_connected: bool
    codex_direct_connection: bool
    security_firewall: bool
    audit_log: bool


class ApprovalCreateRequest(BaseModel):
    command_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    risk_level: RiskLevel


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecision
    note: str | None = None


class IntelligenceAnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8000)


class SandboxRunRequest(BaseModel):
    command_id: str | None = None
    sandbox_type: SandboxType = "simulation"
    description: str = Field(min_length=1, max_length=4000)