from __future__ import annotations

import html
import ipaddress
import re
from datetime import datetime, timezone
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from uuid import uuid4

try:
    from app.private_search import PrivateSearchService
    from app.safety import check_request_safety
    from app.storage import ProjectStorageService
except ImportError:
    from private_search import PrivateSearchService
    from safety import check_request_safety
    from storage import ProjectStorageService


class WebIngestService:
    def __init__(self, storage: ProjectStorageService, search: PrivateSearchService) -> None:
        self.storage = storage
        self.search = search

    def ingest_url(
        self,
        url: str,
        source_note: str | None = None,
        timeout_seconds: int = 8,
        max_content_bytes: int = 50000,
    ) -> dict[str, Any]:
        safety = self._validate_url(url)
        record_id = f"url_ingest_{uuid4().hex[:12]}"
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if not safety["allowed"]:
            blocked_reason = safety["reason"]
            self.storage.save_record(
                "url_ingest_records",
                {
                    "id": record_id,
                    "url": url,
                    "source_note": source_note,
                    "status": "blocked",
                    "warnings": [blocked_reason, safety["safe_alternative"]],
                    "blocked_reason": blocked_reason,
                    "failure_reason": blocked_reason,
                    "retrieved_at": retrieved_at,
                },
            )
            return {
                "id": record_id,
                "ok": False,
                "learned": False,
                "url": url,
                "final_url": "",
                "domain": "",
                "document_id": None,
                "title": "",
                "text_chars": 0,
                "chunks_created": 0,
                "saved_to_private_search": False,
                "warnings": [blocked_reason, safety["safe_alternative"]],
                "blocked_reason": blocked_reason,
                "failure_reason": blocked_reason,
            }

        try:
            request = urlrequest.Request(
                url,
                headers={"User-Agent": "BuilderCoreSafeIngest/1.0"},
                method="GET",
            )
            with urlrequest.urlopen(request, timeout=max(1, int(timeout_seconds))) as response:
                content_type = response.headers.get("Content-Type", "")
                final_url = response.geturl()
                raw_bytes = response.read(max(1000, int(max_content_bytes)))
            text = raw_bytes.decode("utf-8", errors="ignore")
            cleaned_text = self._extract_text(text)
            title = self._extract_title(text) or url
            domain = (urlparse.urlparse(final_url).hostname or urlparse.urlparse(url).hostname or "").lower()

            if not cleaned_text:
                warnings = ["The page was fetched, but readable text could not be extracted safely."]
                self.storage.save_record(
                    "url_ingest_records",
                    {
                        "id": record_id,
                        "url": url,
                        "final_url": final_url,
                        "domain": domain,
                        "source_note": source_note,
                        "status": "failed",
                        "warnings": warnings,
                        "failure_reason": warnings[0],
                        "content_type": content_type,
                        "retrieved_at": retrieved_at,
                    },
                )
                return {
                    "id": record_id,
                    "ok": False,
                    "learned": False,
                    "url": url,
                    "final_url": final_url,
                    "domain": domain,
                    "document_id": None,
                    "title": title,
                    "text_chars": 0,
                    "chunks_created": 0,
                    "saved_to_private_search": False,
                    "warnings": warnings,
                    "blocked_reason": None,
                    "failure_reason": warnings[0],
                }

            search_result = self.search.add_document_to_index(
                title=title,
                text=cleaned_text,
                source_type="url_ingest",
                url=final_url,
                metadata={"source_note": source_note or "", "content_type": content_type, "domain": domain},
                document_id=record_id,
            )
            self.storage.save_record(
                "url_ingest_records",
                {
                    "id": record_id,
                    "document_id": record_id,
                    "url": url,
                    "final_url": final_url,
                    "domain": domain,
                    "title": title,
                    "text": cleaned_text[:50000],
                    "source_note": source_note,
                    "status": "completed",
                    "content_type": content_type,
                    "text_chars": len(cleaned_text),
                    "chunks_created": search_result["chunks_created"],
                    "retrieved_at": retrieved_at,
                },
            )
            return {
                "id": record_id,
                "ok": True,
                "learned": True,
                "url": url,
                "final_url": final_url,
                "domain": domain,
                "document_id": record_id,
                "title": title,
                "text_chars": len(cleaned_text),
                "chunks_created": search_result["chunks_created"],
                "saved_to_private_search": True,
                "warnings": [],
                "blocked_reason": None,
                "failure_reason": None,
            }
        except (urlerror.URLError, TimeoutError) as error:
            failure_reason = f"URL fetch failed: {error}"
            warnings = [failure_reason]
            self.storage.save_record(
                "url_ingest_records",
                {
                    "id": record_id,
                    "url": url,
                    "source_note": source_note,
                    "status": "failed",
                    "warnings": warnings,
                    "failure_reason": failure_reason,
                    "retrieved_at": retrieved_at,
                },
            )
            return {
                "id": record_id,
                "ok": False,
                "learned": False,
                "url": url,
                "final_url": "",
                "domain": "",
                "document_id": None,
                "title": "",
                "text_chars": 0,
                "chunks_created": 0,
                "saved_to_private_search": False,
                "warnings": warnings,
                "blocked_reason": None,
                "failure_reason": failure_reason,
            }

    def _validate_url(self, url: str) -> dict[str, Any]:
        safety = check_request_safety(url, category="url_ingest")
        if not safety["allowed"]:
            return safety

        parsed = urlparse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return {
                "allowed": False,
                "risk_level": "high",
                "reason": "Only http and https URLs are allowed.",
                "safe_alternative": "Use a public http or https page instead.",
            }

        host = (parsed.hostname or "").lower()
        if not host:
            return {
                "allowed": False,
                "risk_level": "high",
                "reason": "The URL host is missing.",
                "safe_alternative": "Paste a full public URL.",
            }

        if host.endswith(".onion") or host in {"localhost", "127.0.0.1"}:
            return {
                "allowed": False,
                "risk_level": "high",
                "reason": "Builder Core blocks localhost, private hosts, and onion links.",
                "safe_alternative": "Use a public http or https URL instead.",
            }

        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return {
                    "allowed": False,
                    "risk_level": "high",
                    "reason": "Private or internal IP addresses are blocked.",
                    "safe_alternative": "Use a public website instead.",
                }
        except ValueError:
            pass

        return {
            "allowed": True,
            "risk_level": "low",
            "reason": "URL passed the safe-ingest checks.",
            "safe_alternative": "Not needed.",
        }

    def _extract_title(self, html_text: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())

    def _extract_text(self, html_text: str) -> str:
        without_scripts = re.sub(r"<script.*?>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
        without_styles = re.sub(r"<style.*?>.*?</style>", " ", without_scripts, flags=re.IGNORECASE | re.DOTALL)
        without_tags = re.sub(r"<[^>]+>", " ", without_styles)
        cleaned = html.unescape(re.sub(r"\s+", " ", without_tags)).strip()
        return cleaned[:20000]
