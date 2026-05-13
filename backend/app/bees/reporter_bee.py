from __future__ import annotations

from app.core.context import WorkflowState


def _unique_items(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


class ReporterBee:
    name = "reporter_bee"

    def run(self, state: WorkflowState) -> str:
        state.learned_items = self._build_learned_items(state)
        state.proposed_improvements = self._build_proposed_improvements(state)
        state.assistant_reply = self._compose_reply(state)

        note = (
            f"Prepared the final report with {len(state.learned_items)} learned item(s) "
            f"and {len(state.proposed_improvements)} proposal(s)."
        )
        state.add_trace(self.name, note)
        return note

    def build_response(self, state: WorkflowState) -> dict:
        return {
            "ok": True,
            "assistant_reply": state.assistant_reply,
            "intent": state.intent,
            "project_name": state.project_name,
            "worker_mode": state.worker_mode,
            "plan": state.plan_data.get("plan", []),
            "files_changed": state.files_changed,
            "files_created": state.files_changed,
            "test_result": state.test_result,
            "build_triggered": state.plan_data.get("build_triggered", False),
            "module_key": state.plan_data.get("module_key"),
            "route_path": state.plan_data.get("route_path"),
            "title": state.plan_data.get("title"),
            "inspection": state.inspection,
            "run_info": state.run_info,
            "learned_items": state.learned_items,
            "proposed_improvements": state.proposed_improvements,
            "workflow_trace": state.workflow_trace,
            "repair_attempts": state.repair_attempts,
            "repair_history": state.repair_history,
            "version_snapshot": state.version_snapshot,
            "memory": state.memory_snapshot,
            "codex_task": state.codex_task,
        }

    def _build_learned_items(self, state: WorkflowState) -> list[str]:
        inspection_summary = state.inspection.get("summary", {}) if state.inspection else {}
        items: list[str] = []

        items.append(
            f"{state.project_name} currently exposes {inspection_summary.get('module_count', 0)} module(s)."
        )

        if state.codex_task:
            items.append(
                f"Codex task {state.codex_task.get('task_id')} is {state.codex_task.get('status')} for {state.project_name}."
            )
            if state.codex_task.get("github_issue_number"):
                items.append(
                    f"GitHub issue #{state.codex_task.get('github_issue_number')} is tracking the branch-first coding work."
                )
            return _unique_items(items)[:3]

        if state.plan_data.get("build_triggered"):
            route_path = state.plan_data.get("route_path") or "/module"
            title = state.plan_data.get("title") or "module"
            items.append(
                f"{title} is routed through {route_path} and the swarm changed {len(state.files_changed)} file(s)."
            )
            items.append(
                f"Tester outcome for this build was {state.test_result.get('status', 'unknown')}."
            )
            if state.repair_attempts:
                items.append(f"Repair bee used {state.repair_attempts} attempt(s) during this workflow.")
        elif state.intent == "run" and state.run_info:
            items.append("Run instructions are available directly from the generated project scaffold.")
        elif state.intent == "inspect":
            routes = state.inspection.get("routes", []) if state.inspection else []
            if routes:
                items.append(f"Scout confirmed live project routes such as {', '.join(routes[:3])}.")

        return _unique_items(items)[:3]

    def _build_proposed_improvements(self, state: WorkflowState) -> list[str]:
        proposals: list[str] = []

        if state.codex_task:
            proposals.append("Keep the Codex bridge branch-first and merge only after Backend Checks and Frontend Checks pass.")
            proposals.append(state.codex_task.get("next_action", "Wait for Codex to pick up the GitHub issue."))
            return _unique_items(proposals)[:3]

        if state.plan_data.get("build_triggered") and state.test_result.get("status") == "success":
            proposals.append("Promote this successful step sequence into pattern memory during phase 2.")
        elif state.plan_data.get("build_triggered"):
            proposals.append("Review the recorded repair cases before widening automatic repair authority.")

        if state.intent == "inspect" and not state.inspection.get("modules"):
            proposals.append("Seed the project with a starter module so the swarm has richer context to inspect.")

        if state.repair_attempts == 0 and state.plan_data.get("build_triggered"):
            proposals.append("Keep collecting successful patterns before enabling more aggressive self-repair.")
        else:
            proposals.append("Keep commander outputs stable and compare repeated traces before widening the bee swarm.")
        return _unique_items(proposals)[:3]

    def _compose_reply(self, state: WorkflowState) -> str:
        if state.intent == "chat":
            return (
                f"Commander treated this as a chat request for {state.project_name}. "
                "The swarm stayed in observation mode, gathered project context, and is ready to pivot into build, inspect, or run as soon as you give a concrete goal."
            )

        if state.intent == "inspect":
            summary = state.inspection.get("summary", {}) if state.inspection else {}
            routes = state.inspection.get("routes", []) if state.inspection else []
            route_preview = ", ".join(routes[:4]) if routes else "/"
            return (
                f"Commander routed this as an inspect request for {state.project_name}. "
                f"Scout found {summary.get('module_count', 0)} module(s), {summary.get('file_count', 0)} generated file(s), "
                f"and routes including {route_preview}."
            )

        if state.intent == "run":
            commands = state.run_info.get("commands", []) if state.run_info else []
            return (
                f"Commander routed this as a run request for {state.project_name}. "
                f"Scout and planner prepared {len(commands)} launch command(s), and tester confirmed the run instructions are ready."
            )

        if state.codex_task:
            issue_number = state.codex_task.get("github_issue_number")
            issue_label = f"GitHub issue #{issue_number}" if issue_number else "the pending GitHub bridge task"
            return (
                f"Commander routed this as a {state.intent} request for {state.project_name}. "
                f"Planner prepared {len(state.plan_data.get('plan', []))} step(s), then the Codex bridge submitted {issue_label} "
                f"so Codex can work from a branch or pull request first. {state.codex_task.get('next_action', '')}"
            ).strip()

        title = state.plan_data.get("title") or "module"
        route_path = state.plan_data.get("route_path") or "/module"
        repair_note = ""
        if state.repair_attempts:
            repair_note = f" Repair bee ran {state.repair_attempts} attempt(s) before the final verdict."
        return (
            f"Commander routed this as a {state.intent} request for {state.project_name}. "
            f"Scout inspected the project, planner prepared {len(state.plan_data.get('plan', []))} step(s), "
            f"coder changed {len(state.files_changed)} file(s) for {title} at {route_path}, "
            f"and tester finished with {state.test_result.get('summary', 'no summary available').lower()}{repair_note}"
        )
