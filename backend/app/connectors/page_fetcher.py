from __future__ import annotations

import logging
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from app.connectors.content_extractor import extract_readable_content
from app.connectors.page_policy import evaluate_page_url

logger = logging.getLogger(__name__)

MAX_PAGE_BYTES = 350_000
DEFAULT_TIMEOUT_SECONDS = 6
USER_AGENT = "BuilderCore/phase4-live-search (+safe-public-page-reader)"


def fetch_allowed_page(url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    decision = evaluate_page_url(url)
    if not decision.allowed:
        return {
            "opened": False,
            "url": url,
            "title": "",
            "text": "",
            "warning": decision.reason,
        }

    request = urlrequest.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1"})
    try:
        with urlrequest.urlopen(request, timeout=timeout_seconds) as response:
            content_type = str(response.headers.get("content-type") or "").lower()
            if not _content_type_allowed(content_type):
                return {
                    "opened": False,
                    "url": url,
                    "title": "",
                    "text": "",
                    "warning": "Could not open this source page.",
                }
            raw = response.read(MAX_PAGE_BYTES + 1)
    except (urlerror.URLError, TimeoutError, OSError) as error:
        logger.info("Safe page fetch failed for %s: %s", url, error)
        return {
            "opened": False,
            "url": url,
            "title": "",
            "text": "",
            "warning": "Could not open this source page.",
        }

    if len(raw) > MAX_PAGE_BYTES:
        return {
            "opened": False,
            "url": url,
            "title": "",
            "text": "",
            "warning": "Could not open this source page.",
        }

    html = raw.decode(_guess_encoding(content_type), errors="replace")
    content = extract_readable_content(html)
    if not content.get("text"):
        return {
            "opened": False,
            "url": url,
            "title": str(content.get("title") or ""),
            "text": "",
            "warning": "Could not open this source page.",
        }
    return {
        "opened": True,
        "url": url,
        "title": str(content.get("title") or ""),
        "text": str(content.get("text") or ""),
        "warning": "",
    }


def _content_type_allowed(content_type: str) -> bool:
    if not content_type:
        return True
    return "text/html" in content_type or "text/plain" in content_type


def _guess_encoding(content_type: str) -> str:
    marker = "charset="
    if marker in content_type:
        return content_type.split(marker, 1)[1].split(";", 1)[0].strip() or "utf-8"
    return "utf-8"
