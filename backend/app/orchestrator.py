from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

try:
    from app.app_planner import AppPlannerService
    from app.command_router import route_user_message
    from app.learning import LearningService
    from app.market_analyzer import MarketAnalyzerService
    from app.model_router import ModelRouterService
    from app.private_search import PrivateSearchService
    from app.prompt_builder import build_codex_prompt, get_project_context
    from app.research_engine import ResearchEngineService
    from app.safety import check_request_safety
    from app.security_hardening import get_security_hardening_payload
    from app.self_improvement import SelfImprovementService
    from app.storage import ProjectStorageService
    from app.tool_registry import ToolRegistryService
except ImportError:
    from app_planner import AppPlannerService
    from command_router import route_user_message
    from learning import LearningService
    from market_analyzer import MarketAnalyzerService
    from model_router import ModelRouterService
    from private_search import PrivateSearchService
    from prompt_builder import build_codex_prompt, get_project_context
    from research_engine import ResearchEngineService
    from safety import check_request_safety
    from security_hardening import get_security_hardening_payload
    from self_improvement import SelfImprovementService
    from storage import ProjectStorageService
    from tool_registry import ToolRegistryService


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UnifiedOrchestrator:
    def __init__(
        self,
        storage: ProjectStorageService,
        learning: LearningService,
        task_service: Any,
        model_router: ModelRouterService,
        private_search: PrivateSearchService,
        research_engine: ResearchEngineService,
        market_analyzer: MarketAnalyzerService,
        app_planner: AppPlannerService,
        self_improvement: SelfImprovementService,
        tool_registry: ToolRegistryService,
        agent_engine: Any | None = None,
        security_monitor: Any | None = None,
        account_agent: Any | None = None,
        approval_system: Any | None = None,
        rate_limiter: Any | None = None,
        knowledge_manager: Any | None = None,
    ) -> None:
        self.storage = storage
        self.learning = learning
        self.task_service = task_service
        self.model_router = model_router
        self.private_search = private_search
        self.research_engine = research_engine
        self.market_analyzer = market_analyzer
        self.app_planner = app_planner
        self.self_improvement = self_improvement
        self.tool_registry = tool_registry
        self.agent_engine = agent_engine
        self.security_monitor = security_monitor
        self.account_agent = account_agent
        self.approval_system = approval_system
        self.rate_limiter = rate_limiter
        self.knowledge_manager = knowledge_manager

    def run_unified_workflow(self, message: str, mode: str = "auto", save_to_memory: bool = True) -> dict[str, Any]:
        safety = check_request_safety(message, category=mode)
        command_id = f"command_{uuid4().hex[:12]}"
        created_at = utc_now_iso()
        memory = self.storage.get_project_memory(8)
        assistant_memory = self.storage.get_assistant_memory(8)
        lessons = self.learning.get_lessons(8)
        latest_summary = self.storage.get_latest_summary()
        route = route_user_message(message, {"mode": mode})

        if route["workflow"] == "save_summary":
            return self._save_manual_summary(command_id, message, route, save_to_memory, created_at)

        if not safety["allowed"]:
            blocked = {
                "command_id": command_id,
                "reply": safety["reason"],
                "detected_intents": route["intents"],
                "workflow": "blocked",
                "internal_tools_used": ["safety_firewall", "command_router"],
                "progress": {
                    "status": "blocked",
                    "steps": [
                        "Safety firewall reviewed the request.",
                        "Builder Core blocked the unsafe action and returned a safe alternative.",
                    ],
                },
                "private_search": {"used": False, "results_count": 0, "top_sources": []},
                "research": {},
                "market_analysis": {},
                "app_plan": {},
                "codex_prompt": "",
                "summary": {"message": safety["safe_alternative"]},
                "storage_used": "firestore" if self.storage.using_firestore else "local",
                "memory_saved": False,
                "next_actions": [safety["safe_alternative"]],
                "limitations": ["Unsafe requests are blocked by Builder Core."],
                "created_at": created_at,
            }
            self.storage.save_record(
                "command_history",
                {
                    "command_id": command_id,
                    "message": message,
                    "mode": mode,
                    "workflow": "blocked",
                    "reply": blocked["reply"],
                    "safety": safety,
                },
            )
            return blocked

        if route["workflow"] == "security_check":
            return self._run_security_command(command_id, message, mode, route, save_to_memory, created_at)

        if route["workflow"] == "knowledge_add":
            return self._run_knowledge_add_command(command_id, message, mode, route, save_to_memory, created_at)

        if route["workflow"] == "knowledge_search":
            return self._run_knowledge_search_command(command_id, message, mode, route, save_to_memory, created_at)

        if route["workflow"] == "url_learning":
            return self._run_url_learning_command(command_id, message, mode, route, save_to_memory, created_at)

        if route["workflow"] == "agent_os" and self.agent_engine is not None:
            return self._run_agent_os_command(command_id, message, mode, route, save_to_memory, created_at)

        search_result = self.private_search.search_private_index(message, limit=6)
        tools_used = ["safety_firewall", "command_router", "private_search", "model_router"]
        workflow = route["workflow"]
        research_result: dict[str, Any] = {}
        market_result: dict[str, Any] = {}
        app_plan: dict[str, Any] = {}
        codex_prompt = ""
        summary: dict[str, Any] = {}
        limitations: list[str] = []
        progress_steps: list[str] = [
            "Safety firewall checked the request.",
            "Builder Core loaded memory, lessons, and private-search context.",
            f"Command router selected workflow: {workflow}.",
        ]

        if workflow in {"research_only", "research_to_app_plan", "market_analysis"}:
            research_result = self.research_engine.run_internal_research(
                topic=message,
                goal=message,
                category=route["primary_intent"],
            )
            tools_used.append("research_engine")
            progress_steps.append("Internal research engine summarized saved knowledge.")

        if workflow in {"market_analysis", "research_to_app_plan"}:
            topic = self._extract_market_topic(message)
            market_result = self.market_analyzer.analyze_market(topic, research_result.get("sources", []))
            tools_used.append("market_analyzer")
            progress_steps.append("Market analyzer created a target-user and opportunity framework.")

        if workflow in {"app_builder", "research_to_app_plan"}:
            topic = self._extract_market_topic(message)
            app_plan = self.app_planner.create_app_plan(topic, research_result or None, market_result or None)
            codex_prompt = app_plan.get("codex_prompt", "")
            tools_used.append("app_planner")
            progress_steps.append("App planner built an MVP plan and Codex prompt.")
        elif workflow == "codex_prompt_only":
            project_context = get_project_context(self.storage.get_project_structure_summary())
            codex_prompt = build_codex_prompt(
                command=message,
                project_context=project_context,
                memory=memory + assistant_memory,
                lessons=lessons,
                known_issues=self.learning.get_known_issues(),
            )
            tools_used.append("codex_prompt_builder")
            progress_steps.append("Codex prompt builder created a manual prompt.")
        elif workflow == "private_search":
            progress_steps.append("Private search returned saved knowledge matches.")
        elif workflow == "document_ingest":
            limitations.append("Use the advanced Document Ingest panel to submit the title, text, and source type safely.")
        elif workflow == "url_ingest":
            limitations.append("Use the advanced URL Ingest panel to fetch one safe public URL.")
        elif workflow == "crawler_plan":
            limitations.append("Use the advanced Crawler Plan panel to create a safe crawl plan without starting an automated crawl.")

        if workflow == "cloud_storage_setup":
            summary = {
                "message": "Firestore is already configured by the user. Builder Core can explain the storage plan and save a follow-up Codex prompt if needed.",
                "manual_setup": [
                    "Confirm the Cloud Run service account has Cloud Datastore User role.",
                    "Run /storage/test to verify Firestore writes from the live backend.",
                ],
            }
            limitations.append("Builder Core does not auto-create Google Cloud resources.")

        if workflow == "research_to_app_plan" and "market" not in message.lower():
            limitations.append(
                "I can start with a general market-analysis app template. Tell me the exact market later and I will customize it."
            )

        if codex_prompt:
            self.storage.save_latest_prompt(
                {
                    "task_id": command_id,
                    "command": message,
                    "project_name": "Builder Core",
                    "prompt": codex_prompt,
                    "status": "prompt_ready",
                    "workflow": workflow,
                }
            )

        reply = self._compose_reply(
            message=message,
            workflow=workflow,
            route=route,
            search_result=search_result,
            research_result=research_result,
            market_result=market_result,
            app_plan=app_plan,
            latest_summary=latest_summary,
            limitations=limitations,
        )

        next_actions = self._build_next_actions(workflow, research_result, market_result, app_plan, codex_prompt)
        memory_saved = False
        if save_to_memory:
            self.storage.save_project_memory(
                {
                    "type": "command_chat",
                    "command_id": command_id,
                    "command": message,
                    "note": f"Saved unified command result for workflow {workflow}.",
                    "workflow": workflow,
                    "next_actions": next_actions,
                }
            )
            memory_saved = True

        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": workflow,
                "detected_intents": route["intents"],
                "reply": reply,
                "private_search": {
                    "used": True,
                    "results_count": search_result.get("results_count", 0),
                    "top_sources": search_result.get("top_sources", []),
                },
            },
        )

        self.self_improvement.record_interaction_lesson(
            {
                "category": "chat",
                "user_message": message,
                "assistant_reply": reply,
                "status": "completed",
                "suggestions": next_actions,
            }
        )

        return {
            "command_id": command_id,
            "reply": reply,
            "detected_intents": route["intents"],
            "workflow": workflow,
            "internal_tools_used": list(dict.fromkeys(tools_used)),
            "progress": {
                "status": "completed" if workflow != "blocked" else "blocked",
                "steps": progress_steps,
            },
            "private_search": {
                "used": True,
                "results_count": search_result.get("results_count", 0),
                "top_sources": search_result.get("top_sources", []),
                "results": search_result.get("results", []),
            },
            "research": research_result,
            "market_analysis": market_result,
            "app_plan": app_plan,
            "codex_prompt": codex_prompt,
            "summary": summary,
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": memory_saved,
            "next_actions": next_actions,
            "limitations": limitations
            or [
                "Builder Core does not automatically perform live internet-wide research or Codex execution in this workflow."
            ],
            "created_at": created_at,
        }

    def _run_security_command(
        self,
        command_id: str,
        message: str,
        mode: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        summary = self.security_monitor.get_security_summary() if self.security_monitor is not None else {}
        report = self.security_monitor.create_incident_report() if self.security_monitor is not None else {}
        hardening = get_security_hardening_payload()
        rate_limit_status = self.rate_limiter.get_rate_limit_status() if self.rate_limiter is not None else {}
        highest = str(report.get("highest_severity") or "low")
        security = {
            "monitor_enabled": self.security_monitor is not None,
            "rate_limiter_enabled": bool(getattr(self.rate_limiter, "enabled", False)),
            "events_count": summary.get("events_count", 0),
            "highest_severity": highest,
            "recent_high_severity": summary.get("recent_high_severity", []),
            "top_patterns": report.get("top_patterns", []),
            "approximate_sources": report.get("approximate_sources", []),
            "recommendations": report.get("recommended_actions") or summary.get("recommendations", []),
            "hardening": {
                "cloud_run": hardening.get("cloud_run", [])[:3],
                "firestore": hardening.get("firestore", [])[:3],
                "secret_safety": hardening.get("secret_safety", [])[:3],
                "frontend_security": hardening.get("frontend_security", [])[:3],
                "incident_response": hardening.get("incident_response", [])[:3],
            },
            "rate_limit_status": rate_limit_status,
            "disclaimer": "IP/location data is approximate and does not identify a person. Builder Core does not retaliate.",
        }
        tools_used = [
            "safety_firewall",
            "command_router",
            "security_monitor",
            "security_hardening",
            "rate_limiter",
        ]
        reply = self._compose_security_reply(security)
        memory_saved = False
        if save_to_memory:
            self.storage.save_project_memory(
                {
                    "type": "security_check",
                    "command_id": command_id,
                    "command": message,
                    "note": f"Security check completed. Highest severity: {highest}.",
                    "workflow": route["workflow"],
                }
            )
            memory_saved = True
        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": route["workflow"],
                "detected_intents": route["intents"],
                "reply": reply,
                "security": security,
            },
        )
        return {
            "command_id": command_id,
            "reply": reply,
            "detected_intents": route["intents"],
            "workflow": route["workflow"],
            "internal_tools_used": tools_used,
            "progress": {
                "status": "completed",
                "steps": [
                    "Safety firewall checked the request.",
                    "Command router selected the defensive security workflow.",
                    "Security monitor summarized logged events.",
                    "Hardening checklists and rate-limit status were included.",
                ],
            },
            "security": security,
            "private_search": {"used": False, "results_count": 0, "top_sources": []},
            "research": {},
            "market_analysis": {},
            "app_plan": {},
            "codex_prompt": "",
            "summary": {"message": reply},
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": memory_saved,
            "next_actions": [
                "Set ADMIN_API_KEY in Cloud Run before using internal dashboard panels.",
                "Review recent high-severity events before changing any policy.",
                "Use Cloud Armor/API Gateway later for production perimeter controls.",
            ],
            "limitations": [
                "This is defensive status and hardening guidance only.",
                "IP/location data is approximate and does not identify a person.",
                "Builder Core does not retaliate or perform offensive security actions.",
            ],
            "created_at": created_at,
        }

    def _run_knowledge_add_command(
        self,
        command_id: str,
        message: str,
        mode: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        if self.knowledge_manager is None:
            raise RuntimeError("Knowledge manager is not configured.")
        note = self._extract_knowledge_note(message)
        result = self.knowledge_manager.add_knowledge_entry(
            {
                "title": self._knowledge_title(note),
                "content": note,
                "source_type": "manual_note",
                "category": self.knowledge_manager.classify_knowledge(note),
                "tags": self.knowledge_manager.tag_knowledge(note),
            }
        )
        memory_saved = False
        if save_to_memory and result.get("ok"):
            self.storage.save_project_memory(
                {
                    "type": "knowledge_note",
                    "command_id": command_id,
                    "command": message,
                    "note": note,
                    "knowledge_id": result.get("knowledge_id"),
                    "workflow": route["workflow"],
                }
            )
            memory_saved = True
        reply = (
            f"I saved that into Builder Core knowledge as {result.get('knowledge_id')}. "
            f"It was indexed for private search with {result.get('chunks_created', 0)} chunks."
            if result.get("ok")
            else "I could not save that knowledge note because the content was empty."
        )
        knowledge = {
            "action": "add",
            "saved": bool(result.get("ok")),
            "knowledge_id": result.get("knowledge_id"),
            "summary": result.get("summary"),
            "key_points": result.get("key_points", []),
            "confidence": result.get("entry", {}).get("confidence") or "low",
            "sources_used": [result.get("entry", {}).get("title")] if result.get("entry") else [],
            "missing_knowledge": [],
        }
        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": route["workflow"],
                "detected_intents": route["intents"],
                "reply": reply,
                "knowledge": knowledge,
            },
        )
        return {
            "command_id": command_id,
            "reply": reply,
            "detected_intents": route["intents"],
            "workflow": route["workflow"],
            "internal_tools_used": ["safety_firewall", "command_router", "knowledge_manager", "private_search", "learning_engine"],
            "progress": {
                "status": "completed" if result.get("ok") else "failed",
                "steps": [
                    "Detected a one-chat memory/knowledge save request.",
                    "Saved the note into the knowledge base.",
                    "Indexed the note into private search.",
                    "Created a learning lesson for reuse.",
                ],
            },
            "knowledge": knowledge,
            "knowledge_sources_used": knowledge["sources_used"],
            "confidence": knowledge["confidence"],
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": memory_saved,
            "private_search": {"used": True, "results_count": 0, "top_sources": knowledge["sources_used"]},
            "research": {},
            "market_analysis": {},
            "app_plan": {},
            "codex_prompt": "",
            "summary": result,
            "next_actions": ["Ask: what do you know about this topic?", "Add another note or safe URL to improve confidence."],
            "limitations": ["This is knowledge-base memory, not model training."],
            "created_at": created_at,
        }

    def _run_knowledge_search_command(
        self,
        command_id: str,
        message: str,
        mode: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        if self.knowledge_manager is None:
            raise RuntimeError("Knowledge manager is not configured.")
        query = self._extract_knowledge_query(message)
        result = self.knowledge_manager.search_knowledge(query=query, limit=8)
        sources = result.get("sources_used", [])
        facts = [item.get("summary") or item.get("preview") or item.get("title") for item in result.get("results", [])[:5]]
        if facts:
            reply = "Here is what Builder Core currently has saved:\n" + "\n".join(f"- {fact}" for fact in facts if fact)
        else:
            reply = "Builder Core does not have strong saved knowledge for that yet. Add notes, seed packs, or one safe public URL to improve answers."
        knowledge = {
            "action": "search",
            "query": query,
            "results": result.get("results", []),
            "sources_used": sources,
            "confidence": result.get("confidence", "low"),
            "missing_knowledge": result.get("missing_knowledge", []),
        }
        memory_saved = False
        if save_to_memory:
            self.storage.save_project_memory(
                {
                    "type": "knowledge_search",
                    "command_id": command_id,
                    "command": message,
                    "note": f"Knowledge search completed for: {query}",
                    "workflow": route["workflow"],
                    "sources_used": sources,
                }
            )
            memory_saved = True
        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": route["workflow"],
                "detected_intents": route["intents"],
                "reply": reply,
                "knowledge": knowledge,
            },
        )
        return {
            "command_id": command_id,
            "reply": reply,
            "detected_intents": route["intents"],
            "workflow": route["workflow"],
            "internal_tools_used": ["safety_firewall", "command_router", "knowledge_manager", "private_search"],
            "progress": {
                "status": "completed",
                "steps": [
                    "Detected a knowledge question.",
                    "Searched structured knowledge entries.",
                    "Searched private-search chunks.",
                    "Returned saved sources and confidence honestly.",
                ],
            },
            "knowledge": knowledge,
            "knowledge_sources_used": sources,
            "confidence": result.get("confidence", "low"),
            "private_search": result.get("private_search", {"used": True}),
            "research": {},
            "market_analysis": {},
            "app_plan": {},
            "codex_prompt": "",
            "summary": {"message": reply},
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": memory_saved,
            "next_actions": ["Seed the knowledge base.", "Add more notes or a safe public URL if the answer is weak."],
            "limitations": result.get("missing_knowledge", []) or ["Builder Core only searches saved/internal knowledge here."],
            "created_at": created_at,
        }

    def _run_url_learning_command(
        self,
        command_id: str,
        message: str,
        mode: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        url = self._extract_first_url(message)
        if not url:
            raise HTTPException(status_code=400, detail="No URL found in message.")
        learned = self.agent_engine.learn_url(url=url, topic=message, reason="command_chat") if self.agent_engine else {}
        knowledge_result = (
            self.knowledge_manager.add_url_ingest_result(learned, url=url, topic=message)
            if self.knowledge_manager is not None and learned.get("learned")
            else {"ok": False, "warnings": learned.get("warnings", [])}
        )
        reply = (
            f"I learned one safe public page: {url}. Title: {learned.get('title') or 'Unknown'}. "
            f"Text chars: {learned.get('text_chars', 0)}. Chunks created: {learned.get('chunks_created', 0)}."
            if learned.get("learned")
            else f"I could not learn that URL. {learned.get('blocked_reason') or '; '.join(learned.get('warnings', []))}"
        )
        memory_saved = False
        if save_to_memory:
            self.storage.save_project_memory(
                {
                    "type": "url_learning",
                    "command_id": command_id,
                    "command": message,
                    "note": f"URL learning attempted for {url}. learned={learned.get('learned')}",
                    "workflow": route["workflow"],
                }
            )
            memory_saved = True
        knowledge = {
            "action": "learn_url",
            "source_url": url,
            "learned": bool(learned.get("learned")),
            "title": learned.get("title"),
            "text_chars": learned.get("text_chars", 0),
            "chunks_created": learned.get("chunks_created", 0),
            "knowledge_id": knowledge_result.get("knowledge_id"),
            "warnings": learned.get("warnings", []) + knowledge_result.get("warnings", []),
            "confidence": knowledge_result.get("entry", {}).get("confidence") or ("medium" if learned.get("learned") else "low"),
        }
        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": route["workflow"],
                "detected_intents": route["intents"],
                "reply": reply,
                "knowledge": knowledge,
            },
        )
        return {
            "command_id": command_id,
            "reply": reply,
            "detected_intents": route["intents"],
            "workflow": route["workflow"],
            "internal_tools_used": ["safety_firewall", "command_router", "url_ingest", "knowledge_manager", "private_search"],
            "progress": {
                "status": "completed" if learned.get("learned") else "blocked",
                "steps": [
                    "Detected a URL learning request in the main chat.",
                    "Checked safe URL rules.",
                    "Fetched one page only when allowed.",
                    "Indexed the result into private search and knowledge when learning succeeded.",
                ],
            },
            "knowledge": knowledge,
            "knowledge_sources_used": [knowledge.get("title")] if knowledge.get("title") else [],
            "confidence": knowledge["confidence"],
            "private_search": {"used": bool(learned.get("learned")), "results_count": 0, "top_sources": [knowledge.get("title")] if knowledge.get("title") else []},
            "research": {},
            "market_analysis": {},
            "app_plan": {},
            "codex_prompt": "",
            "summary": learned,
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": memory_saved,
            "next_actions": ["Ask what Builder Core learned from the page.", "Add another safe public URL only when you want one-page learning."],
            "limitations": [
                "Only one user-provided public http/https page is fetched.",
                "No login, paywall, CAPTCHA bypass, private scraping, or uncontrolled crawling is performed.",
            ],
            "created_at": created_at,
        }

    def _compose_security_reply(self, security: dict[str, Any]) -> str:
        return "\n".join(
            [
                "Builder Core defensive security status:",
                f"- Monitor enabled: {security.get('monitor_enabled')}",
                f"- Rate limiter enabled: {security.get('rate_limiter_enabled')}",
                f"- Events logged: {security.get('events_count', 0)}",
                f"- Highest severity: {security.get('highest_severity', 'low')}",
                "- Recommended actions: " + "; ".join(security.get("recommendations", [])[:3]),
                "- Policy: no retaliation; use logs, hardening, provider controls, and human approval for policy changes.",
                f"- Limit: {security.get('disclaimer')}",
            ]
        )

    def _extract_knowledge_note(self, message: str) -> str:
        patterns = [
            r"remember this:\s*(.*)",
            r"learn this note:\s*(.*)",
            r"learn this:\s*(.*)",
            r"save this to memory:\s*(.*)",
            r"save this:\s*(.*)",
            r"add this to knowledge:\s*(.*)",
            r"study this:\s*(.*)",
            r"teach yourself this:\s*(.*)",
            r"ingest this note:\s*(.*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return message.strip()

    def _extract_knowledge_query(self, message: str) -> str:
        patterns = [
            r"search your knowledge for\s*(.*)",
            r"what do you know about\s*(.*)",
            r"use your knowledge to\s*(.*)",
            r"build knowledge about\s*(.*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                return match.group(1).strip(" ?:")
        return message.strip()

    def _extract_first_url(self, text: str) -> str | None:
        match = re.search(r"https?://[^\s<>\"]+", text)
        return match.group(0).rstrip(").,]") if match else None

    def _knowledge_title(self, note: str) -> str:
        first = note.strip().split(".")[0].strip()
        return first[:120] or "Manual knowledge note"

    def _save_manual_summary(
        self,
        command_id: str,
        message: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        latest_prompt = self.storage.get_latest_prompt() or {}
        task_id = str(latest_prompt.get("task_id") or "").strip()
        extracted = self.learning.extract_codex_summary_details(message)
        updated_task = None
        tools_used = ["safety_firewall", "command_router", "memory_manager", "learning_engine"]

        if task_id:
            task = self.task_service.get_task(task_id)
            if task is not None:
                summary = {
                    "task_id": task_id,
                    "original_command": task.get("command"),
                    "final_status": "completed_manual_codex",
                    "stages_completed": ["summary_received", "completed"],
                    "files_changed": extracted.get("files_changed", []),
                    "folder_used": "builder-core",
                    "backend_logs": ["Summary saved from unified command chat."],
                    "errors": extracted.get("known_issues", []),
                    "what_completed": extracted.get("what_completed", []),
                    "what_still_needs_manual_setup": extracted.get("what_remains", []),
                    "next_recommended_step": extracted.get("next_recommendation"),
                    "message": "Manual Codex summary saved from the unified command chat.",
                    "codex_summary": message,
                    "updated_at": created_at,
                }
                updated_task = self.task_service.update_task(
                    task_id,
                    {
                        "status": "completed_manual_codex",
                        "stage": "completed",
                        "current_stage": "completed",
                        "progress": 100,
                        "summary": summary,
                        "codex_summary": message,
                        "files_changed": extracted.get("files_changed", []),
                        "known_issues": extracted.get("known_issues", []),
                        "what_completed": extracted.get("what_completed", []),
                        "what_remains": extracted.get("what_remains", []),
                        "next_recommended_step": extracted.get("next_recommendation"),
                    },
                )
                self.storage.save_latest_summary(summary)
                self.learning.record_codex_summary_lesson(updated_task or task, message)

        if save_to_memory:
            self.storage.save_project_memory(
                {
                    "type": "codex_summary",
                    "command_id": command_id,
                    "task_id": task_id or None,
                    "note": "Saved a manual Codex summary from the unified command chat.",
                    "codex_summary": message,
                    "files_changed": extracted.get("files_changed", []),
                    "next_recommended_step": extracted.get("next_recommendation"),
                }
            )

        self.self_improvement.record_interaction_lesson(
            {
                "category": "project",
                "command": task_id or "manual_summary",
                "summary": message,
                "status": "completed_manual_codex",
                "suggestions": [extracted.get("next_recommendation")],
            }
        )

        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "workflow": "save_summary",
                "detected_intents": route["intents"],
                "reply": "Builder Core saved the pasted Codex summary and updated memory plus learning.",
            },
        )

        return {
            "command_id": command_id,
            "reply": "Builder Core saved the pasted Codex summary and updated memory plus learning.",
            "detected_intents": route["intents"],
            "workflow": "save_summary",
            "internal_tools_used": tools_used,
            "progress": {
                "status": "completed",
                "steps": [
                    "Builder Core detected a pasted Codex summary.",
                    "The summary was parsed into files changed, completed work, and remaining setup.",
                    "Memory, learning, and self-improvement notes were updated.",
                ],
            },
            "private_search": {
                "used": False,
                "results_count": 0,
                "top_sources": [],
            },
            "research": {},
            "market_analysis": {},
            "app_plan": {},
            "codex_prompt": "",
            "summary": updated_task.get("summary") if isinstance(updated_task, dict) else {
                "message": "Summary saved, but no matching task was found. Memory and learning were still updated.",
            },
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "memory_saved": True,
            "next_actions": [extracted.get("next_recommendation") or "Review the saved lesson and choose the next safe task."],
            "limitations": ["Builder Core still relies on the user to paste the Codex summary manually."],
            "created_at": created_at,
        }

    def _run_agent_os_command(
        self,
        command_id: str,
        message: str,
        mode: str,
        route: dict[str, Any],
        save_to_memory: bool,
        created_at: str,
    ) -> dict[str, Any]:
        agent_result = self.agent_engine.run_agent(message=message, mode=mode, save_to_memory=save_to_memory)
        reply = agent_result.get("answer") or "Builder Core OS agent workflow completed."
        tools_used = ["safety_firewall", "command_router", "agent_engine"] + list(agent_result.get("tools_used") or [])
        progress_steps = [
            "Safety firewall checked the request.",
            "Command router selected Builder Core OS agent workflow.",
        ]
        for step in agent_result.get("plan", {}).get("steps", []):
            action = str(step.get("action") or "").strip()
            if action:
                progress_steps.append(action)

        self.storage.save_record(
            "command_history",
            {
                "command_id": command_id,
                "message": message,
                "mode": mode,
                "workflow": "agent_os",
                "detected_intents": route.get("intents", []),
                "selected_agent_role": agent_result.get("selected_agent_role"),
                "reply": reply,
            },
        )

        return {
            "command_id": command_id,
            "reply": reply,
            "selected_agent_role": agent_result.get("selected_agent_role"),
            "detected_intents": route.get("intents", []),
            "workflow": "agent_os",
            "internal_tools_used": list(dict.fromkeys(tools_used)),
            "progress": {
                "status": "completed",
                "steps": progress_steps,
                "agent_plan": agent_result.get("plan"),
            },
            "private_search": agent_result.get("result", {}).get("outputs", {}).get(
                "private_search",
                {"used": False, "results_count": 0, "top_sources": []},
            ),
            "research": agent_result.get("result", {}).get("outputs", {}).get("research", {}),
            "market_analysis": agent_result.get("result", {}).get("outputs", {}).get("market_analysis", {}),
            "app_plan": agent_result.get("result", {}).get("outputs", {}).get("app_plan", {}),
            "codex_prompt": "",
            "summary": {
                "message": reply,
                "agent_run_id": agent_result.get("agent_run_id"),
                "approvals_needed": agent_result.get("approvals_needed", []),
                "security": agent_result.get("result", {}).get("outputs", {}).get("security", {}),
                "learn_url": agent_result.get("result", {}).get("outputs", {}).get("learn_url", {}),
                "crawler_plan": agent_result.get("result", {}).get("outputs", {}).get("crawler_plan", {}),
            },
            "storage_used": agent_result.get("storage_used") or ("firestore" if self.storage.using_firestore else "local"),
            "memory_saved": agent_result.get("memory_saved", False),
            "next_actions": agent_result.get("next_actions", []),
            "limitations": agent_result.get("limitations", []),
            "approvals_needed": agent_result.get("approvals_needed", []),
            "security_warnings": agent_result.get("security_warnings", []),
            "knowledge_sources_used": agent_result.get("knowledge_sources_used", []),
            "confidence": agent_result.get("confidence", "medium"),
            "created_at": created_at,
        }

    def _extract_market_topic(self, message: str) -> str:
        lowered = message.lower()
        if "trucking dispatch" in lowered:
            return "trucking dispatch market"
        if "dispatch" in lowered and "market" in lowered:
            return "dispatch market"
        if "market" in lowered:
            return message.replace("create an app", "").replace("build an app", "").strip()
        return message.strip()

    def _build_reply_prompt(
        self,
        message: str,
        workflow: str,
        research_result: dict[str, Any],
        market_result: dict[str, Any],
        app_plan: dict[str, Any],
        latest_summary: dict[str, Any] | None,
    ) -> str:
        pieces = [f"User message: {message}", f"Workflow: {workflow}"]
        if research_result:
            pieces.append(f"Research summary: {research_result.get('summary', '')}")
        if market_result:
            pieces.append(f"Market summary: {market_result.get('market_summary', '')}")
        if app_plan:
            pieces.append(f"App concept: {app_plan.get('app_concept', '')}")
        if isinstance(latest_summary, dict):
            pieces.append(f"Latest saved summary next step: {latest_summary.get('next_recommended_step', '')}")
        return "\n".join(piece for piece in pieces if piece)

    def _compose_reply(
        self,
        message: str,
        workflow: str,
        route: dict[str, Any],
        search_result: dict[str, Any],
        research_result: dict[str, Any],
        market_result: dict[str, Any],
        app_plan: dict[str, Any],
        latest_summary: dict[str, Any] | None,
        limitations: list[str],
    ) -> str:
        if workflow == "normal_chat":
            reply_prompt = self._build_reply_prompt(message, workflow, research_result, market_result, app_plan, latest_summary)
            return self.model_router.generate_reply(
                reply_prompt,
                {
                    "workflow": workflow,
                    "memory": self.storage.get_project_memory(8) + self.storage.get_assistant_memory(6),
                    "lessons": self.learning.get_lessons(8),
                    "project_name": "Builder Core",
                    "known_issues": self.learning.get_known_issues(),
                },
            )

        lines = [
            f"Builder Core handled this as `{workflow}`.",
            f"Detected intents: {', '.join(route.get('intents', [])) or 'chat'}.",
        ]
        if search_result.get("results_count", 0):
            lines.append(
                f"Private search found {search_result.get('results_count', 0)} saved matches, including {', '.join(search_result.get('top_sources', [])[:3])}."
            )
        else:
            lines.append("Private search did not find strong saved matches yet, so this response is using the current stored context conservatively.")

        if research_result:
            lines.append(f"Research summary: {research_result.get('summary', 'No research summary was generated.')}")

        if market_result:
            lines.append(f"Market view: {market_result.get('market_summary', 'No market summary was generated.')}")

        if app_plan:
            lines.append(f"App concept: {app_plan.get('app_concept', 'No app concept was generated.')}")
            features = app_plan.get("mvp_features") or []
            if features:
                lines.append(f"Starter MVP: {', '.join(str(item) for item in features[:3])}.")

        if isinstance(latest_summary, dict):
            next_step = str(latest_summary.get("next_recommended_step") or "").strip()
            if next_step:
                lines.append(f"Latest saved lesson says the next safe move is: {next_step}")

        if limitations:
            lines.append(f"Limit note: {limitations[0]}")

        return "\n".join(lines)

    def _build_next_actions(
        self,
        workflow: str,
        research_result: dict[str, Any],
        market_result: dict[str, Any],
        app_plan: dict[str, Any],
        codex_prompt: str,
    ) -> list[str]:
        actions = []
        if research_result:
            actions.append("Review the internal research findings and add more documents or safe URL ingests if the evidence still feels thin.")
        if market_result:
            actions.append("Verify the target users and competitor questions with real external research before trusting the market direction.")
        if app_plan:
            actions.append("Trim the MVP plan down to the smallest version worth building first.")
        if codex_prompt:
            actions.append("Copy the Codex prompt into Codex manually when you are ready to build the next step.")
        if not actions:
            actions.append("Keep the discussion going or save the most useful note to memory.")
        return actions[:6]
