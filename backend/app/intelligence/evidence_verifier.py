from __future__ import annotations

from typing import Any

CLAIM_TYPES = {"verified_fact", "reported_claim", "weak_claim", "opinion", "unknown"}


def classify_claim(text: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    clean_text = " ".join((text or "").split())
    if not clean_text:
        return {"text": "", "classification": "unknown", "confidence": "low", "reason": "No claim text provided."}

    if not sources:
        return {
            "text": clean_text,
            "classification": "unknown",
            "confidence": "low",
            "reason": "No verified sources were provided.",
        }

    return {
        "text": clean_text,
        "classification": "reported_claim",
        "confidence": "medium",
        "reason": "The claim is tied to provided source material but has not been independently verified by Builder Core.",
    }


def verify_evidence(query: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    safe_sources = sources or []
    if not safe_sources:
        return {
            "facts": [],
            "claims": [],
            "confidence": "low",
            "missing_data": ["Verified sources"],
        }

    claims = [classify_claim(str(source.get("title") or source.get("snippet") or source.get("summary") or query), safe_sources) for source in safe_sources]
    return {
        "facts": [],
        "claims": claims,
        "confidence": "medium",
        "missing_data": ["Independent corroboration"],
    }
