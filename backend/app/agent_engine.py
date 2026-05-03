from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.action_permissions import check_action_permission
    from app.agent_roles import AgentRoleService
    from app.crawler_plan import CrawlerPlanService
    from app.platform_adapter import get_platform_status
    from app.private_search import PrivateSearchService
    from app.research_engine import ResearchEngineService
    from app.storage import ProjectStorageService
    from app.web_ingest import WebIngestService
except ImportError:
    from action_permissions import check_action_permission
    from agent_roles import AgentRoleService
    from crawler_plan import CrawlerPlanService
    from platform_adapter import get_platform_status
    from private_search import PrivateSearchService
    from research_engine import ResearchEngineService
    from storage import ProjectStorageService
    from web_ingest import WebIngestService


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentEngineService:
    def __init__(
        self,
        storage: ProjectStorageService,
        private_search: PrivateSearchService,
        research_engine: ResearchEngineService,
        market_analyzer: Any | None,
        app_planner: Any | None,
        web_ingest: WebIngestService,
        crawler_plan: CrawlerPlanService,
        roles: AgentRoleService,
        security_monitor: Any | None = None,
        account_agent: Any | None = None,
    ) -> None:
        self.storage = storage
        self.private_search = private_search
        self.research_engine = research_engine
        self.market_analyzer = market_analyzer
        self.app_planner = app_planner
        self.web_ingest = web_ingest
        self.crawler_plan = crawler_plan
        self.roles = roles
        self.security_monitor = security_monitor
        self.account_agent = account_agent

    def run_agent(self, message: str, mode: str = "auto", save_to_memory: bool = True) -> dict[str, Any]:
        context = {
            "mode": mode,
            "platform": get_platform_status(),
            "memory": self.storage.get_project_memory(8),
            "lessons": self.storage.get_lessons(8),
        }
        plan = self.create_agent_plan(message, context)
        execution = self.execute_agent_steps(plan)
        summary = self.summarize_agent_result(execution)
        memory_saved = self.save_agent_memory(execution) if save_to_memory else False
        followups = self.create_followup_suggestions(execution)
        run_id = f"agent_run_{uuid4().hex[:12]}"
        selected_role = plan.get("selected_agent_role")
        saved_run = self.storage.save_record(
            "agent_runs",
            {
                "id": run_id,
                "run_id": run_id,
                "message": message,
                "mode": mode,
                "selected_agent_role": selected_role,
                "plan": plan,
                "result": execution,
                "summary": summary,
                "memory_saved": memory_saved,
                "created_at": utc_now_iso(),
            },
        )
        self.storage.save_record(
            "self_improvement",
            {
                "type": "agent_run",
                "user_goal": message,
                "selected_agent": selected_role,
                "tools_used": execution.get("tools_used", []),
                "what_worked": "Created an internal agent plan and used only Builder Core tools.",
                "what_failed": "; ".join(execution.get("limitations", [])) or "No failure recorded.",
                "missing_knowledge": execution.get("missing_knowledge", []),
                "security_warnings": execution.get("security_warnings", []),
                "storage_used": "firestore" if self.storage.using_firestore else "local",
                "better_future_instruction": "Keep high-risk work decision-support only and ask for explicit approval before external action.",
                "next_recommended_improvement": "Add authenticated admin controls before enabling any production security dashboard.",
            },
        )
        return {
            "ok": True,
            "agent_run_id": saved_run["id"],
            "selected_agent_role": selected_role,
            "answer": summary,
            "plan": plan,
            "result": execution,
            "tools_used": execution.get("tools_used", []),
            "approvals_needed": execution.get("approvals_needed", []),
            "security_warnings": execution.get("security_warnings", []),
            "knowledge_sources_used": execution.get("knowledge_sources_used", []),
            "confidence": execution.get("confidence", "medium"),
            "limitations": execution.get("limitations", []),
            "memory_saved": memory_saved,
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "next_actions": followups,
            "created_at": saved_run["created_at"],
        }

    def create_agent_plan(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        detected_intents = self._detect_intents(message)
        selected_agent = self._select_agent_role(message, detected_intents)
        tools = self.choose_tools_for_goal(message, detected_intents)
        steps = [
            {
                "step_id": f"step_{index + 1}",
                "tool": tool,
                "action": self._describe_tool_action(tool, message),
                "status": "created",
                "result_summary": "",
            }
            for index, tool in enumerate(tools)
        ]
        plan = {
            "goal": message,
            "selected_agent_role": selected_agent,
            "detected_intents": detected_intents,
            "steps": steps,
            "limits": [
                "This is an internal task agent, not consciousness or AGI.",
                "No uncontrolled background work.",
                "No external search API is required.",
                "High-risk or external actions require approval or are blocked.",
            ],
            "needs_user_input": [],
            "created_at": utc_now_iso(),
        }
        self.storage.save_record("agent_plans", {"id": f"agent_plan_{uuid4().hex[:12]}", **plan})
        return plan

    def choose_tools_for_goal(self, goal: str, detected_intents: list[str]) -> list[str]:
        tools = ["private_search"]
        if "security_check" in detected_intents or "incident_report" in detected_intents:
            tools.append("security_monitor")
        if "url_learning" in detected_intents:
            tools.append("url_ingest")
        if "crawler_plan" in detected_intents:
            tools.append("crawler_planning")
        if "market_analysis" in detected_intents:
            tools.append("market_analyzer")
        if "app_builder" in detected_intents:
            tools.append("app_planner")
        if "teaching" in detected_intents or "research" in detected_intents:
            tools.append("research_engine")
        if "account_agent_search" in detected_intents:
            tools.append("account_agent")
        tools.append("memory_manager")
        return list(dict.fromkeys(tools))[:8]

    def execute_agent_steps(self, plan: dict[str, Any]) -> dict[str, Any]:
        goal = str(plan.get("goal") or "")
        tools_used: list[str] = []
        knowledge_sources: list[str] = []
        limitations: list[str] = []
        approvals_needed: list[str] = []
        security_warnings: list[str] = []
        missing_knowledge: list[str] = []
        outputs: dict[str, Any] = {}
        completed_steps: list[dict[str, Any]] = []

        for step in plan.get("steps", []):
            tool = step.get("tool")
            step_result = dict(step)
            step_result["status"] = "completed"
            tools_used.append(str(tool))

            if tool == "private_search":
                search = self.private_search.search_private_index(goal, limit=5)
                outputs["private_search"] = search
                knowledge_sources.extend(search.get("top_sources", []))
                step_result["result_summary"] = f"Found {search.get('results_count', 0)} saved private-search matches."
                if not search.get("results_count"):
                    missing_knowledge.append("Private search has little saved context for this goal.")
            elif tool == "research_engine":
                research = self.research_engine.run_internal_research(topic=goal, goal=goal, category="agent")
                outputs["research"] = research
                knowledge_sources.extend([str(source.get("title") or "") for source in research.get("sources", []) if isinstance(source, dict)])
                step_result["result_summary"] = research.get("summary", "Internal research completed.")
            elif tool == "security_monitor" and self.security_monitor is not None:
                summary = self.security_monitor.get_security_summary()
                report = self.security_monitor.create_incident_report()
                outputs["security"] = {"status": summary, "report": report}
                security_warnings.extend(summary.get("warnings", []))
                step_result["result_summary"] = report.get("summary", "Security summary ready.")
            elif tool == "market_analyzer" and self.market_analyzer is not None:
                market = self.market_analyzer.analyze_market(goal, outputs.get("private_search", {}).get("results", []))
                outputs["market_analysis"] = market
                step_result["result_summary"] = market.get("market_summary", "Market analysis completed.")
            elif tool == "app_planner" and self.app_planner is not None:
                app_plan = self.app_planner.create_app_plan(
                    goal,
                    outputs.get("research"),
                    outputs.get("market_analysis"),
                )
                outputs["app_plan"] = app_plan
                step_result["result_summary"] = app_plan.get("app_concept", "App plan completed.")
            elif tool == "url_ingest":
                url = self._extract_first_url(goal)
                if not url:
                    limitations.append("No URL was found in the message, so URL learning did not run.")
                    step_result["status"] = "blocked"
                    step_result["result_summary"] = "No URL found."
                else:
                    learned = self.learn_url(url=url, topic=goal, reason="agent_run")
                    outputs["learn_url"] = learned
                    step_result["status"] = "completed" if learned.get("ok") else "blocked"
                    step_result["result_summary"] = "URL learned into private search." if learned.get("learned") else str(learned.get("blocked_reason") or learned.get("warnings"))
            elif tool == "crawler_planning":
                url = self._extract_first_url(goal)
                seed_urls = [url] if url else []
                plan_result = self.create_crawl_plan(seed_urls=seed_urls, topic=goal, max_pages=5)
                outputs["crawler_plan"] = plan_result
                step_result["status"] = "completed" if plan_result.get("allowed") else "blocked"
                step_result["result_summary"] = "Safe crawl plan created; no crawl execution was started."
            elif tool == "account_agent" and self.account_agent is not None:
                account_result = self.account_agent.run_account_search(goal, ["firestore_memory", "private_search"], save_to_memory=False)
                outputs["account_agent"] = account_result
                step_result["result_summary"] = account_result.get("summary", "Account-agent search completed.")
            elif tool == "memory_manager":
                permission = check_action_permission("save_memory", goal)
                if permission.get("blocked"):
                    step_result["status"] = "blocked"
                    step_result["result_summary"] = permission["reason"]
                else:
                    step_result["result_summary"] = "Memory can be saved when requested by the user."
            else:
                step_result["result_summary"] = "Tool is planned for this agent path but remains rule-based in this foundation stage."

            completed_steps.append(step_result)
            self.storage.save_record("agent_steps", {"id": f"agent_step_{uuid4().hex[:12]}", **step_result, "goal": goal})

        selected_agent = self.roles.get_role(str(plan.get("selected_agent_role") or ""))
        if selected_agent and selected_agent.get("human_approval_required"):
            approvals_needed.extend(selected_agent.get("requires_approval_for", []))

        return {
            "goal": goal,
            "selected_agent_role": plan.get("selected_agent_role"),
            "steps": completed_steps,
            "outputs": outputs,
            "tools_used": list(dict.fromkeys(tools_used)),
            "approvals_needed": approvals_needed,
            "security_warnings": list(dict.fromkeys(security_warnings)),
            "knowledge_sources_used": [source for source in dict.fromkeys(knowledge_sources) if source],
            "missing_knowledge": missing_knowledge,
            "limitations": limitations
            or [
                "Agent work is rule-based and internal in this foundation stage.",
                "It does not perform uncontrolled background work or external high-risk action.",
            ],
            "confidence": "medium",
        }

    def summarize_agent_result(self, result: dict[str, Any]) -> str:
        role = result.get("selected_agent_role") or "internal_agent"
        lines = [f"{role} handled the goal using Builder Core internal tools."]
        if result.get("outputs", {}).get("security"):
            lines.append(result["outputs"]["security"]["report"].get("summary", "Security report is ready."))
        if result.get("outputs", {}).get("learn_url"):
            learned = result["outputs"]["learn_url"]
            lines.append(f"URL learning: learned={learned.get('learned')} chunks={learned.get('chunks_created', 0)}.")
        if result.get("outputs", {}).get("crawler_plan"):
            lines.append("Crawler plan created without starting uncontrolled crawling.")
        if result.get("knowledge_sources_used"):
            lines.append(f"Knowledge sources used: {', '.join(result['knowledge_sources_used'][:5])}.")
        if result.get("approvals_needed"):
            lines.append("Approval gates apply before high-risk or external action.")
        return " ".join(lines)

    def save_agent_memory(self, result: dict[str, Any]) -> bool:
        self.storage.save_record(
            "agent_memory",
            {
                "id": f"agent_memory_{uuid4().hex[:12]}",
                "agent_id": result.get("selected_agent_role") or "internal_agent",
                "goal": result.get("goal"),
                "tools_used": result.get("tools_used", []),
                "summary": self.summarize_agent_result(result),
                "limitations": result.get("limitations", []),
            },
        )
        return True

    def create_followup_suggestions(self, result: dict[str, Any]) -> list[str]:
        suggestions = [
            "Search memory for related saved context.",
            "Ingest one safe public URL if more evidence is needed.",
            "Create a human-reviewed Codex prompt for implementation work.",
        ]
        if result.get("outputs", {}).get("security"):
            suggestions.insert(0, "Review the security report and hardening checklist before changing policies.")
        if result.get("approvals_needed"):
            suggestions.insert(0, "Use the approval queue before any high-risk external action.")
        return suggestions[:5]

    def learn_url(self, url: str, topic: str | None = None, reason: str | None = None) -> dict[str, Any]:
        result = self.web_ingest.ingest_url(url=url, source_note=reason or topic)
        learned = bool(result.get("ok") and result.get("document_id"))
        if learned:
            self.storage.save_record(
                "learning_lessons",
                {
                    "task_id": result.get("document_id"),
                    "command": topic or url,
                    "lesson_learned": "Builder Core learned from one user-provided safe public URL without an external search API.",
                    "next_recommendation": "Use private search or the agent engine to reuse this learned source in future answers.",
                    "source_url": url,
                    "retrieved_at": utc_now_iso(),
                    "status": "completed",
                },
            )
        return {
            "ok": bool(result.get("ok")),
            "document_id": result.get("document_id"),
            "learned": learned,
            "chunks_created": result.get("chunks_created", 0),
            "saved_to_firestore": bool(self.storage.using_firestore and learned),
            "warnings": result.get("warnings", []),
            "blocked_reason": None if result.get("ok") else "; ".join(result.get("warnings", [])),
        }

    def create_crawl_plan(self, seed_urls: list[str], topic: str, max_pages: int) -> dict[str, Any]:
        return self.crawler_plan.create_crawl_plan(seed_urls=seed_urls, max_pages=max_pages, topic=topic)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.storage.list_records("agent_runs", max(1, min(limit, 100)))

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "engine": "internal_rule_based_agent_engine",
            "agent_runs": len(self.storage.list_records("agent_runs", 200)),
            "agent_plans": len(self.storage.list_records("agent_plans", 200)),
            "agent_memory": len(self.storage.list_records("agent_memory", 200)),
            "roles_count": self.roles.count_roles(),
            "warnings": [
                "This is not AGI or consciousness.",
                "No uncontrolled background work is enabled.",
                "High-risk actions are blocked or require human approval.",
            ],
        }

    def _detect_intents(self, message: str) -> list[str]:
        lowered = message.lower()
        intents: list[str] = []
        if "act as" in lowered or "agent" in lowered:
            intents.append("agent_role_request")
        if any(token in lowered for token in ["business", "ceo", "profit", "operations"]):
            intents.append("business_planning")
        if any(token in lowered for token in ["market", "competitor", "customer"]):
            intents.append("market_analysis")
        if any(token in lowered for token in ["build app", "mvp", "app plan"]):
            intents.append("app_builder")
        if any(token in lowered for token in ["security", "attack", "under attack", "protect", "firewall"]):
            intents.append("security_check")
        if any(token in lowered for token in ["incident report", "security report"]):
            intents.append("incident_report")
        if any(token in lowered for token in ["learn this url", "learn url", "http://", "https://"]):
            intents.append("url_learning")
        if "crawl" in lowered:
            intents.append("crawler_plan")
        if any(token in lowered for token in ["teach", "study", "python"]):
            intents.append("teaching")
        if any(token in lowered for token in ["search my memory", "account agent", "my sources"]):
            intents.append("account_agent_search")
        if any(token in lowered for token in ["research", "investigate", "analyze"]):
            intents.append("research")
        return list(dict.fromkeys(intents or ["normal_chat"]))

    def _select_agent_role(self, message: str, detected_intents: list[str]) -> str:
        lowered = message.lower()
        role_map = {
            "ceo": "ceo_agent",
            "operations": "operations_manager_agent",
            "research": "research_agent",
            "developer": "developer_agent",
            "market": "market_agent",
            "sales": "sales_agent",
            "support": "customer_support_agent",
            "teacher": "teacher_agent",
            "cyber": "cybersecurity_agent",
            "security": "cybersecurity_agent",
            "finance": "finance_trading_analyst",
            "trading": "finance_trading_analyst",
            "legal": "legal_research_assistant",
            "medical": "medical_info_assistant",
            "engineering": "engineering_planner",
            "firewall": "firewall_defense_agent",
            "incident": "incident_response_agent",
            "simulation": "simulation_safety_agent",
        }
        for token, role_id in role_map.items():
            if token in lowered:
                return role_id
        if "security_check" in detected_intents:
            return "cybersecurity_agent"
        if "teaching" in detected_intents:
            return "teacher_agent"
        return "research_agent"

    def _describe_tool_action(self, tool: str, message: str) -> str:
        descriptions = {
            "private_search": "Search saved Builder Core knowledge.",
            "security_monitor": "Summarize defensive security events and recommendations.",
            "url_ingest": "Learn one safe user-provided public URL.",
            "crawler_planning": "Create a safe crawl plan without execution.",
            "market_analyzer": "Frame the market using saved context and assumptions.",
            "app_planner": "Create a small app/MVP plan.",
            "research_engine": "Run internal research over saved knowledge.",
            "account_agent": "Search connected internal account-agent sources only.",
            "memory_manager": "Save useful internal memory if requested.",
        }
        return descriptions.get(tool, f"Use {tool} for {message[:80]}.")

    def _extract_first_url(self, text: str) -> str | None:
        match = re.search(r"https?://[^\s<>\"]+", text)
        return match.group(0).rstrip(").,]") if match else None
