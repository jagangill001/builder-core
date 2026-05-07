from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.connectors.page_fetcher import fetch_allowed_page
from app.connectors.search_connector import DUCKDUCKGO_UNAVAILABLE, SearchConnector
from app.memory.memory_store import save_safe_memory

MAX_SOURCES = 5
MAX_PAGES_TO_OPEN = 3


def build_search_answer(query: str, *, save_memory: bool = True) -> dict[str, Any]:
    clean_query = " ".join((query or "").split())
    connector_result = SearchConnector().search(clean_query, limit=MAX_SOURCES)
    warnings: list[str] = []

    if not connector_result.get("connected"):
        message = str(connector_result.get("message") or DUCKDUCKGO_UNAVAILABLE)
        warnings.append(message)
        return {
            "query": clean_query,
            "search_connected": False,
            "live_search_connected": False,
            "sources": [],
            "facts": [],
            "claims": [],
            "unknowns": [
                {
                    "text": "No live DuckDuckGo results were available for this query.",
                    "reason": message,
                }
            ],
            "answer": DUCKDUCKGO_UNAVAILABLE,
            "summary": DUCKDUCKGO_UNAVAILABLE,
            "confidence": "low",
            "missing_data": ["Live DuckDuckGo search results", "Verified sources"],
            "warnings": list(dict.fromkeys(warnings)),
            "memory_saved": False,
            "recommended_next_step": "Try again later or verify the question with trusted sources outside Builder Core.",
        }

    raw_sources = list(connector_result.get("results") or [])[:MAX_SOURCES]
    sources = [_source_record(source) for source in raw_sources if isinstance(source, dict)]
    page_results = _open_allowed_pages(sources)
    warnings.extend(page_results["warnings"])

    for source in sources:
        opened = page_results["by_url"].get(source["url"])
        if opened:
            source["opened"] = bool(opened.get("opened"))
            source["page_excerpt"] = _truncate(str(opened.get("text") or ""), 500)
            page_title = str(opened.get("title") or "").strip()
            if page_title and not source["title"]:
                source["title"] = page_title
        else:
            source["opened"] = False
            source["page_excerpt"] = ""

    facts = _build_facts(sources)
    claims = _build_claims(sources)
    unknowns = _build_unknowns(sources)
    missing_data = _build_missing_data(sources)
    answer = _build_answer(clean_query, sources)
    confidence = _confidence(sources)
    memory_saved = False

    if save_memory and sources:
        memory_result = save_safe_memory(
            {
                "memory_type": "search_answer",
                "topic": clean_query,
                "summary": answer,
                "sources": sources,
                "confidence": confidence,
                "verify_before_use": True,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        memory_saved = bool(memory_result.get("saved"))
        warnings.extend(str(item) for item in memory_result.get("warnings", []) if item)

    return {
        "query": clean_query,
        "search_connected": True,
        "live_search_connected": True,
        "sources": sources,
        "facts": facts,
        "claims": claims,
        "unknowns": unknowns,
        "answer": answer,
        "summary": answer,
        "confidence": confidence,
        "missing_data": missing_data,
        "warnings": list(dict.fromkeys(warnings)),
        "memory_saved": memory_saved,
        "recommended_next_step": "Review the listed sources and verify important decisions against primary sources.",
    }


def _open_allowed_pages(sources: list[dict[str, Any]]) -> dict[str, Any]:
    by_url: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for source in sources[:MAX_PAGES_TO_OPEN]:
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        opened = fetch_allowed_page(url)
        by_url[url] = opened
        warning = str(opened.get("warning") or "").strip()
        if warning:
            warnings.append(warning)
    return {"by_url": by_url, "warnings": list(dict.fromkeys(warnings))}


def _source_record(source: dict[str, Any]) -> dict[str, Any]:
    snippet = _truncate(str(source.get("snippet") or source.get("summary") or ""), 1000)
    return {
        "title": _truncate(str(source.get("title") or ""), 240),
        "url": str(source.get("url") or "").strip(),
        "snippet": snippet,
        "summary": snippet,
        "source_domain": str(source.get("source_domain") or "").strip(),
        "provider": str(source.get("provider") or "duckduckgo"),
        "source_type": str(source.get("source_type") or "duckduckgo_web_result"),
        "citation_candidate": bool(source.get("url") and (source.get("title") or snippet)),
    }


def _build_facts(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for source in sources:
        title = source.get("title")
        domain = source.get("source_domain") or "unknown source"
        if title:
            facts.append(
                {
                    "text": f"DuckDuckGo returned a source from {domain} titled: {title}",
                    "source_url": source.get("url"),
                    "confidence": "high",
                    "type": "source_metadata",
                }
            )
    return facts


def _build_claims(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for source in sources:
        evidence = str(source.get("page_excerpt") or source.get("snippet") or "").strip()
        if not evidence:
            continue
        claims.append(
            {
                "text": _truncate(evidence, 500),
                "classification": "reported_claim",
                "confidence": "medium" if source.get("opened") else "low",
                "source_url": source.get("url"),
                "reason": "This comes from source text or DuckDuckGo result snippets and still needs human verification before critical use.",
            }
        )
    return claims


def _build_unknowns(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unknowns: list[dict[str, Any]] = [
        {
            "text": "Builder Core has not independently verified these sources beyond collecting search results and allowed page excerpts.",
            "reason": "Independent corroboration is outside the current deterministic answer engine.",
        }
    ]
    unopened = [source for source in sources[:MAX_PAGES_TO_OPEN] if not source.get("opened")]
    if unopened:
        unknowns.append(
            {
                "text": "Some source pages could not be opened by the safe page reader.",
                "reason": "The answer may rely on DuckDuckGo snippets and source metadata for those sources.",
            }
        )
    return unknowns


def _build_missing_data(sources: list[dict[str, Any]]) -> list[str]:
    missing = ["Independent corroboration"]
    if not any(source.get("opened") for source in sources):
        missing.append("Full source page text")
    if not sources:
        missing.extend(["Live DuckDuckGo search results", "Verified sources"])
    return list(dict.fromkeys(missing))


def _build_answer(query: str, sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "DuckDuckGo search returned no usable sources for this query. Builder Core did not invent an answer."

    evidence_lines = []
    for index, source in enumerate(sources[:3], start=1):
        title = str(source.get("title") or "Untitled source").strip()
        domain = str(source.get("source_domain") or "unknown source").strip()
        evidence = str(source.get("page_excerpt") or source.get("snippet") or "").strip()
        if evidence:
            evidence_lines.append(f"{index}. {title} ({domain}): {_truncate(evidence, 420)}")
        else:
            evidence_lines.append(f"{index}. {title} ({domain})")

    basis = " ".join(evidence_lines)
    if any(source.get("opened") for source in sources):
        qualifier = "Based on DuckDuckGo results and allowed source page excerpts"
    else:
        qualifier = "Based on DuckDuckGo result snippets and source metadata"

    return f"{qualifier} for '{query}', the strongest supported answer is: {basis}"


def _confidence(sources: list[dict[str, Any]]) -> str:
    opened_count = len([source for source in sources if source.get("opened")])
    if opened_count >= 2 and len(sources) >= 3:
        return "high"
    if sources:
        return "medium"
    return "low"


def _truncate(text: str, max_chars: int) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."
