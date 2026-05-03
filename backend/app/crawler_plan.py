from __future__ import annotations

from typing import Any
from uuid import uuid4

try:
    from app.storage import ProjectStorageService
    from app.web_ingest import WebIngestService
except ImportError:
    from storage import ProjectStorageService
    from web_ingest import WebIngestService


class CrawlerPlanService:
    def __init__(self, storage: ProjectStorageService, web_ingest: WebIngestService) -> None:
        self.storage = storage
        self.web_ingest = web_ingest

    def validate_crawl_safety(self, url: str) -> dict[str, Any]:
        return self.web_ingest._validate_url(url)

    def explain_crawl_limits(self) -> list[str]:
        return [
            "Builder Core crawl planning must respect robots.txt and public-only access.",
            "No private pages, logins, paywall bypass, or dark web targets are allowed.",
            "The current build creates plans only. It does not run uncontrolled crawling.",
            "Future crawls should rate-limit requests and save summaries plus source links only.",
        ]

    def create_crawl_plan(self, seed_urls: list[str], max_pages: int, topic: str | None = None) -> dict[str, Any]:
        valid_urls: list[str] = []
        warnings: list[str] = []

        for url in seed_urls:
            safety = self.validate_crawl_safety(url)
            if safety["allowed"]:
                valid_urls.append(url)
            else:
                warnings.append(f"{url}: {safety['reason']}")

        plan_id = f"crawler_plan_{uuid4().hex[:12]}"
        allowed = bool(valid_urls) and not any("private" in warning.lower() or "onion" in warning.lower() for warning in warnings)
        plan = {
            "id": plan_id,
            "plan_id": plan_id,
            "allowed": allowed,
            "seed_urls": valid_urls,
            "topic": topic or "general",
            "max_pages": max(1, min(max_pages, 25)),
            "status": "planned",
            "safety_rules": self.explain_crawl_limits(),
            "limits": self.explain_crawl_limits(),
            "warnings": warnings,
            "steps": [
                "Validate public URLs and robots rules first.",
                "Fetch a small number of public pages with a visible rate limit.",
                "Save summaries and source links into Builder Core private search only.",
                "Run execution only after explicit user approval and safe executor setup.",
            ],
            "future_execution_requirements": [
                "robots.txt respect",
                "rate limits",
                "allowlist domains",
                "max pages",
                "Cloud Run Jobs",
                "Cloud Scheduler only after user approval",
            ],
        }
        self.storage.save_record("crawler_plans", plan)
        return plan
