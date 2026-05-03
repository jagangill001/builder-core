from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from urllib import parse as urlparse
from uuid import uuid4

try:
    from app.storage import ProjectStorageService
    from app.web_ingest import WebIngestService
except ImportError:
    from storage import ProjectStorageService
    from web_ingest import WebIngestService


CATEGORIES = {
    "coding",
    "finance",
    "government",
    "market",
    "business",
    "history",
    "news",
    "public_data",
    "education",
    "security_defensive",
    "ai",
    "cloud",
    "law",
    "logistics",
    "health_info",
    "engineering",
    "general",
}

PRIORITIES = {"low", "medium", "high"}


STARTER_PACKS: dict[str, dict[str, Any]] = {
    "coding_basics": {
        "name": "Coding basics",
        "category": "coding",
        "urls": [
            ("MDN Learn Web Development", "https://developer.mozilla.org/en-US/docs/Learn"),
            ("Git Book", "https://git-scm.com/book/en/v2"),
            ("The Twelve-Factor App", "https://12factor.net/"),
            ("Refactoring Guru Design Patterns", "https://refactoring.guru/design-patterns"),
            ("Web.dev Learn", "https://web.dev/learn"),
        ],
    },
    "python": {
        "name": "Python",
        "category": "coding",
        "urls": [
            ("Python Tutorial", "https://docs.python.org/3/tutorial/"),
            ("Python Standard Library", "https://docs.python.org/3/library/"),
            ("Python Packaging Tutorial", "https://packaging.python.org/en/latest/tutorials/packaging-projects/"),
            ("Python Learn", "https://www.learnpython.org/"),
            ("Real Python Basics", "https://realpython.com/python-basics/"),
        ],
    },
    "fastapi_backend": {
        "name": "FastAPI/backend",
        "category": "coding",
        "urls": [
            ("FastAPI Tutorial", "https://fastapi.tiangolo.com/tutorial/"),
            ("FastAPI Deployment", "https://fastapi.tiangolo.com/deployment/"),
            ("Starlette", "https://www.starlette.io/"),
            ("Pydantic", "https://docs.pydantic.dev/latest/"),
            ("Uvicorn", "https://www.uvicorn.org/"),
        ],
    },
    "javascript_typescript": {
        "name": "JavaScript/TypeScript",
        "category": "coding",
        "urls": [
            ("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
            ("TypeScript Docs", "https://www.typescriptlang.org/docs/"),
            ("JavaScript Info", "https://javascript.info/"),
            ("Node Learn", "https://nodejs.org/en/learn"),
            ("NPM Docs", "https://docs.npmjs.com/"),
        ],
    },
    "react_next_frontend": {
        "name": "React/Next.js/frontend",
        "category": "coding",
        "urls": [
            ("React Learn", "https://react.dev/learn"),
            ("Next.js Docs", "https://nextjs.org/docs"),
            ("Next.js Learn", "https://nextjs.org/learn"),
            ("MDN HTML", "https://developer.mozilla.org/en-US/docs/Web/HTML"),
            ("MDN CSS", "https://developer.mozilla.org/en-US/docs/Web/CSS"),
        ],
    },
    "databases_storage": {
        "name": "Databases/storage",
        "category": "cloud",
        "urls": [
            ("Firebase Firestore", "https://firebase.google.com/docs/firestore"),
            ("Google Cloud Firestore", "https://cloud.google.com/firestore/docs"),
            ("PostgreSQL Docs", "https://www.postgresql.org/docs/"),
            ("SQLite Docs", "https://www.sqlite.org/docs.html"),
            ("Supabase Docs", "https://supabase.com/docs"),
        ],
    },
    "google_cloud_deployment": {
        "name": "Google Cloud/deployment",
        "category": "cloud",
        "urls": [
            ("Cloud Run Docs", "https://cloud.google.com/run/docs"),
            ("Cloud Build Docs", "https://cloud.google.com/build/docs"),
            ("Artifact Registry Docs", "https://cloud.google.com/artifact-registry/docs"),
            ("IAM Docs", "https://cloud.google.com/iam/docs"),
            ("Secret Manager Docs", "https://cloud.google.com/secret-manager/docs"),
        ],
    },
    "git_github": {
        "name": "Git/GitHub",
        "category": "coding",
        "urls": [
            ("GitHub Get Started", "https://docs.github.com/en/get-started"),
            ("GitHub Actions", "https://docs.github.com/en/actions"),
            ("GitHub REST API", "https://docs.github.com/en/rest"),
            ("GitHub Copilot Docs", "https://docs.github.com/en/copilot"),
            ("Git Book", "https://git-scm.com/book/en/v2"),
        ],
    },
    "ai_ml_basics": {
        "name": "AI/ML basics",
        "category": "ai",
        "urls": [
            ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
            ("Scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html"),
            ("PyTorch Tutorials", "https://pytorch.org/tutorials/"),
            ("Hugging Face Docs", "https://huggingface.co/docs"),
            ("TensorFlow Learn", "https://www.tensorflow.org/learn"),
        ],
    },
    "local_models_llm_tools": {
        "name": "Local models/LLM tools",
        "category": "ai",
        "urls": [
            ("Ollama", "https://ollama.com/"),
            ("llama.cpp", "https://github.com/ggerganov/llama.cpp"),
            ("Transformers Docs", "https://huggingface.co/docs/transformers"),
            ("LangChain Docs", "https://python.langchain.com/docs/"),
            ("LlamaIndex Docs", "https://docs.llamaindex.ai/"),
        ],
    },
    "defensive_security_learning": {
        "name": "Defensive security learning",
        "category": "security_defensive",
        "urls": [
            ("OWASP Top Ten", "https://owasp.org/www-project-top-ten/"),
            ("OWASP Cheat Sheets", "https://cheatsheetseries.owasp.org/"),
            ("Google Security Architecture", "https://cloud.google.com/architecture/framework/security"),
            ("CISA Resources", "https://www.cisa.gov/resources-tools"),
            ("NIST Cybersecurity Framework", "https://www.nist.gov/cyberframework"),
        ],
    },
    "business_startup_product": {
        "name": "Business/startup/product",
        "category": "business",
        "urls": [
            ("Y Combinator Library", "https://www.ycombinator.com/library"),
            ("Strategyzer Library", "https://www.strategyzer.com/library"),
            ("ProductPlan Learn", "https://www.productplan.com/learn/"),
            ("Atlassian Agile", "https://www.atlassian.com/agile"),
            ("Intercom Resources", "https://www.intercom.com/resources"),
        ],
    },
    "finance_markets_education": {
        "name": "Finance/markets education",
        "category": "finance",
        "urls": [
            ("SEC Investor", "https://www.investor.gov/"),
            ("FINRA Investors", "https://www.finra.org/investors"),
            ("Federal Reserve Education", "https://www.federalreserveeducation.org/"),
            ("CFTC Learn", "https://www.cftc.gov/LearnAndProtect/index.htm"),
            ("BLS Economy", "https://www.bls.gov/"),
        ],
    },
    "government_public_data": {
        "name": "Government/public data portals",
        "category": "public_data",
        "urls": [
            ("Data.gov", "https://data.gov/"),
            ("USA.gov", "https://www.usa.gov/"),
            ("Census Data", "https://www.census.gov/data.html"),
            ("World Bank Data", "https://data.worldbank.org/"),
            ("OECD Data", "https://data.oecd.org/"),
        ],
    },
    "news_public_information": {
        "name": "News/public information sources",
        "category": "news",
        "urls": [
            ("Associated Press", "https://apnews.com/"),
            ("Reuters", "https://www.reuters.com/"),
            ("BBC News", "https://www.bbc.com/news"),
            ("NPR", "https://www.npr.org/"),
            ("The Conversation", "https://theconversation.com/"),
        ],
    },
    "history_public_archives": {
        "name": "History/public archives",
        "category": "history",
        "urls": [
            ("Library of Congress", "https://www.loc.gov/"),
            ("National Archives", "https://www.archives.gov/"),
            ("Smithsonian", "https://www.si.edu/"),
            ("Internet Archive", "https://archive.org/"),
            ("Project Gutenberg", "https://www.gutenberg.org/"),
        ],
    },
    "logistics_trucking_business": {
        "name": "Logistics/trucking/business",
        "category": "logistics",
        "urls": [
            ("FMCSA", "https://www.fmcsa.dot.gov/"),
            ("BTS Freight", "https://www.bts.gov/topics/freight-transportation"),
            ("DAT Freight Insights", "https://www.dat.com/blog"),
            ("OOIDA", "https://www.ooida.com/"),
            ("SBA Business Guide", "https://www.sba.gov/business-guide"),
        ],
    },
    "teaching_learning_resources": {
        "name": "Teaching/learning resources",
        "category": "education",
        "urls": [
            ("UNC Learning Center", "https://learningcenter.unc.edu/tips-and-tools/"),
            ("Learning How to Learn", "https://www.coursera.org/articles/learning-how-to-learn"),
            ("MIT OpenCourseWare", "https://ocw.mit.edu/"),
            ("Khan Academy", "https://www.khanacademy.org/"),
            ("edX Learn", "https://www.edx.org/learn"),
        ],
    },
    "engineering_system_design": {
        "name": "Engineering/system design",
        "category": "engineering",
        "urls": [
            ("Martin Fowler Architecture", "https://martinfowler.com/architecture/"),
            ("Django Design Philosophies", "https://docs.djangoproject.com/en/stable/misc/design-philosophies/"),
            ("Microservices Patterns", "https://microservices.io/patterns/"),
            ("Google Cloud Architecture", "https://cloud.google.com/architecture"),
            ("AWS Architecture Center", "https://aws.amazon.com/architecture/"),
        ],
    },
    "safety_limits": {
        "name": "Legal/medical/finance safety limits",
        "category": "law",
        "urls": [
            ("FTC Business Guidance", "https://www.ftc.gov/business-guidance"),
            ("FDA Health Information", "https://www.fda.gov/consumers"),
            ("MedlinePlus", "https://medlineplus.gov/"),
            ("SEC Investor Alerts", "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins"),
            ("FindLaw Legal Information", "https://www.findlaw.com/"),
        ],
    },
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_domain(url: str) -> str:
    return (urlparse.urlparse(url).hostname or "").lower()


class LearningUrlPackService:
    def __init__(self, storage: ProjectStorageService, web_ingest: WebIngestService) -> None:
        self.storage = storage
        self.web_ingest = web_ingest

    def import_urls(self, payload: Any) -> dict[str, Any]:
        confirm = bool(payload.get("confirm")) if isinstance(payload, dict) else False
        if not confirm:
            return {"ok": False, "saved_count": 0, "warnings": ["confirm=true is required."], "items": []}
        pack_id = str(payload.get("pack_id") or f"url_pack_{uuid4().hex[:10]}") if isinstance(payload, dict) else f"url_pack_{uuid4().hex[:10]}"
        pack_name = str(payload.get("pack_name") or payload.get("name") or pack_id) if isinstance(payload, dict) else pack_id
        items = self._extract_import_items(payload)
        saved, blocked = self._save_items(pack_id=pack_id, pack_name=pack_name, items=items)
        if isinstance(payload, dict) and payload.get("run_now"):
            return {**saved, "run_now_requested": True, "note": "Import saved pending URLs. Create/start a learning run to ingest within limits."}
        return {**saved, "blocked": blocked}

    def seed_starter_packs(self, confirm: bool) -> dict[str, Any]:
        if not confirm:
            return {"ok": False, "seeded_packs": 0, "saved_urls": 0, "warnings": ["confirm=true is required."]}
        total_urls = 0
        seeded = 0
        updated = 0
        for pack_id, pack in STARTER_PACKS.items():
            items = [
                {"title": title, "url": url, "category": pack["category"], "priority": "high" if index == 0 else "medium"}
                for index, (title, url) in enumerate(pack["urls"])
            ]
            existing = self.storage.get_record("learning_url_packs", pack_id)
            result, _blocked = self._save_items(pack_id=pack_id, pack_name=pack["name"], items=items)
            total_urls += result.get("saved_count", 0)
            if existing:
                updated += 1
            else:
                seeded += 1
        return {
            "ok": True,
            "seeded_packs": seeded,
            "updated_packs": updated,
            "saved_urls": total_urls,
            "pack_count": len(STARTER_PACKS),
            "message": "Starter learning URL packs are saved as pending. They are not ingested until an admin starts a controlled run.",
            "storage_used": "firestore" if self.storage.using_firestore else "local",
        }

    def list_packs(self, limit: int = 200) -> dict[str, Any]:
        packs = self.storage.list_records("learning_url_packs", max(1, min(limit, 500)))
        return {"ok": True, "items": packs, "count": len(packs)}

    def list_urls(self, limit: int = 500, category: str | None = None, status: str | None = None) -> dict[str, Any]:
        urls = self.storage.list_records("learning_urls", max(1, min(limit, 2000)))
        if category:
            urls = [item for item in urls if item.get("category") == category]
        if status:
            urls = [item for item in urls if item.get("status") == status]
        return {"ok": True, "items": urls[:limit], "count": len(urls)}

    def update_url_status(self, url_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        return self.storage.update_record("learning_urls", url_id, updates)

    def select_urls_for_run(
        self,
        category: str | None,
        limit: int,
        max_pages_per_domain: int,
    ) -> list[dict[str, Any]]:
        candidates = [
            item
            for item in self.storage.list_records("learning_urls", 20000)
            if item.get("enabled", True) and item.get("status") in {"pending", "failed"}
        ]
        if category:
            candidates = [item for item in candidates if item.get("category") == category]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        candidates = sorted(candidates, key=lambda item: (priority_order.get(str(item.get("priority")), 9), item.get("created_at", "")))
        selected: list[dict[str, Any]] = []
        per_domain: dict[str, int] = {}
        for item in candidates:
            domain = str(item.get("domain") or normalize_domain(str(item.get("url") or "")))
            if per_domain.get(domain, 0) >= max_pages_per_domain:
                continue
            selected.append(item)
            per_domain[domain] = per_domain.get(domain, 0) + 1
            if len(selected) >= limit:
                break
        return selected

    def _extract_import_items(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        raw = str(payload.get("content") or payload.get("csv") or payload.get("json") or "").strip()
        fmt = str(payload.get("format") or "").lower()
        if not raw:
            return []
        if fmt == "csv" or raw.lower().startswith("title,url"):
            reader = csv.DictReader(io.StringIO(raw))
            return [dict(row) for row in reader]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
        return []

    def _save_items(self, pack_id: str, pack_name: str, items: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        now = utc_now_iso()
        saved_items: list[dict[str, Any]] = []
        blocked_items: list[dict[str, Any]] = []
        self.storage.save_record(
            "learning_url_packs",
            {
                "id": pack_id,
                "pack_id": pack_id,
                "name": pack_name,
                "urls_count": len(items),
                "status": "ready",
                "updated_at": now,
            },
        )
        existing_by_url = {item.get("url"): item for item in self.storage.list_records("learning_urls", 20000)}
        for item in items:
            url = str(item.get("url") or "").strip()
            safety = self.web_ingest._validate_url(url)
            if not safety.get("allowed"):
                blocked_items.append({"url": url, "reason": safety.get("reason")})
                continue
            category = str(item.get("category") or "general").strip().lower()
            priority = str(item.get("priority") or "medium").strip().lower()
            domain = normalize_domain(url)
            record_id = str(existing_by_url.get(url, {}).get("id") or f"learning_url_{uuid4().hex[:12]}")
            record = {
                "id": record_id,
                "pack_id": pack_id,
                "title": str(item.get("title") or domain or url).strip()[:220],
                "url": url,
                "domain": domain,
                "category": category if category in CATEGORIES else "general",
                "priority": priority if priority in PRIORITIES else "medium",
                "enabled": bool(item.get("enabled", True)),
                "status": str(existing_by_url.get(url, {}).get("status") or "pending"),
                "last_attempt_at": existing_by_url.get(url, {}).get("last_attempt_at"),
                "last_success_at": existing_by_url.get(url, {}).get("last_success_at"),
                "failure_reason": existing_by_url.get(url, {}).get("failure_reason"),
                "created_at": existing_by_url.get(url, {}).get("created_at") or now,
                "updated_at": now,
            }
            saved_items.append(self.storage.save_record("learning_urls", record))
        return (
            {
                "ok": True,
                "pack_id": pack_id,
                "pack_name": pack_name,
                "saved_count": len(saved_items),
                "blocked_count": len(blocked_items),
                "items": saved_items[:50],
                "storage_used": "firestore" if self.storage.using_firestore else "local",
            },
            blocked_items,
        )
