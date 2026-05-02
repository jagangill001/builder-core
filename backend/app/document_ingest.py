from __future__ import annotations

from typing import Any
from uuid import uuid4

try:
    from app.learning import LearningService
    from app.private_search import PrivateSearchService
    from app.safety import check_request_safety
    from app.storage import ProjectStorageService
except ImportError:
    from learning import LearningService
    from private_search import PrivateSearchService
    from safety import check_request_safety
    from storage import ProjectStorageService


class DocumentIngestService:
    def __init__(
        self,
        storage: ProjectStorageService,
        search: PrivateSearchService,
        learning: LearningService,
    ) -> None:
        self.storage = storage
        self.search = search
        self.learning = learning

    def ingest_text(self, title: str, text: str, source_type: str, tags: list[str] | None = None) -> dict[str, Any]:
        safety = check_request_safety(text, category=source_type)
        if not safety["allowed"]:
            return {
                "ok": False,
                "document_id": None,
                "chunks_created": 0,
                "saved_to_search": False,
                "saved_to_memory": False,
                "warnings": [safety["reason"], safety["safe_alternative"]],
            }

        document_id = f"document_{uuid4().hex[:12]}"
        record = self.storage.save_record(
            "document_ingest",
            {
                "id": document_id,
                "document_id": document_id,
                "title": title,
                "text": text,
                "source_type": source_type,
                "tags": tags or [],
                "safety": safety,
            },
        )
        search_result = self.search.add_document_to_index(
            title=title,
            text=text,
            source_type=source_type,
            metadata={"tags": tags or [], "document_id": document_id},
            document_id=document_id,
        )

        self.storage.save_project_memory(
            {
                "type": "document_ingest",
                "note": f"Ingested document: {title}",
                "document_id": document_id,
                "source_type": source_type,
            }
        )
        self.storage.save_lesson(
            {
                "task_id": document_id,
                "command": title,
                "what_happened": [f"Document ingested into private search with {search_result['chunks_created']} chunks."],
                "files_changed": [],
                "error": None,
                "lesson_learned": "Builder Core can learn from user-provided text without outside AI.",
                "next_recommendation": "Search this document from the unified command chat or create a research task from it.",
                "status": "completed",
            }
        )

        return {
            "ok": True,
            "document_id": record["document_id"],
            "chunks_created": search_result["chunks_created"],
            "saved_to_search": True,
            "saved_to_memory": True,
            "warnings": [],
        }
