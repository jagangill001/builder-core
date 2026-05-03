from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from app.private_search import PrivateSearchService
    from app.storage import ProjectStorageService
except ImportError:
    from private_search import PrivateSearchService
    from storage import ProjectStorageService


SOURCE_TYPES = {
    "manual_note",
    "pasted_text",
    "public_url",
    "project_doc",
    "code_note",
    "market_note",
    "business_note",
    "legal_note",
    "medical_info_note",
    "security_note",
    "teaching_note",
    "trucking_note",
    "exam_note",
    "codex_summary",
    "agent_result",
    "research_result",
    "seed_pack",
}

CATEGORIES = {
    "general",
    "code",
    "business",
    "market",
    "law",
    "medical_info",
    "security",
    "teaching",
    "exam",
    "trucking",
    "project",
    "ai_os",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: str, limit: int = 50000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


class KnowledgeManagerService:
    def __init__(self, storage: ProjectStorageService, private_search: PrivateSearchService, repo_root: Path | None = None) -> None:
        self.storage = storage
        self.private_search = private_search
        self.repo_root = repo_root

    def add_knowledge_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        content = _clean_text(str(entry.get("content") or ""))
        title = _clean_text(str(entry.get("title") or ""), 180) or self._title_from_content(content)
        if not content:
            return {
                "ok": False,
                "knowledge_id": None,
                "saved_to_firestore": False,
                "saved_to_private_search": False,
                "chunks_created": 0,
                "summary": "",
                "key_points": [],
                "warnings": ["Knowledge content is empty."],
            }

        source_type = str(entry.get("source_type") or "manual_note").strip() or "manual_note"
        if source_type not in SOURCE_TYPES:
            source_type = "manual_note"

        category = str(entry.get("category") or "").strip() or self.classify_knowledge(content)
        if category not in CATEGORIES:
            category = self.classify_knowledge(content)

        now = utc_now_iso()
        knowledge_id = str(entry.get("knowledge_id") or entry.get("id") or f"knowledge_{uuid4().hex[:12]}").strip()
        summary = str(entry.get("summary") or self.summarize_knowledge_entry({"content": content}))
        key_points = entry.get("key_points") if isinstance(entry.get("key_points"), list) else self.extract_key_points(content)
        tags = list(dict.fromkeys([str(tag).strip().lower() for tag in (entry.get("tags") or self.tag_knowledge(content)) if str(tag).strip()]))[:12]
        source_url = str(entry.get("source_url") or entry.get("url") or "").strip() or None
        confidence = str(entry.get("confidence") or self._entry_confidence(content, source_type, source_url))

        record = {
            "id": knowledge_id,
            "knowledge_id": knowledge_id,
            "title": title,
            "content": content,
            "source_type": source_type,
            "category": category,
            "tags": tags,
            "summary": summary,
            "key_points": key_points,
            "confidence": confidence,
            "source_url": source_url,
            "created_at": str(entry.get("created_at") or now),
            "updated_at": now,
        }
        saved = self.storage.save_record("knowledge_base", record)
        self.storage.save_record(
            "knowledge_sources",
            {
                "id": f"knowledge_source_{knowledge_id}",
                "knowledge_id": knowledge_id,
                "source_type": source_type,
                "source_url": source_url,
                "title": title,
                "created_at": now,
            },
        )
        for tag in tags:
            self.storage.save_record(
                "knowledge_tags",
                {
                    "id": f"knowledge_tag_{tag}_{knowledge_id}"[:180],
                    "knowledge_id": knowledge_id,
                    "tag": tag,
                    "category": category,
                },
            )

        chunks_created = self._save_knowledge_chunks(saved)
        search_result = self.save_knowledge_to_private_search(saved)
        self.create_lesson_from_knowledge(saved)
        return {
            "ok": True,
            "knowledge_id": saved["id"],
            "saved_to_firestore": bool(self.storage.using_firestore),
            "saved_to_private_search": bool(search_result.get("saved_to_search")),
            "chunks_created": chunks_created,
            "summary": summary,
            "key_points": key_points,
            "created_at": saved.get("created_at"),
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "entry": saved,
        }

    def list_knowledge(self, limit: int = 50, category: str | None = None) -> list[dict[str, Any]]:
        records = [item for item in self.storage.list_records("knowledge_base", max(1, min(limit * 3, 500))) if item.get("knowledge_id")]
        if category:
            records = [item for item in records if item.get("category") == category]
        return records[: max(1, min(limit, 100))]

    def get_knowledge_entry(self, knowledge_id: str) -> dict[str, Any] | None:
        record = self.storage.get_record("knowledge_base", knowledge_id)
        if record and record.get("knowledge_id"):
            return record
        for item in self.storage.list_records("knowledge_base", 500):
            if item.get("knowledge_id") == knowledge_id:
                return item
        return None

    def search_knowledge(self, query: str, limit: int = 10) -> dict[str, Any]:
        query = _clean_text(query, 500)
        records = self.list_knowledge(limit=500)
        ranked = self._rank_knowledge(query, records)[: max(1, min(limit, 25))]
        private_result = self.private_search.search_private_index(query, limit=max(1, min(limit, 20)))
        sources = [item.get("title") for item in ranked if item.get("title")]
        sources.extend(private_result.get("top_sources", []))
        confidence = self.calculate_confidence(ranked, query)
        missing = []
        if not ranked and not private_result.get("results_count"):
            missing.append("No saved knowledge matched this question yet.")
        elif confidence != "high":
            missing.append("Add more notes or safe public URLs to strengthen this answer.")
        return {
            "query": query,
            "results": ranked,
            "private_search": private_result,
            "sources_used": list(dict.fromkeys([str(source) for source in sources if source]))[:12],
            "confidence": confidence,
            "missing_knowledge": missing,
            "storage_used": "firestore" if self.storage.using_firestore else "local",
        }

    def summarize_knowledge_entry(self, entry: dict[str, Any]) -> str:
        content = _clean_text(str(entry.get("content") or entry.get("text") or ""), 800)
        if len(content) <= 320:
            return content
        sentence_parts = re.split(r"(?<=[.!?])\s+", content)
        summary = " ".join(sentence_parts[:3]).strip()
        return summary[:500] if summary else content[:500]

    def extract_key_points(self, text: str) -> list[str]:
        cleaned = _clean_text(text, 4000)
        candidates = re.split(r"(?<=[.!?])\s+|\n+|;\s+", cleaned)
        points = []
        for candidate in candidates:
            candidate = candidate.strip(" -")
            if len(candidate) < 28:
                continue
            points.append(candidate[:220])
            if len(points) >= 5:
                break
        return points or ([cleaned[:220]] if cleaned else [])

    def classify_knowledge(self, text: str) -> str:
        lowered = text.lower()
        keyword_map = [
            ("security", ["security", "firewall", "rate limit", "incident", "admin key", "x-admin-key"]),
            ("trucking", ["trucking", "dispatch", "load board", "owner-operator", "fuel cost", "profit per mile"]),
            ("business", ["business", "revenue", "customer", "market", "profit", "mvp"]),
            ("market", ["competitor", "market", "trend", "industry"]),
            ("code", ["python", "typescript", "frontend", "backend", "route", "firestore", "api"]),
            ("law", ["legal", "law", "contract", "compliance"]),
            ("medical_info", ["medical", "health", "diagnosis", "treatment"]),
            ("teaching", ["teach", "lesson", "practice", "quiz", "study"]),
            ("exam", ["exam", "syllabus", "revision"]),
            ("ai_os", ["builder core os", "agent", "model router", "platform adapter"]),
            ("project", ["builder core", "project progress", "command center"]),
        ]
        for category, keywords in keyword_map:
            if any(keyword in lowered for keyword in keywords):
                return category
        return "general"

    def tag_knowledge(self, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", text.lower())
        stop_words = {"that", "this", "with", "from", "have", "will", "should", "about", "into", "builder", "core"}
        tags: list[str] = []
        for token in tokens:
            if token in stop_words or token in tags:
                continue
            tags.append(token)
            if len(tags) >= 8:
                break
        category = self.classify_knowledge(text)
        if category != "general" and category not in tags:
            tags.insert(0, category)
        return tags[:10]

    def save_knowledge_to_private_search(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.private_search.add_document_to_index(
            title=str(entry.get("title") or "Knowledge entry"),
            text=str(entry.get("content") or entry.get("summary") or ""),
            source_type=str(entry.get("source_type") or "manual_note"),
            url=entry.get("source_url"),
            metadata={
                "knowledge_id": entry.get("knowledge_id") or entry.get("id"),
                "category": entry.get("category"),
                "tags": entry.get("tags") or [],
            },
            document_id=f"knowledge_search_{entry.get('knowledge_id') or entry.get('id')}",
        )

    def create_lesson_from_knowledge(self, entry: dict[str, Any]) -> dict[str, Any]:
        lesson = {
            "task_id": f"lesson_{entry.get('knowledge_id') or entry.get('id')}",
            "command": entry.get("title"),
            "lesson_learned": entry.get("summary") or str(entry.get("content") or "")[:500],
            "next_recommendation": "Use this saved knowledge in future Builder Core answers and mention source limits honestly.",
            "source_type": entry.get("source_type"),
            "source_url": entry.get("source_url"),
            "status": "completed",
        }
        return self.storage.save_record("learning_lessons", lesson)

    def add_url_ingest_result(self, ingest_result: dict[str, Any], url: str, topic: str | None = None) -> dict[str, Any]:
        if not ingest_result.get("ok") or not ingest_result.get("document_id"):
            return {"ok": False, "knowledge_id": None, "warnings": ingest_result.get("warnings", [])}
        record = self.storage.get_record("url_ingest_records", str(ingest_result.get("document_id"))) or {}
        content = str(record.get("text") or "")
        return self.add_knowledge_entry(
            {
                "knowledge_id": f"knowledge_url_{ingest_result.get('document_id')}",
                "title": ingest_result.get("title") or record.get("title") or topic or url,
                "content": content or str(ingest_result.get("title") or url),
                "source_type": "public_url",
                "category": self.classify_knowledge(f"{topic or ''} {content}"),
                "tags": self.tag_knowledge(f"{topic or ''} {content}"),
                "source_url": url,
                "confidence": "medium" if content else "low",
            }
        )

    def get_status(self) -> dict[str, Any]:
        entries = self.list_knowledge(limit=1000)
        categories: dict[str, int] = {}
        tags: list[str] = []
        for entry in entries:
            category = str(entry.get("category") or "general")
            categories[category] = categories.get(category, 0) + 1
            tags.extend([str(tag) for tag in entry.get("tags", []) if tag])
        search_status = self.private_search.get_search_status()
        seed_records = [item for item in entries if item.get("source_type") == "seed_pack"]
        return {
            "total_entries": len(entries),
            "categories": categories,
            "tags": sorted(set(tags))[:50],
            "private_search_documents": search_status.get("document_count", 0),
            "private_search_chunks": search_status.get("chunk_count", 0),
            "knowledge_seed_status": {
                "seed_entries": len(seed_records),
                "seeded": len(seed_records) > 0,
            },
            "storage_used": "firestore" if self.storage.using_firestore else "local",
            "last_updated": entries[0].get("updated_at") if entries else utc_now_iso(),
        }

    def scan_project_files(self) -> dict[str, Any]:
        if self.repo_root is None:
            return {"ok": False, "files_scanned": [], "knowledge_entries_created": 0, "warnings": ["Repo root is not configured."]}
        safe_files = [
            self.repo_root / "README.md",
            self.repo_root / "COMMAND_CENTER.md",
            self.repo_root / "PROJECT_PROGRESS.md",
            self.repo_root / "frontend" / "src" / "app" / "page.tsx",
        ]
        app_dir = self.repo_root / "backend" / "app"
        if app_dir.exists():
            safe_files.extend(sorted(app_dir.glob("*.py")))

        files_scanned: list[str] = []
        created = 0
        warnings: list[str] = []
        for path in safe_files:
            try:
                resolved = path.resolve()
                if not resolved.exists() or not resolved.is_file():
                    continue
                if any(part in {".env", "node_modules", "venv", ".venv", "runtime_data", ".next", "__pycache__"} for part in resolved.parts):
                    continue
                text = resolved.read_text(encoding="utf-8", errors="ignore")[:12000]
                if not text.strip():
                    continue
                relative = str(resolved.relative_to(self.repo_root))
                summary = self._summarize_project_file(relative, text)
                self.add_knowledge_entry(
                    {
                        "knowledge_id": f"knowledge_project_{re.sub(r'[^A-Za-z0-9_]+', '_', relative)[:120]}",
                        "title": f"Project file summary: {relative}",
                        "content": summary,
                        "source_type": "project_doc" if resolved.suffix.lower() in {".md", ".tsx"} else "code_note",
                        "category": "project" if resolved.suffix.lower() == ".md" else "code",
                        "tags": ["project", "builder-core", resolved.suffix.lower().strip(".") or "file"],
                        "confidence": "medium",
                    }
                )
                files_scanned.append(relative)
                created += 1
            except Exception as error:
                warnings.append(f"Skipped {path.name}: {error}")

        self.storage.save_record(
            "knowledge_scan_records",
            {
                "id": f"knowledge_scan_{uuid4().hex[:12]}",
                "files_scanned": files_scanned,
                "knowledge_entries_created": created,
                "warnings": warnings,
            },
        )
        return {"ok": True, "files_scanned": files_scanned, "knowledge_entries_created": created, "warnings": warnings}

    def calculate_confidence(self, results: list[dict[str, Any]], query: str = "") -> str:
        if not results:
            return "low"
        clear_sources = [item for item in results if len(str(item.get("content") or item.get("summary") or "")) > 180]
        source_types = {item.get("source_type") for item in results}
        has_url = any(item.get("source_url") for item in results)
        if len(results) >= 3 and len(clear_sources) >= 2 and (has_url or len(source_types) >= 2):
            return "high"
        return "medium"

    def _save_knowledge_chunks(self, entry: dict[str, Any]) -> int:
        chunks = self.private_search.chunk_text(str(entry.get("content") or ""), max_chars=1200)
        knowledge_id = str(entry.get("knowledge_id") or entry.get("id"))
        for index, chunk in enumerate(chunks):
            self.storage.save_record(
                "knowledge_chunks",
                {
                    "id": f"{knowledge_id}_knowledge_chunk_{index + 1}",
                    "knowledge_id": knowledge_id,
                    "chunk_index": index + 1,
                    "title": entry.get("title"),
                    "text": chunk,
                    "category": entry.get("category"),
                    "source_type": entry.get("source_type"),
                    "source_url": entry.get("source_url"),
                },
            )
        return len(chunks)

    def _rank_knowledge(self, query: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        query_words = set(re.findall(r"[A-Za-z0-9_]{3,}", query.lower()))
        ranked: list[dict[str, Any]] = []
        for record in records:
            title = str(record.get("title") or "")
            content = str(record.get("content") or "")
            combined = f"{title} {content} {' '.join(record.get('tags', []) or [])}".lower()
            score = 0
            if query.lower() and query.lower() in combined:
                score += 8
            score += len(query_words.intersection(set(re.findall(r"[A-Za-z0-9_]{3,}", combined)))) * 2
            if record.get("source_type") == "seed_pack":
                score += 1
            if record.get("source_url"):
                score += 1
            if score <= 0:
                continue
            ranked.append({**record, "score": score, "preview": content[:260]})
        return sorted(ranked, key=lambda item: item.get("score", 0), reverse=True)

    def _entry_confidence(self, content: str, source_type: str, source_url: str | None) -> str:
        if len(content) > 1000 and (source_url or source_type == "seed_pack"):
            return "medium"
        if len(content) > 300:
            return "medium"
        return "low"

    def _title_from_content(self, content: str) -> str:
        first = content.split(".")[0].strip()
        return first[:120] or "Untitled knowledge"

    def _summarize_project_file(self, relative_path: str, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        interesting = []
        for line in lines:
            if line.startswith(("def ", "class ", "@app.", "export default", "function ", "const ", "#", "##")):
                interesting.append(line[:220])
            if len(interesting) >= 40:
                break
        body = "\n".join(interesting) if interesting else "\n".join(lines[:30])
        return f"{relative_path}\n\nSafe project scan summary:\n{body[:5000]}"
