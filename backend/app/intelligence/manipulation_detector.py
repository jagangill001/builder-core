from __future__ import annotations

from typing import Any

SIGNAL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("outrage", "possible signal: call-to-outrage language"),
    ("you won't believe", "possible signal: emotional trigger language"),
    ("share before", "possible signal: urgency to amplify before verification"),
    ("viral", "possible signal: amplification framing"),
    ("fake comments", "possible signal: fake engagement request"),
    ("bot", "possible signal: bot amplification framing"),
    ("screenshot", "possible signal: screenshot-only claim needs verification"),
    ("they don't want you to know", "possible signal: conspiratorial framing"),
    ("make people angry", "possible signal: emotional manipulation framing"),
    ("change people's mood", "possible signal: public mood manipulation framing"),
    ("old video", "possible signal: old content may be reused as new"),
)


def detect_manipulation(text: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    normalized = " ".join((text or "").lower().split())
    signals = [description for pattern, description in SIGNAL_PATTERNS if pattern in normalized]

    if not sources:
        if signals:
            return {
                "level": "medium",
                "signals": signals,
                "explanation": "The user-provided text contains possible manipulation signals, but live search is not connected yet, so Builder Core cannot verify real-world context.",
            }
        return {
            "level": "unknown",
            "signals": [],
            "explanation": "Live search is not connected yet, so real manipulation analysis cannot be completed.",
        }

    return {
        "level": "unknown",
        "signals": signals,
        "explanation": "Builder Core can flag possible signals from provided text, but verified source comparison is still required.",
    }
