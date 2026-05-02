from __future__ import annotations

import json
import os
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest


class ModelRouterService:
    def __init__(self) -> None:
        self.assistant_mode = (os.environ.get("ASSISTANT_MODE") or "local").strip().lower()
        self.local_model_provider = (os.environ.get("LOCAL_MODEL_PROVIDER") or "disabled").strip().lower()
        self.local_model_endpoint = (os.environ.get("LOCAL_MODEL_ENDPOINT") or "").strip()
        self.local_model_name = (os.environ.get("LOCAL_MODEL_NAME") or "").strip()
        self.openai_api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()

    def get_active_model_status(self) -> dict[str, Any]:
        warnings: list[str] = []
        provider_status = "disabled"
        local_model_connected = False
        active_brain = "local_rule_based"

        if self.local_model_provider != "disabled" and self.local_model_endpoint:
            provider_status = self._normalize_provider(self.local_model_provider)
            local_model_connected = self._check_local_model_connection()
            if not local_model_connected:
                warnings.append("Local model provider is configured, but the endpoint could not be reached right now.")
            else:
                active_brain = "local_model"

        if self.assistant_mode == "openai":
            if self.openai_api_key:
                active_brain = "openai_optional"
                warnings.append(
                    "OpenAI is configured as an optional path, but Builder Core still keeps the local rule-based brain ready as fallback."
                )
            else:
                warnings.append("ASSISTANT_MODE=openai was requested, but OPENAI_API_KEY is missing.")

        if self.assistant_mode == "local":
            active_brain = "local_rule_based" if not local_model_connected else "local_model"

        return {
            "assistant_mode": self.assistant_mode or "local",
            "active_brain": active_brain,
            "local_model_provider": provider_status,
            "local_model_connected": local_model_connected,
            "openai_configured": bool(self.openai_api_key),
            "warnings": warnings,
        }

    def generate_reply(self, prompt: str, context: dict[str, Any]) -> str:
        status = self.get_active_model_status()
        if status["active_brain"] == "local_model" and self.local_model_endpoint:
            reply = self._call_local_model(prompt, context)
            if reply:
                return reply

        return self._local_rule_based_reply(prompt, context, status)

    def generate_summary(self, text: str) -> str:
        cleaned = " ".join(text.split())
        if not cleaned:
            return "No summary content was provided."
        return f"Summary: {cleaned[:320]}"

    def generate_ideas(self, topic: str, context: dict[str, Any]) -> list[str]:
        context_hint = context.get("project_name") or "Builder Core"
        return [
            f"Create a small assistant workflow around {topic} inside {context_hint}.",
            f"Save the most important memory signals from {topic} so future prompts improve.",
            f"Turn {topic} into a safe research plan before jumping into code changes.",
        ]

    def generate_plan(self, goal: str, context: dict[str, Any]) -> list[str]:
        hints = []
        if context.get("known_issues"):
            hints.append("Review the latest known issues before changing direction.")
        hints.extend(
            [
                f"Clarify the goal: {goal[:160]}",
                "Break the work into one or two safe implementation steps.",
                "Save the result to memory and lessons when done.",
            ]
        )
        return hints

    def _check_local_model_connection(self) -> bool:
        if not self.local_model_endpoint:
            return False
        try:
            request = urlrequest.Request(self.local_model_endpoint, method="GET")
            with urlrequest.urlopen(request, timeout=3) as response:
                return 200 <= response.status < 500
        except Exception:
            return False

    def _call_local_model(self, prompt: str, context: dict[str, Any]) -> str | None:
        try:
            payload = json.dumps(
                {
                    "model": self.local_model_name or None,
                    "prompt": prompt,
                    "context": context,
                }
            ).encode("utf-8")
            request = urlrequest.Request(
                self.local_model_endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlrequest.urlopen(request, timeout=8) as response:
                body = json.loads(response.read().decode("utf-8"))
            if isinstance(body, dict):
                for key in ("reply", "response", "text"):
                    value = body.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
        except (urlerror.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return None
        return None

    def _local_rule_based_reply(self, prompt: str, context: dict[str, Any], status: dict[str, Any]) -> str:
        memory_count = len(context.get("memory", [])) if isinstance(context.get("memory"), list) else 0
        lesson_count = len(context.get("lessons", [])) if isinstance(context.get("lessons"), list) else 0
        route = context.get("workflow") or "normal_chat"

        lines = [
            "Local assistant mode is running. Add OPENAI_API_KEY later for stronger AI replies.",
            f"Builder Core is using {status['active_brain']} for this response.",
            f"Current workflow hint: {route}.",
            f"Saved context available: {memory_count} memory items and {lesson_count} lessons.",
            "",
            "Helpful response:",
            f"- Focus: {prompt[:220]}",
            "- I can research this when you ask me.",
            "- I can save this to memory.",
            "- I can create a research task.",
            "- I can use previous memory and lessons.",
            "- I do not automatically know new internet information unless research is run.",
        ]
        return "\n".join(lines)

    def _normalize_provider(self, value: str) -> str:
        lowered = value.lower()
        if "ollama" in lowered:
            return "ollama_ready"
        if "llama" in lowered:
            return "llama_cpp_ready"
        return "custom_http_ready"
