from __future__ import annotations

from typing import Any

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


DEFAULT_TOOLS = [
    {
        "tool_id": "assistant_chat",
        "name": "Builder Core Assistant",
        "description": "Local-first project-aware assistant chat.",
        "category": "assistant",
        "enabled": True,
        "input_schema": "message, mode, save_to_memory",
        "output_schema": "reply, suggestions, next_actions, memory_used",
        "limitations": ["Stronger AI replies need optional model configuration later."],
        "safety_notes": ["Does not claim live internet knowledge unless research is actually run."],
    },
    {
        "tool_id": "command_router",
        "name": "Command Router",
        "description": "Detects intents and chooses the next internal workflow.",
        "category": "orchestration",
        "enabled": True,
        "input_schema": "message, context",
        "output_schema": "primary_intent, intents, workflow, actions",
        "limitations": ["Rule-based routing only in this phase."],
        "safety_notes": ["Routes still pass through the safety firewall."],
    },
    {
        "tool_id": "private_search",
        "name": "Private Search",
        "description": "Searches Builder Core's saved knowledge and indexed documents.",
        "category": "search",
        "enabled": True,
        "input_schema": "query, limit",
        "output_schema": "results, scores, source summaries",
        "limitations": ["Not internet-wide and not Google-scale."],
        "safety_notes": ["Searches saved knowledge only unless safe URL ingest has added public pages."],
    },
    {
        "tool_id": "document_ingest",
        "name": "Document Ingest",
        "description": "Ingests plain text into private search and knowledge storage.",
        "category": "ingest",
        "enabled": True,
        "input_schema": "title, text, source_type, tags",
        "output_schema": "document_id, chunks_created, saved flags",
        "limitations": ["Plain text only right now."],
        "safety_notes": ["Text passes through the safety firewall before indexing."],
    },
    {
        "tool_id": "safe_url_ingest",
        "name": "Safe URL Ingest",
        "description": "Fetches one public URL safely and adds readable text to private search.",
        "category": "ingest",
        "enabled": True,
        "input_schema": "url, source_note",
        "output_schema": "document_id, text_chars, warnings",
        "limitations": ["Single-page public fetch only, no login or paywall bypass."],
        "safety_notes": ["Blocks private IPs, localhost, file URLs, onion links, and unsafe targets."],
    },
    {
        "tool_id": "research_engine",
        "name": "Research Engine",
        "description": "Runs internal research using saved knowledge first.",
        "category": "research",
        "enabled": True,
        "input_schema": "topic, goal, category",
        "output_schema": "summary, findings, unknowns, confidence, next_steps",
        "limitations": ["No live web research unless safe URL ingest has added documents."],
        "safety_notes": ["Must stay honest about missing evidence and unknowns."],
    },
    {
        "tool_id": "market_analyzer",
        "name": "Market Analyzer",
        "description": "Creates market-analysis structure from saved knowledge and user context.",
        "category": "analysis",
        "enabled": True,
        "input_schema": "topic, context_sources",
        "output_schema": "market_summary, target_users, risks, opportunities, app_ideas",
        "limitations": ["No guaranteed market predictions."],
        "safety_notes": ["Must separate evidence from assumptions."],
    },
    {
        "tool_id": "app_planner",
        "name": "App Planner",
        "description": "Turns research and market analysis into an app plan and Codex-ready build direction.",
        "category": "planning",
        "enabled": True,
        "input_schema": "goal, research_result, market_analysis",
        "output_schema": "app_plan, routes, screens, storage collections, codex prompt",
        "limitations": ["Provides planning structure, not automatic code execution."],
        "safety_notes": ["Keeps MVP scope small and explicit."],
    },
    {
        "tool_id": "codex_prompt_builder",
        "name": "Codex Prompt Builder",
        "description": "Builds strong manual Codex prompts from Builder Core context.",
        "category": "planning",
        "enabled": True,
        "input_schema": "command, memory, lessons, project context",
        "output_schema": "copyable prompt",
        "limitations": ["Manual handoff to Codex is still required."],
        "safety_notes": ["Does not fake repo changes or execution."],
    },
    {
        "tool_id": "memory_manager",
        "name": "Memory Manager",
        "description": "Stores project memory, assistant memory, summaries, and history.",
        "category": "memory",
        "enabled": True,
        "input_schema": "record collections and payloads",
        "output_schema": "saved records and storage status",
        "limitations": ["Local fallback is still temporary on Cloud Run."],
        "safety_notes": ["No secrets should be stored in plaintext memory."],
    },
    {
        "tool_id": "learning_engine",
        "name": "Learning Engine",
        "description": "Turns saved tasks and summaries into lessons and next recommendations.",
        "category": "learning",
        "enabled": True,
        "input_schema": "task, summary, saved memory",
        "output_schema": "lessons, issues, recommended next steps",
        "limitations": ["Not a trained model."],
        "safety_notes": ["Must describe saved history honestly."],
    },
    {
        "tool_id": "self_improvement",
        "name": "Self-Improvement",
        "description": "Tracks what worked, what failed, and better future instructions.",
        "category": "learning",
        "enabled": True,
        "input_schema": "interaction or manual note",
        "output_schema": "improvement notes and next recommended upgrade",
        "limitations": ["Memory-based improvement only."],
        "safety_notes": ["Does not claim AI model training."],
    },
    {
        "tool_id": "storage_manager",
        "name": "Storage Manager",
        "description": "Routes Builder Core records to local JSON or Firestore.",
        "category": "storage",
        "enabled": True,
        "input_schema": "collection, record, updates",
        "output_schema": "saved records, storage status, test results",
        "limitations": ["Firestore still needs working permissions."],
        "safety_notes": ["Never store secrets in frontend-visible data."],
    },
    {
        "tool_id": "safety_firewall",
        "name": "Safety Firewall",
        "description": "Checks requests before internal tools act on them.",
        "category": "safety",
        "enabled": True,
        "input_schema": "text, category",
        "output_schema": "allowed, risk_level, reason, safe_alternative",
        "limitations": ["Rule-based only right now."],
        "safety_notes": ["Blocks hacking, dark web, paywall bypass, and dangerous content."],
    },
    {
        "tool_id": "model_router",
        "name": "Model Router",
        "description": "Chooses between local rule-based logic, future local models, or optional OpenAI mode.",
        "category": "assistant",
        "enabled": True,
        "input_schema": "prompt, context",
        "output_schema": "reply, plan, summary, ideas",
        "limitations": ["Defaults to local rule-based mode."],
        "safety_notes": ["OpenAI is optional only, not required."],
    },
    {
        "tool_id": "crawler_planner",
        "name": "Crawler Planner",
        "description": "Creates safe crawl plans without running uncontrolled crawls.",
        "category": "planning",
        "enabled": True,
        "input_schema": "seed_urls, max_pages",
        "output_schema": "plan, limits, warnings",
        "limitations": ["Planning only, not execution."],
        "safety_notes": ["Must respect public-only, rate limits, and safety boundaries."],
    },
    {
        "tool_id": "platform_adapter",
        "name": "Platform Adapter",
        "description": "Detects runtime platform, storage mode, degradation plan, and future portability notes.",
        "category": "platform",
        "enabled": True,
        "input_schema": "environment",
        "output_schema": "platform, runtime_mode, resource_profile, supported capabilities",
        "limitations": ["Best-effort detection only."],
        "safety_notes": ["Does not claim unsupported hardware control."],
    },
    {
        "tool_id": "agent_engine",
        "name": "Agent Engine",
        "description": "Runs internal rule-based agent plans using Builder Core tools.",
        "category": "agents",
        "enabled": True,
        "input_schema": "message, mode, save_to_memory",
        "output_schema": "plan, steps, tools_used, limitations, next_actions",
        "limitations": ["Not AGI or autonomous background work."],
        "safety_notes": ["High-risk actions stay blocked or approval-gated."],
    },
    {
        "tool_id": "approval_system",
        "name": "Human Approval System",
        "description": "Records approval requests for high-risk or external actions.",
        "category": "safety",
        "enabled": True,
        "input_schema": "action_type, description, requested_by_agent",
        "output_schema": "approval_id, status, risk_level",
        "limitations": ["Blocked-by-default actions cannot be approved here."],
        "safety_notes": ["Human approval is required for high-risk domains."],
    },
    {
        "tool_id": "security_monitor",
        "name": "Defensive Security Monitor",
        "description": "Logs suspicious requests, summarizes incidents, and supports defensive hardening.",
        "category": "security",
        "enabled": True,
        "input_schema": "request metadata",
        "output_schema": "security events, summary, incident report",
        "limitations": ["IP geolocation is not configured and cannot identify a person."],
        "safety_notes": ["No hack-back or offensive action."],
    },
    {
        "tool_id": "account_agent",
        "name": "Account Agent",
        "description": "Searches user-authorized internal sources in read-only-first mode.",
        "category": "connectors",
        "enabled": True,
        "input_schema": "query, sources, save_to_memory",
        "output_schema": "results, summary, audit_log_id",
        "limitations": ["Gmail, Drive, browser, and YouTube are future-ready only."],
        "safety_notes": ["No passwords, CAPTCHA bypass, login bypass, or private scraping."],
    },
]


class ToolRegistryService:
    def __init__(self, storage: ProjectStorageService | None = None) -> None:
        self.storage = storage
        self._tools = {tool["tool_id"]: dict(tool) for tool in DEFAULT_TOOLS}

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())

    def get_tool(self, tool_id: str) -> dict[str, Any] | None:
        return self._tools.get(tool_id)

    def register_tool(self, tool: dict[str, Any]) -> dict[str, Any]:
        self._tools[tool["tool_id"]] = dict(tool)
        return self._tools[tool["tool_id"]]

    def get_enabled_tools(self) -> list[dict[str, Any]]:
        return [tool for tool in self._tools.values() if tool.get("enabled")]

    def get_tool_status(self) -> dict[str, Any]:
        payload = {
            "total_tools": len(self._tools),
            "enabled_tools": len(self.get_enabled_tools()),
            "disabled_tools": len([tool for tool in self._tools.values() if not tool.get("enabled")]),
        }
        if self.storage is not None:
            self.storage.save_record(
                "tool_registry",
                {
                    "tool_id": "tool_registry_snapshot",
                    "name": "Tool Registry Snapshot",
                    "description": "Latest internal tool registry status.",
                    "snapshot": payload,
                    "items": self.list_tools(),
                },
            )
        return payload
