from __future__ import annotations

from typing import Any

from app.intelligence.evidence_verifier import verify_evidence
from app.intelligence.live_source_collector import LIVE_SEARCH_NOT_CONNECTED
from app.intelligence.manipulation_detector import detect_manipulation
from app.intelligence.timeline_engine import build_timeline
from app.research.search_answer_engine import build_search_answer
from app.storage.storage_backend import save_jsonl


def build_research_response(query: str) -> dict[str, Any]:
    clean_query = query.strip()
    search_answer = build_search_answer(clean_query)
    sources = search_answer.get("sources", [])
    evidence = verify_evidence(clean_query, sources)
    timeline = build_timeline(sources)
    manipulation_risk = detect_manipulation(clean_query, sources)

    missing_data = _unique_strings(
        search_answer.get("missing_data", [])
        + evidence.get("missing_data", [])
        + timeline.get("missing_data", [])
    )

    if not search_answer.get("search_connected"):
        summary = str(search_answer.get("answer") or LIVE_SEARCH_NOT_CONNECTED)
    elif not sources:
        summary = "DuckDuckGo search returned no usable sources for this query. Builder Core did not invent evidence."
    else:
        summary = str(search_answer.get("answer") or "Builder Core prepared an evidence-based research answer from connected DuckDuckGo sources.")

    result = {
        "query": clean_query,
        "search_connected": bool(search_answer.get("search_connected")),
        "live_search_connected": bool(search_answer.get("live_search_connected")),
        "sources": sources,
        "facts": search_answer.get("facts") or evidence.get("facts", []),
        "claims": search_answer.get("claims") or evidence.get("claims", []),
        "unknowns": search_answer.get("unknowns", []),
        "timeline": {
            "before": timeline.get("before", []),
            "during": timeline.get("during", []),
            "after": timeline.get("after", []),
            "event_count": timeline.get("event_count", 0),
        },
        "manipulation_risk": manipulation_risk,
        "future_scenarios": [],
        "confidence": search_answer.get("confidence") or evidence.get("confidence", "low"),
        "missing_data": missing_data,
        "warnings": search_answer.get("warnings", []),
        "answer": search_answer.get("answer") or summary,
        "memory_saved": bool(search_answer.get("memory_saved")),
        "summary": summary,
        "recommended_next_step": str(search_answer.get("recommended_next_step") or "Verify claims against primary and reputable secondary sources."),
    }
    save_jsonl("intelligence_reports", result)
    return result


def _unique_strings(items: list[Any]) -> list[str]:
    output: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in output:
            output.append(value)
    return output
