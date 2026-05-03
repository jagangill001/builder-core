from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.action_permissions import check_action_permission
    from app.agent_roles import AgentRoleService
    from app.storage import ProjectStorageService
except ImportError:
    from action_permissions import check_action_permission
    from agent_roles import AgentRoleService
    from storage import ProjectStorageService


INTERNAL_AGENT_TOOLS = [
    "private_search",
    "research_engine",
    "market_analyzer",
    "app_planner",
    "prompt_builder",
    "document_ingest",
    "web_ingest",
    "storage",
    "learning",
    "self_improvement",
    "safety",
    "security_monitor",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentTaskService:
    def __init__(self, storage: ProjectStorageService, roles: AgentRoleService) -> None:
        self.storage = storage
        self.roles = roles

    def create_agent_task(self, agent_id: str, user_goal: str, run_now: bool = False) -> dict[str, Any]:
        role = self.roles.get_role(agent_id)
        if role is None:
            agent_id = "research_agent"
            role = self.roles.get_role(agent_id) or {}

        risk_level = str(role.get("risk_level") or "medium")
        approval_required = bool(role.get("human_approval_required"))
        task_id = f"agent_task_{uuid4().hex[:12]}"
        created_at = utc_now_iso()
        tools = self._choose_task_tools(agent_id, user_goal, role)
        task = {
            "id": task_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_name": role.get("name", agent_id),
            "user_goal": user_goal,
            "status": "created",
            "steps": [
                {
                    "step_id": f"{task_id}_step_1",
                    "tool": "safety",
                    "action": "Review task risk and permission boundaries.",
                    "status": "created",
                    "result_summary": "",
                }
            ],
            "tools_used": [],
            "planned_tools": tools,
            "result": {},
            "approval_required": approval_required,
            "risk_level": risk_level,
            "created_at": created_at,
            "updated_at": created_at,
        }
        saved = self.save_agent_task(task)
        if run_now:
            return self.run_agent_task(saved["task_id"])
        return saved

    def run_agent_task(self, task_id: str) -> dict[str, Any]:
        task = self.get_agent_task(task_id)
        if task is None:
            return {
                "ok": False,
                "task_id": task_id,
                "status": "failed",
                "reason": "Agent task not found.",
            }

        permission = check_action_permission("generate_plan", task.get("user_goal", ""))
        if permission.get("blocked"):
            return self._update_task(
                task,
                {
                    "status": "blocked",
                    "approval_required": False,
                    "result": {
                        "summary": permission["reason"],
                        "permission": permission,
                    },
                },
            )

        role = self.roles.get_role(str(task.get("agent_id") or "")) or {}
        if task.get("approval_required") or role.get("human_approval_required"):
            status = "waiting_for_approval"
            result_summary = (
                "Task created as decision-support only. Human approval is required before any external, high-risk, or real-world action."
            )
        else:
            status = "completed"
            result_summary = "Agent created an internal plan using Builder Core tools only."

        steps = [
            {
                "step_id": f"{task_id}_step_1",
                "tool": "safety",
                "action": "Checked permission boundaries.",
                "status": "completed",
                "result_summary": permission["reason"],
            },
            {
                "step_id": f"{task_id}_step_2",
                "tool": "private_search",
                "action": "Use saved memory and private search before proposing work.",
                "status": "completed" if status == "completed" else "blocked",
                "result_summary": "Private search is allowed; no external search API is required.",
            },
            {
                "step_id": f"{task_id}_step_3",
                "tool": "prompt_builder",
                "action": "Return a concise human-reviewed action plan.",
                "status": status,
                "result_summary": result_summary,
            },
        ]
        return self._update_task(
            task,
            {
                "status": status,
                "steps": steps,
                "tools_used": list(dict.fromkeys(["safety", "private_search", "prompt_builder"] + list(task.get("planned_tools") or []))),
                "result": {
                    "summary": result_summary,
                    "role_disclaimer": role.get("disclaimer"),
                    "next_steps": self._build_next_steps(task),
                },
            },
        )

    def list_agent_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.storage.list_records("agent_tasks", max(1, min(limit, 200)))

    def get_agent_task(self, task_id: str) -> dict[str, Any] | None:
        return self.storage.get_record("agent_tasks", task_id)

    def save_agent_task(self, task: dict[str, Any]) -> dict[str, Any]:
        task["updated_at"] = utc_now_iso()
        return self.storage.save_record("agent_tasks", task)

    def add_agent_task_step(self, task_id: str, step: dict[str, Any]) -> dict[str, Any] | None:
        task = self.get_agent_task(task_id)
        if task is None:
            return None
        steps = list(task.get("steps") or [])
        steps.append({**step, "step_id": step.get("step_id") or f"{task_id}_step_{len(steps) + 1}"})
        return self.storage.update_record("agent_tasks", task_id, {"steps": steps, "updated_at": utc_now_iso()})

    def _update_task(self, task: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        updated = self.storage.update_record("agent_tasks", task["task_id"], {**updates, "updated_at": utc_now_iso()})
        return updated or {**task, **updates}

    def _choose_task_tools(self, agent_id: str, user_goal: str, role: dict[str, Any]) -> list[str]:
        tools = [tool for tool in role.get("allowed_tools", []) if tool in INTERNAL_AGENT_TOOLS or tool == "prompt_builder"]
        lowered = user_goal.lower()
        if "market" in lowered and "market_analyzer" not in tools:
            tools.append("market_analyzer")
        if "app" in lowered and "app_planner" not in tools:
            tools.append("app_planner")
        if ("security" in lowered or "attack" in lowered) and "security_monitor" not in tools:
            tools.append("security_monitor")
        if "teach" in lowered and "learning" not in tools:
            tools.append("learning")
        return list(dict.fromkeys(tools))[:8]

    def _build_next_steps(self, task: dict[str, Any]) -> list[str]:
        if task.get("approval_required"):
            return [
                "Review the task as decision-support.",
                "Approve only a specific safe action if a real-world step is needed.",
                "Keep blocked actions blocked by default.",
            ]
        return [
            "Review the generated plan.",
            "Use private search or ingest a safe source if evidence is thin.",
            "Save useful results to memory.",
        ]
