from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.storage import ProjectStorageService
except ImportError:
    from storage import ProjectStorageService


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "into",
    "then",
    "have",
    "will",
    "would",
    "should",
    "about",
    "after",
    "before",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PrivateSearchService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def add_document_to_index(
        self,
        title: str,
        text: str,
        source_type: str,
        url: str | None = None,
        metadata: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        document_id = document_id or f"document_{uuid4().hex[:12]}"
        clean_text = text.strip()
        chunks = self.chunk_text(clean_text)
        keywords = self.extract_keywords(f"{title}\n{clean_text}")

        document = self.storage.save_record(
            "search_documents",
            {
                "id": document_id,
                "document_id": document_id,
                "title": title.strip() or "Untitled document",
                "text": clean_text,
                "source_type": source_type,
                "url": url,
                "metadata": metadata or {},
                "keywords": keywords,
            },
        )

        for index, chunk in enumerate(chunks):
            self.storage.save_record(
                "search_chunks",
                {
                    "id": f"{document_id}_chunk_{index + 1}",
                    "document_id": document_id,
                    "title": document["title"],
                    "chunk_index": index + 1,
                    "text": chunk,
                    "source_type": source_type,
                    "url": url,
                    "keywords": self.extract_keywords(chunk),
                    "metadata": metadata or {},
                },
            )

        self.storage.save_record(
            "knowledge_base",
            {
                "id": f"knowledge_{document_id}",
                "document_id": document_id,
                "title": document["title"],
                "summary": clean_text[:500],
                "source_type": source_type,
                "url": url,
                "metadata": metadata or {},
            },
        )

        return {
            "document_id": document_id,
            "chunks_created": len(chunks),
            "saved_to_search": True,
            "saved_to_memory": True,
        }

    def chunk_text(self, text: str, max_chars: int = 1200) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        return [cleaned[index : index + max_chars] for index in range(0, len(cleaned), max_chars)]

    def extract_keywords(self, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9_]{3,}", text.lower())
        keywords: list[str] = []
        for token in tokens:
            if token in STOP_WORDS:
                continue
            if token not in keywords:
                keywords.append(token)
        return keywords[:20]

    def search_private_index(self, query: str, limit: int = 10) -> dict[str, Any]:
        if not self.storage.list_records("search_chunks", 1):
            self.rebuild_index_from_storage()

        chunks = self.storage.list_records("search_chunks", 3000)
        ranked = self.rank_results(query, chunks)[:limit]
        self.storage.save_record(
            "search_queries",
            {
                "query": query,
                "result_count": len(ranked),
                "top_sources": [item.get("title") for item in ranked[:3]],
            },
        )

        return {
            "query": query,
            "results_count": len(ranked),
            "results": ranked,
            "top_sources": [item.get("title") for item in ranked[:3]],
        }

    def rank_results(self, query: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        query_lower = query.lower()
        query_words = set(self.extract_keywords(query))
        ranked: list[dict[str, Any]] = []

        for document in documents:
            title = str(document.get("title") or "")
            text = str(document.get("text") or "")
            keywords = set(document.get("keywords") or [])
            score = 0

            if query_lower in title.lower():
                score += 8
            if query_lower in text.lower():
                score += 6

            overlap = len(query_words.intersection(set(self.extract_keywords(f"{title} {text}"))))
            keyword_overlap = len(query_words.intersection(keywords))
            score += overlap * 2
            score += keyword_overlap * 2

            source_type = str(document.get("source_type") or "")
            if source_type in {"project_memory", "assistant_memory", "learning_lesson"}:
                score += 2

            created_at = str(document.get("created_at") or "")
            if created_at:
                score += 1

            if score <= 0:
                continue

            ranked.append(
                {
                    **document,
                    "score": score,
                    "preview": text[:240],
                }
            )

        return sorted(ranked, key=lambda item: item.get("score", 0), reverse=True)

    def rebuild_index_from_storage(self) -> dict[str, Any]:
        source_map = {
            "project_memory": lambda record: str(record.get("note") or record.get("command") or ""),
            "assistant_memory": lambda record: str(record.get("assistant_reply") or record.get("note") or ""),
            "research_results": lambda record: " ".join(record.get("findings", []) or []) + " " + str(record.get("summary") or ""),
            "learning_lessons": lambda record: str(record.get("lesson_learned") or "") + " " + str(record.get("next_recommendation") or ""),
            "codex_summaries": lambda record: str(record.get("codex_summary") or record.get("message") or ""),
            "market_analysis": lambda record: str(record.get("market_summary") or ""),
            "app_plans": lambda record: str(record.get("app_concept") or ""),
            "document_ingest": lambda record: str(record.get("text") or ""),
            "url_ingest_records": lambda record: str(record.get("text") or ""),
        }

        created = 0
        existing_document_ids = {item.get("document_id") for item in self.storage.list_records("search_documents", 1000)}

        for collection, text_builder in source_map.items():
            for record in self.storage.list_records(collection, 200):
                source_id = str(record.get("id") or record.get("document_id") or "")
                if not source_id:
                    continue
                document_id = f"source_{collection}_{source_id}"
                if document_id in existing_document_ids:
                    continue

                title = str(record.get("title") or record.get("note") or record.get("command") or collection)
                text = text_builder(record).strip()
                if not text:
                    continue

                self.add_document_to_index(
                    title=title,
                    text=text,
                    source_type=collection,
                    url=record.get("url"),
                    metadata={"source_collection": collection, "source_record_id": source_id},
                    document_id=document_id,
                )
                existing_document_ids.add(document_id)
                created += 1

        return {
            "ok": True,
            "documents_added": created,
            "checked_at": utc_now_iso(),
        }

    def get_search_status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "document_count": len(self.storage.list_records("search_documents", 2000)),
            "chunk_count": len(self.storage.list_records("search_chunks", 5000)),
            "query_count": len(self.storage.list_records("search_queries", 500)),
            "knowledge_entries": len(self.storage.list_records("knowledge_base", 2000)),
            "status_message": "Builder Core private search is ready. It searches saved knowledge and indexed documents only.",
            "checked_at": utc_now_iso(),
        }
