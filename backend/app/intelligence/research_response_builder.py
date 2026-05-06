from __future__ import annotations

from typing import Any

from app.intelligence.evidence_verifier import verify_evidence
from app.intelligence.live_source_collector import LIVE_SEARCH_NOT_CONNECTED, collect_live_sources
from app.intelligence.manipulation_detector import detect_manipulation
from app.intelligence.timeline_engine import build_timeline
from app.storage.storage_backend import save_jsonl


def build_research_response(query: str) -> dict[str, Any]:
    clean_query = query.strip()
    collection = collect_live_sources(clean_query)
    sources = collection.get("sources", [])
    evidence = verify_evidence(clean_query, sources)
    timeline = build_timeline(sources)
    manipulation_risk = detect_manipulation(clean_query, sources)

    missing_data = _unique_strings(
        ["Live search connector", "Verified sources"]
        + evidence.get("missing_data", [])
        + timeline.get("missing_data", [])
    )

    if not collection.get("connected"):
        summary = (
            f"{LIVE_SEARCH_NOT_CONNECTED} Builder Core can prepare the analysis structure "
            "but cannot verify real-world claims without sources."
        )
    elif not sources:
        summary = "Live internet/search is connected, but no sources were returned for this query. Builder Core did not invent evidence."
    else:
        summary = "Builder Core prepared an evidence-based research structure from connected internet/search sources."

    result = {
        "query": clean_query,
        "live_search_connected": bool(collection.get("connected")),
        "sources": sources,
        "facts": evidence.get("facts", []),
        "claims": evidence.get("claims", []),
        "timeline": {
            "before": timeline.get("before", []),
            "during": timeline.get("during", []),
            "after": timeline.get("after", []),
            "event_count": timeline.get("event_count", 0),
        },
        "manipulation_risk": manipulation_risk,
        "future_scenarios": [],
        "confidence": evidence.get("confidence", "low"),
        "missing_data": missing_data,
        "summary": summary,
        "recommended_next_step": "Connect a real live-search provider, then verify claims against primary and reputable secondary sources.",
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