from __future__ import annotations

from typing import Any


def classify_intent(message: str, memory: dict[str, Any] | None = None) -> str:
    text = message.lower().strip()
    if not text:
        return "chat"

    if any(
        phrase in text
        for phrase in (
            "how do i run",
            "run this app",
            "launch instructions",
            "prepare run command",
            "start the app",
        )
    ):
        return "run"

    if any(
        phrase in text
        for phrase in (
            "show project files",
            "inspect current module registry",
            "what routes exist",
            "inspect",
            "project structure",
            "module registry",
        )
    ):
        return "inspect"

    if any(keyword in text for keyword in ("modify", "update", "add ", "change", "extend", "edit", "improve", "fix ")):
        return "modify"

    if any(keyword in text for keyword in ("build", "create", "make", "generate")):
        return "build"

    if "current app" in text and memory and memory.get("latest_generated_module"):
        return "modify"

    return "chat"
