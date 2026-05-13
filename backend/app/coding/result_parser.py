from __future__ import annotations

from typing import Any


def parse_codex_result(raw_result: dict[str, Any] | None) -> dict[str, Any]:
    if not raw_result:
        return {
            "ok": False,
            "message": "No Codex execution result is available.",
            "patch_summary": None,
            "tests": [],
        }
    return {
        "ok": bool(raw_result.get("ok")),
        "message": raw_result.get("message", "Codex result received."),
        "patch_summary": raw_result.get("patch_summary"),
        "tests": raw_result.get("tests", []),
    }
