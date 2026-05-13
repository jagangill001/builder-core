from __future__ import annotations

from app.connectors.registry import configured_connector_map
from app.memory.lessons import list_lessons


def recommended_next_steps() -> list[str]:
    connectors = configured_connector_map()
    steps: list[str] = [
        "Keep routing all frontend commands through /tasks/create so backend remains source of truth.",
    ]
    if not connectors.get("github"):
        steps.append("Configure GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME to enable real GitHub automation.")
    if not connectors.get("search"):
        steps.append("Add a real search provider adapter before relying on current-events answers.")
    if not connectors.get("weather"):
        steps.append("Add a real weather provider adapter before answering weather requests.")
    if not connectors.get("news"):
        steps.append("Add a real news provider adapter before answering news requests.")
    if list_lessons():
        steps.append("Review lessons learned before adding more automation, especially connector and deployment failures.")
    steps.append("Move immediate task processing into an external worker when tasks become long-running.")
    return steps
