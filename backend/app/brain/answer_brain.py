from __future__ import annotations

from typing import Any

from app.brain.context_manager import normalize_history
from app.brain.followup_questioner import followup_questions
from app.brain.question_classifier import classify_question
from app.connectors.news_connector import answer_news_query
from app.connectors.weather_connector import answer_weather_query
from app.memory.memory_search import recall_relevant_memories
from app.models.command_models import CommandIntent
from app.research.search_answer_engine import build_search_answer


def build_brain_answer(message: str, intent: CommandIntent, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    clean_message = " ".join((message or "").split())
    normalized_history = normalize_history(history or [])
    clarification_questions = followup_questions(clean_message, normalized_history)
    memory_recall = recall_relevant_memories(clean_message, limit=3)
    recalled_items = list(memory_recall.get("items") or [])

    if clarification_questions:
        answer = clarification_questions[0]
        return _base_result(
            query=clean_message,
            answer=answer,
            answer_mode="clarify",
            confidence="medium",
            facts=_memory_facts(recalled_items),
            warnings=[],
            memory_recalled=bool(recalled_items),
            recommended_next_step="Reply with the missing detail so Builder Core can answer or act safely.",
            extra={"needs_clarification": True, "questions": clarification_questions},
        )

    classification = classify_question(clean_message, intent)
    mode = str(classification.get("mode") or "general_chat")

    if mode == "weather":
        return _with_memory_context(answer_weather_query(clean_message), recalled_items, "weather")
    if mode == "news":
        return _with_memory_context(answer_news_query(clean_message), recalled_items, "news")
    if mode == "live_search":
        result = build_search_answer(clean_message)
        result["answer_mode"] = "live_search"
        result["used_live_search"] = True
        return _with_memory_context(result, recalled_items, "live_search")
    if mode == "direct_answer":
        return _direct_answer_result(clean_message, intent, recalled_items)

    return _general_chat_result(clean_message, normalized_history, recalled_items)


def _direct_answer_result(query: str, intent: CommandIntent, recalled_items: list[dict[str, Any]]) -> dict[str, Any]:
    answer = _stable_answer(query, intent)
    facts = _direct_facts(query, answer) + _memory_facts(recalled_items)
    return _base_result(
        query=query,
        answer=answer,
        answer_mode="direct_answer",
        confidence="medium",
        facts=facts,
        warnings=[],
        memory_recalled=bool(recalled_items),
        recommended_next_step="Ask for examples, a step-by-step walkthrough, or a live source check if you need current details.",
    )


def _general_chat_result(
    query: str,
    history: list[dict[str, str]],
    recalled_items: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized = query.lower()
    if normalized in {"hi", "hello", "hey"}:
        answer = "Hi. Ask me a question or tell me what you want Builder Core to work through."
    elif history:
        answer = (
            "I can help with that. From the recent conversation, tell me the exact piece you want changed, "
            "explained, researched, or checked, and I will keep the details tucked behind the chat controls."
        )
    else:
        answer = (
            "I can help, but I need a little more detail. Ask a direct question, request a source check, "
            "or describe the task you want Builder Core to handle."
        )
    return _base_result(
        query=query,
        answer=answer,
        answer_mode="general_chat",
        confidence="medium" if history else "low",
        facts=_memory_facts(recalled_items),
        warnings=[],
        memory_recalled=bool(recalled_items),
        recommended_next_step="Send the specific question or task.",
    )


def _stable_answer(query: str, intent: CommandIntent) -> str:
    normalized = _normalize(query)
    subject = _subject_from_question(normalized)

    if "fastapi" in normalized:
        return (
            "FastAPI is a Python web framework for building APIs. It is popular because it uses Python type hints "
            "to validate request data, generate OpenAPI documentation, and keep endpoint code concise."
        )
    if normalized in {"what is python", "what is python?"} or subject == "python":
        return (
            "Python is a high-level programming language known for readable syntax and a large ecosystem. "
            "It is used for web apps, automation, data work, AI tooling, scripting, and backend services."
        )
    if "cors" in normalized:
        return (
            "CORS, or Cross-Origin Resource Sharing, is a browser security system that controls whether a page "
            "from one origin can read responses from another origin. Servers opt in by returning headers such as "
            "Access-Control-Allow-Origin."
        )
    if "cloud run" in normalized:
        return (
            "Google Cloud Run is a managed serverless platform for running containerized apps. You deploy a container, "
            "Cloud Run handles HTTPS, scaling, request routing, and scale-to-zero behavior, while you configure CPU, memory, "
            "environment variables, and permissions."
        )
    if "sikh history" in normalized or ("sikh" in normalized and "history" in normalized):
        return (
            "Sikh history begins in the Punjab region with Guru Nanak in the late 15th century and continues through the "
            "ten Sikh Gurus, the formation of the Khalsa by Guru Gobind Singh in 1699, the Sikh misls and Sikh Empire, "
            "colonial-era changes, Partition, and modern Sikh communities around the world."
        )
    if normalized.startswith("how does") and subject:
        return (
            f"{subject.capitalize()} works by combining a few moving parts toward one goal. "
            "The useful way to understand it is to identify the inputs, the rules or system that transforms them, "
            "and the output or behavior you see. Ask me for the specific system and I can make this concrete."
        )
    if normalized.startswith("explain") and subject:
        return (
            f"{subject.capitalize()} means the core idea, why it matters, and how it is used in practice. "
            "Give me the context you care about, such as coding, business, history, or cloud infrastructure, and I can tailor it."
        )
    if intent == "coding":
        return (
            "For a coding question, I can explain the concept, outline the fix, or help inspect the repo. "
            "Share the specific error, file, or behavior and I will give a concrete answer."
        )
    if intent == "cloud":
        return (
            "For a cloud question, I can explain the service, configuration, deployment path, and risks. "
            "Real production changes still require approval before any action happens."
        )
    return (
        "Here is the direct answer: this looks like a stable question, so Builder Core can answer from built-in knowledge. "
        "Ask for a source check if you want current or verified citations."
    )


def _direct_facts(query: str, answer: str) -> list[dict[str, Any]]:
    return [
        {
            "text": answer,
            "confidence": "medium",
            "type": "built_in_knowledge",
            "reason": f"Direct stable answer for: {query}",
        }
    ]


def _memory_facts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for item in items:
        summary = str(item.get("summary") or "").strip()
        if not summary:
            continue
        facts.append(
            {
                "text": summary,
                "confidence": str(item.get("confidence") or "low"),
                "type": "memory_recall",
                "reason": "Relevant safe memory was recalled before answering.",
            }
        )
    return facts


def _with_memory_context(result: dict[str, Any], recalled_items: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    facts = list(result.get("facts") or [])
    facts.extend(_memory_facts(recalled_items))
    warnings = [str(item) for item in result.get("warnings", []) if item]
    if recalled_items:
        warnings.append("Relevant safe memory was recalled before answering.")
    return {
        **result,
        "facts": facts,
        "warnings": list(dict.fromkeys(warnings)),
        "answer_mode": result.get("answer_mode") or mode,
        "memory_recalled": bool(recalled_items),
        "recalled_memory_count": len(recalled_items),
    }


def _base_result(
    *,
    query: str,
    answer: str,
    answer_mode: str,
    confidence: str,
    facts: list[dict[str, Any]],
    warnings: list[str],
    memory_recalled: bool,
    recommended_next_step: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "query": query,
        "search_connected": False,
        "live_search_connected": False,
        "sources": [],
        "facts": facts,
        "claims": [],
        "unknowns": [],
        "answer": answer,
        "summary": answer,
        "confidence": confidence,
        "missing_data": [],
        "warnings": warnings,
        "memory_saved": False,
        "memory_recalled": memory_recalled,
        "answer_mode": answer_mode,
        "used_live_search": False,
        "recommended_next_step": recommended_next_step,
    }
    if extra:
        result.update(extra)
    return result


def _subject_from_question(normalized: str) -> str:
    for prefix in ("what is ", "what are ", "how does ", "how do ", "explain ", "define ", "tell me about "):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip(" ?.")
    return ""


def _normalize(message: str) -> str:
    return " ".join((message or "").lower().replace("-", " ").replace("_", " ").split())
