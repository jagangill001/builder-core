from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.action_permissions import check_action_permission
    from app.connectors import ConnectorRegistryService
    from app.private_search import PrivateSearchService
    from app.storage import ProjectStorageService
except ImportError:
    from action_permissions import check_action_permission
    from connectors import ConnectorRegistryService
    from private_search import PrivateSearchService
    from storage import ProjectStorageService


CURRENT_SOURCES = ["firestore_memory", "private_search", "uploaded_documents", "pasted_notes", "safe_url_ingest"]
FUTURE_READY_SOURCES = ["google_drive_ready", "gmail_ready", "youtube_transcript_ready", "browser_session_ready"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AccountAgentService:
    def __init__(
        self,
        storage: ProjectStorageService,
        private_search: PrivateSearchService,
        connectors: ConnectorRegistryService,
    ) -> None:
        self.storage = storage
        self.private_search = private_search
        self.connectors = connectors
        self.account_agent_id = "account_agent_internal"

    def get_account_agent_status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "mode": "read_only_first",
            "storage": "firestore" if self.storage.using_firestore else "local",
            "connected_sources": CURRENT_SOURCES,
            "future_ready_sources": FUTURE_READY_SOURCES,
            "write_actions_require_confirmation": True,
            "warnings": [
                "Gmail, Drive, browser session, and YouTube connectors are future-ready only and not connected.",
                "Do not paste passwords or secrets.",
                "No login, CAPTCHA, paywall bypass, hidden surveillance, or private scraping is allowed.",
            ],
            "safety_rules": [
                "Read-only first.",
                "Write actions require confirmation.",
                "Search only Builder Core memory, private search, uploaded documents, pasted notes, and safe URL ingests right now.",
                "Do not fake unavailable connectors.",
            ],
        }

    def list_available_connectors(self) -> list[dict[str, Any]]:
        return self.connectors.list_connectors()

    def run_account_search(self, query: str, sources: list[str] | None = None, save_to_memory: bool = False) -> dict[str, Any]:
        requested_sources = sources or ["firestore_memory", "private_search"]
        allowed_sources = [source for source in requested_sources if source in CURRENT_SOURCES]
        future_sources = [source for source in requested_sources if source in FUTURE_READY_SOURCES]
        limitations: list[str] = []
        results: list[dict[str, Any]] = []

        if not allowed_sources:
            allowed_sources = ["private_search"]

        if future_sources:
            limitations.append(f"Future-ready sources were requested but are not connected: {', '.join(future_sources)}.")

        if "private_search" in allowed_sources:
            search = self.private_search.search_private_index(query, limit=10)
            for item in search.get("results", []):
                results.append({**item, "source": "private_search"})

        if "firestore_memory" in allowed_sources:
            memory_collections = [
                "project_memory",
                "assistant_memory",
                "learning_lessons",
                "research_results",
                "codex_summaries",
                "app_plans",
                "market_analysis",
                "document_ingest",
                "url_ingest_records",
            ]
            lowered_query = query.lower()
            for collection in memory_collections:
                for record in self.storage.list_records(collection, 80):
                    haystack = " ".join(str(value) for value in record.values() if isinstance(value, (str, int, float))).lower()
                    if lowered_query and lowered_query in haystack:
                        results.append(
                            {
                                "source": collection,
                                "title": record.get("title") or record.get("note") or record.get("command") or collection,
                                "preview": haystack[:260],
                                "record_id": record.get("id"),
                            }
                        )

        summary = self.summarize_account_results(results)
        memory_saved = False
        if save_to_memory:
            self.save_account_agent_memory(
                {
                    "type": "account_agent_search",
                    "query": query,
                    "sources": allowed_sources,
                    "summary": summary,
                    "result_count": len(results),
                }
            )
            memory_saved = True

        audit = self.create_account_agent_audit_log(
            {
                "action": "account_agent_search",
                "query": query,
                "sources_requested": requested_sources,
                "sources_used": allowed_sources,
                "future_sources_requested": future_sources,
                "result_count": len(results),
                "memory_saved": memory_saved,
            }
        )
        return {
            "account_agent_id": self.account_agent_id,
            "query": query,
            "sources_used": allowed_sources,
            "results": results[:20],
            "summary": summary,
            "memory_saved": memory_saved,
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "limitations": limitations or ["Search is limited to connected internal Builder Core sources."],
            "audit_log_id": audit.get("id"),
            "created_at": utc_now_iso(),
        }

    def summarize_account_results(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return "No matching connected account-agent sources were found. Future OAuth connectors are not connected yet."
        top_titles = [str(item.get("title") or item.get("source") or "source") for item in results[:3]]
        return f"Found {len(results)} matching internal source records. Top matches: {', '.join(top_titles)}."

    def save_account_agent_memory(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.storage.save_record(
            "agent_memory",
            {
                "id": f"account_agent_memory_{uuid4().hex[:12]}",
                "agent_id": self.account_agent_id,
                **entry,
            },
        )

    def create_account_agent_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.storage.save_record(
            "account_agent_audit_logs",
            {
                "id": f"account_agent_audit_{uuid4().hex[:12]}",
                "account_agent_id": self.account_agent_id,
                **entry,
            },
        )

    def require_confirmation_for_write_action(self, action: str) -> dict[str, Any]:
        permission = check_action_permission(action, f"Account agent requested write action: {action}")
        if not permission.get("requires_confirmation") and permission.get("allowed"):
            permission["requires_confirmation"] = True
            permission["allowed"] = False
            permission["reason"] = "Account-agent write actions require confirmation even when the base action is normally allowed."
        return permission
