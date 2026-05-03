from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.knowledge_manager import KnowledgeManagerService
    from app.learning_url_packs import LearningUrlPackService
    from app.storage import ProjectStorageService
    from app.web_ingest import WebIngestService
except ImportError:
    from knowledge_manager import KnowledgeManagerService
    from learning_url_packs import LearningUrlPackService
    from storage import ProjectStorageService
    from web_ingest import WebIngestService


DEFAULT_LIMITS = {
    "max_urls_per_run": 5,
    "max_pages_per_domain_per_run": 2,
    "timeout_seconds": 15,
    "max_content_bytes": 1_000_000,
    "daily_url_limit": 50,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningRunnerService:
    def __init__(
        self,
        storage: ProjectStorageService,
        packs: LearningUrlPackService,
        web_ingest: WebIngestService,
        knowledge_manager: KnowledgeManagerService,
    ) -> None:
        self.storage = storage
        self.packs = packs
        self.web_ingest = web_ingest
        self.knowledge_manager = knowledge_manager

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_id = f"learning_run_{uuid4().hex[:12]}"
        max_urls = self._bounded_int(payload.get("max_urls_per_run"), DEFAULT_LIMITS["max_urls_per_run"], 1, 25)
        record = {
            "id": run_id,
            "run_id": run_id,
            "status": "created",
            "category": payload.get("category"),
            "max_urls_per_run": max_urls,
            "max_pages_per_domain_per_run": self._bounded_int(
                payload.get("max_pages_per_domain_per_run"),
                DEFAULT_LIMITS["max_pages_per_domain_per_run"],
                1,
                10,
            ),
            "timeout_seconds": self._bounded_int(payload.get("timeout_seconds"), DEFAULT_LIMITS["timeout_seconds"], 3, 30),
            "max_content_bytes": self._bounded_int(payload.get("max_content_bytes"), DEFAULT_LIMITS["max_content_bytes"], 10000, 1_000_000),
            "daily_url_limit": self._bounded_int(payload.get("daily_url_limit"), DEFAULT_LIMITS["daily_url_limit"], 1, 200),
            "results": [],
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "warnings": [
                "Runs are manual and bounded. No uncontrolled crawling or background scheduler is started.",
            ],
        }
        return self.storage.save_record("learning_url_ingest_runs", record)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.storage.list_records("learning_url_ingest_runs", max(1, min(limit, 200)))

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.storage.get_record("learning_url_ingest_runs", run_id)

    def start_run(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            return {"ok": False, "error": "Learning run not found."}
        if run.get("status") in {"stopped", "completed"}:
            return {"ok": False, "error": f"Run is already {run.get('status')}."}

        used_today = self._used_today()
        daily_limit = int(run.get("daily_url_limit") or DEFAULT_LIMITS["daily_url_limit"])
        remaining_today = max(0, daily_limit - used_today)
        if remaining_today <= 0:
            updated = self.storage.update_record(
                "learning_url_ingest_runs",
                run_id,
                {"status": "paused", "warnings": ["Daily URL learning limit reached."], "updated_at": utc_now_iso()},
            )
            return {"ok": False, "error": "Daily URL learning limit reached.", "run": updated}

        max_urls = min(int(run.get("max_urls_per_run") or DEFAULT_LIMITS["max_urls_per_run"]), remaining_today)
        selected = self.packs.select_urls_for_run(
            category=run.get("category"),
            limit=max_urls,
            max_pages_per_domain=int(run.get("max_pages_per_domain_per_run") or DEFAULT_LIMITS["max_pages_per_domain_per_run"]),
        )
        results: list[dict[str, Any]] = []
        self.storage.update_record("learning_url_ingest_runs", run_id, {"status": "running", "started_at": utc_now_iso()})
        for item in selected:
            result = self._ingest_one(item, run)
            results.append(result)
            if result.get("learned"):
                self.packs.update_url_status(
                    item["id"],
                    {
                        "status": "learned",
                        "last_attempt_at": result.get("retrieved_at") or utc_now_iso(),
                        "last_success_at": result.get("retrieved_at") or utc_now_iso(),
                        "failure_reason": None,
                    },
                )
            else:
                status = "blocked" if result.get("blocked_reason") else "failed"
                self.packs.update_url_status(
                    item["id"],
                    {
                        "status": status,
                        "last_attempt_at": utc_now_iso(),
                        "failure_reason": result.get("failure_reason") or result.get("blocked_reason"),
                    },
                )
                self.storage.save_record(
                    "learning_url_failures",
                    {
                        "id": f"learning_url_failure_{uuid4().hex[:12]}",
                        "run_id": run_id,
                        "learning_url_id": item["id"],
                        "url": item.get("url"),
                        "domain": item.get("domain"),
                        "failure_reason": result.get("failure_reason") or result.get("blocked_reason") or "Unknown failure.",
                    },
                )

        final_status = "completed" if selected else "completed"
        updated = self.storage.update_record(
            "learning_url_ingest_runs",
            run_id,
            {
                "status": final_status,
                "selected_count": len(selected),
                "learned_count": len([item for item in results if item.get("learned")]),
                "failed_count": len([item for item in results if not item.get("learned")]),
                "results": results,
                "ended_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            },
        )
        return {"ok": True, "run": updated, "results": results}

    def pause_run(self, run_id: str) -> dict[str, Any]:
        return self._set_run_status(run_id, "paused")

    def resume_run(self, run_id: str) -> dict[str, Any]:
        return self._set_run_status(run_id, "created")

    def stop_run(self, run_id: str) -> dict[str, Any]:
        return self._set_run_status(run_id, "stopped")

    def get_status(self) -> dict[str, Any]:
        urls = self.storage.list_records("learning_urls", 20000)
        runs = self.list_runs(20)
        counts = Counter(str(item.get("status") or "pending") for item in urls)
        return {
            "enabled": True,
            "total_urls": len(urls),
            "pending": counts.get("pending", 0),
            "learned": counts.get("learned", 0),
            "failed": counts.get("failed", 0),
            "blocked": counts.get("blocked", 0),
            "runs": runs,
            "last_run": runs[0] if runs else {},
            "daily_limit": DEFAULT_LIMITS["daily_url_limit"],
            "used_today": self._used_today(),
            "background_enabled": False,
            "warnings": [
                "Manual runs are bounded by max URLs, per-domain limits, timeout, content size, and daily limit.",
                "Saved schedule settings do not create a paid Cloud Scheduler job automatically.",
            ],
        }

    def _ingest_one(self, item: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
        ingest = self.web_ingest.ingest_url(
            url=str(item.get("url") or ""),
            source_note=f"learning_url_run:{run.get('run_id')}",
            timeout_seconds=int(run.get("timeout_seconds") or DEFAULT_LIMITS["timeout_seconds"]),
            max_content_bytes=int(run.get("max_content_bytes") or DEFAULT_LIMITS["max_content_bytes"]),
        )
        knowledge = (
            self.knowledge_manager.add_url_ingest_result(ingest, url=str(item.get("url") or ""), topic=str(item.get("title") or "learning URL"))
            if ingest.get("learned")
            else {"ok": False, "knowledge_id": None}
        )
        return {
            **ingest,
            "learning_url_id": item.get("id"),
            "pack_id": item.get("pack_id"),
            "category": item.get("category"),
            "priority": item.get("priority"),
            "knowledge_id": knowledge.get("knowledge_id"),
            "saved_to_firestore": bool(self.storage.using_firestore and ingest.get("learned")),
        }

    def _set_run_status(self, run_id: str, status: str) -> dict[str, Any]:
        updated = self.storage.update_record("learning_url_ingest_runs", run_id, {"status": status, "updated_at": utc_now_iso()})
        if updated is None:
            return {"ok": False, "error": "Learning run not found."}
        return {"ok": True, "run": updated}

    def _used_today(self) -> int:
        today = utc_now_iso()[:10]
        total = 0
        for run in self.storage.list_records("learning_url_ingest_runs", 500):
            if str(run.get("started_at") or run.get("created_at") or "").startswith(today):
                total += int(run.get("selected_count") or 0)
        return total

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default
        return max(minimum, min(maximum, number))
