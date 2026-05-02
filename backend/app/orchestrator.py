from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

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
