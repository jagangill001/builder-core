from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.learning import LearningService
    from app.storage import ProjectStorageService
except ImportError:
    from learning import LearningService
    from storage import ProjectStorageService


ASSISTANT_MODES = [
    "general",
    "coding",
    "research",
    "law",
    "market",
    "exam",
    "project",
    "creative",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatAssistantService:
    def __init__(self, storage: ProjectStorageService, learning: LearningService) -> None:
        self.storage = storage
        self.learning = learning
        self.assistant_mode = (os.environ.get("ASSISTANT_MODE") or "local").strip().lower()
        self.assistant_model = (os.environ.get("ASSISTANT_MODEL") or "").strip()
        self.openai_api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()

    def build_status(self) -> dict[str, Any]:
        return {
            "mode": self.assistant_mode or "local",
            "model": self.assistant_model or None,
            "api_configured": bool(self.openai_api_key),
            "local_fallback_active": not bool(self.openai_api_key),
            "message": (
                "Local assistant mode is running. Add OPENAI_API_KEY later for stronger AI replies."
                if not self.openai_api_key
                else "Assistant API configuration exists, but this build still keeps a local-safe fallback path."
            ),
        }

    def chat(self, message: str, mode: str, save_to_memory: bool) -> dict[str, Any]:
        normalized_mode = mode if mode in ASSISTANT_MODES else "general"
        chat_id = f"chat_{uuid4().hex[:12]}"
        created_at = utc_now_iso()

        memory = self.storage.get_project_memory(6)
        assistant_memory = self.storage.get_assistant_memory(6)
        lessons = self.learning.get_lessons(6)
        latest_summary = self.storage.get_latest_summary()
        history = self.storage.get_chat_history(8)
        memory_used = self._build_memory_used(memory, assistant_memory, lessons, latest_summary)

        reply = self._build_local_reply(
            message=message,
            mode=normalized_mode,
            memory_used=memory_used,
            latest_summary=latest_summary,
            recent_history=history,
        )
        suggestions = self._build_suggestions(normalized_mode, message)
        next_actions = self._build_next_actions(normalized_mode, message, latest_summary)

        self.storage.save_chat_message(
            {
                "chat_id": chat_id,
                "role": "user",
                "mode": normalized_mode,
                "message": message,
                "created_at": created_at,
            }
        )
        self.storage.save_chat_message(
            {
                "chat_id": chat_id,
                "role": "assistant",
                "mode": normalized_mode,
                "message": reply,
                "suggestions": suggestions,
                "next_actions": next_actions,
                "memory_used": memory_used,
                "created_at": created_at,
            }
        )

        saved_to_memory = False
        if save_to_memory:
            note = self.storage.save_assistant_memory(
                {
                    "type": "assistant_chat",
                    "mode": normalized_mode,
                    "source": "assistant_chat",
                    "user_message": message,
                    "assistant_reply": reply,
                    "note": f"Saved assistant chat for {normalized_mode} mode.",
                    "suggestions": suggestions,
                    "next_actions": next_actions,
                }
            )
            self.storage.save_project_memory(
                {
                    "type": "assistant_chat",
                    "mode": normalized_mode,
                    "note": f"Saved assistant chat about: {message[:160]}",
                    "chat_id": chat_id,
                    "assistant_memory_id": note["id"],
                }
            )
            saved_to_memory = True

        return {
            "chat_id": chat_id,
            "reply": reply,
            "suggestions": suggestions,
            "memory_used": memory_used,
            "saved_to_memory": saved_to_memory,
            "next_actions": next_actions,
            "created_at": created_at,
            "assistant_status": self.build_status(),
        }

    def get_history(self, limit: int = 30) -> list[dict[str, Any]]:
        return self.storage.get_chat_history(limit)

    def generate_ideas(self, topic: str, goal: str) -> dict[str, Any]:
        normalized_topic = topic.strip() or "Builder Core upgrade"
        normalized_goal = goal.strip() or "Create the next safe improvement."
        recent_modes = self.learning.build_learning_payload().get("recent_intelligence_modes", [])
        recent_lessons = self.learning.get_lessons(4)

        ideas = [
            self._build_idea(
                title=f"Assistant workflow for {normalized_topic}",
                why="This keeps Builder Core feeling conversational while preserving the safe manual Codex flow.",
                difficulty="Medium",
                next_step="Sketch the assistant response path, then connect saved memory to the reply builder.",
                risk="Needs careful wording so it does not imply fake automation.",
            ),
            self._build_idea(
                title=f"Research notebook for {normalized_goal}",
                why="A saved research notebook would make follow-up learning easier and improve future prompts.",
                difficulty="Medium",
                next_step="Capture research task summaries and let the user pin useful findings to memory.",
                risk="Web research still needs real integration later, so the UI must stay honest.",
            ),
            self._build_idea(
                title="Memory-driven prompt improvements",
                why="Prompt generation gets stronger when recent lessons and user preferences are visible.",
                difficulty="Low",
                next_step="Add the most useful saved memory notes into the prompt builder automatically.",
                risk="Too much saved memory could make prompts noisy if not filtered.",
            ),
            self._build_idea(
                title="Project dashboard suggestions",
                why="A dashboard that surfaces next best actions can make the app feel more assistant-led.",
                difficulty="Low",
                next_step="Promote recommended next steps, known issues, and recent tasks into one summary view.",
                risk="Needs prioritization so the page does not become cluttered.",
            ),
        ]

        if recent_modes:
            ideas.append(
                self._build_idea(
                    title=f"Improve {recent_modes[0]} mode templates",
                    why="Recent work shows this mode is already in use, so better templates would pay off quickly.",
                    difficulty="Low",
                    next_step="Review the last few prompts and tighten the mode-specific acceptance checks.",
                    risk="Mode-specific prompts can become repetitive if not refreshed.",
                )
            )

        if recent_lessons:
            lesson = recent_lessons[0]
            ideas.append(
                self._build_idea(
                    title="Turn recent lessons into reusable playbooks",
                    why="Builder Core already saves lessons, so the next step is making them easier to reuse.",
                    difficulty="Medium",
                    next_step=f"Start with the lesson from task {lesson.get('task_id', 'unknown')} and turn it into a short checklist.",
                    risk="Lesson parsing still depends on summary quality.",
                )
            )

        best_idea = ideas[0]
        return {
            "ideas": ideas[:6],
            "best_idea": best_idea["idea_title"],
            "why": best_idea["why_it_is_useful"],
            "next_steps": [idea["possible_next_step"] for idea in ideas[:3]],
            "created_at": utc_now_iso(),
        }

    def _build_local_reply(
        self,
        message: str,
        mode: str,
        memory_used: list[str],
        latest_summary: dict[str, Any] | None,
        recent_history: list[dict[str, Any]],
    ) -> str:
        intro = "Local assistant mode is running. Add OPENAI_API_KEY later for stronger AI replies."
        capability_lines = [
            "I can research this when you ask me.",
            "I can save this to memory.",
            "I can create a research task.",
            "I can use previous memory and lessons.",
            "I do not automatically know new internet information unless research is run.",
        ]

        mode_guidance = {
            "coding": "I can help shape the next coding change, break it into safer steps, and prepare a stronger Codex prompt.",
            "research": "I can help structure a research plan, point out evidence gaps, and save the result for later.",
            "law": "I can help organize general legal-information research, but I am not replacing a lawyer or jurisdiction-specific advice.",
            "market": "I can help you frame a market question, list assumptions, and separate real evidence from guesses.",
            "exam": "I can help turn a study goal into a realistic schedule, checkpoints, and review loop.",
            "project": "I can help connect your goal to Builder Core memory, recent lessons, and the next safe implementation step.",
            "creative": "I can help brainstorm ideas, variations, and practical next moves without losing project context.",
            "general": "I can help you think through the next step, connect it to project context, and save anything useful.",
        }

        memory_note = (
            f"I used saved context such as: {', '.join(memory_used[:3])}."
            if memory_used
            else "I do not have much saved memory yet, so the guidance is mostly based on your current message."
        )

        summary_note = ""
        if isinstance(latest_summary, dict):
            next_step = latest_summary.get("next_recommended_step")
            if isinstance(next_step, str) and next_step.strip():
                summary_note = f"The latest saved Codex summary suggests this next step: {next_step}"

        history_note = ""
        if recent_history:
            history_note = "I also looked at recent assistant history so I can stay consistent with the current project direction."

        reply_lines = [
            intro,
            "",
            mode_guidance.get(mode, mode_guidance["general"]),
            "",
            memory_note,
        ]

        if summary_note:
            reply_lines.extend(["", summary_note])

        if history_note:
            reply_lines.extend(["", history_note])

        reply_lines.extend(
            [
                "",
                "Helpful next move:",
                f"- Reframe this goal as a small safe task: {message[:180]}",
                f"- Decide whether the next step is chat, prompt generation, or a saved research task for {mode} mode.",
                "",
                "Assistant promises:",
                *[f"- {line}" for line in capability_lines],
            ]
        )

        return "\n".join(reply_lines)

    def _build_suggestions(self, mode: str, message: str) -> list[str]:
        shared = [
            "Save the important part of this discussion to memory if you want Builder Core to reuse it later.",
            "Generate a Codex prompt if you are ready to turn this into a repo change.",
        ]

        per_mode = {
            "coding": [
                "Turn the idea into a small implementation plan before changing multiple files.",
                "Ask Builder Core to generate a Codex prompt once the acceptance checks are clear.",
            ],
            "research": [
                "Create a research task so the topic, goal, and limitations are saved cleanly.",
                "Keep a short list of what still needs real web research or human verification.",
            ],
            "law": [
                "Separate general information from anything that needs a real lawyer.",
                "Capture jurisdiction, date sensitivity, and missing documents before acting.",
            ],
            "market": [
                "List which market claims are evidence-based and which are still assumptions.",
                "Create a research task focused on competitors, customers, or pricing so the result stays organized.",
            ],
            "exam": [
                "Break the goal into study blocks with a real schedule and review loop.",
                "Save the plan to memory so the next session can continue from the same baseline.",
            ],
            "creative": [
                "Generate ideas first, then choose one idea to turn into a concrete prompt or task.",
                "Keep the first version small so Builder Core can learn from the result quickly.",
            ],
            "project": [
                "Compare this request with the latest saved summary before changing direction.",
                "Use memory and lessons to avoid repeating the same issue twice.",
            ],
        }
        return (per_mode.get(mode, []) + shared)[:5]

    def _build_next_actions(self, mode: str, message: str, latest_summary: dict[str, Any] | None) -> list[str]:
        actions = [
            "Decide whether this should stay a chat discussion or become a research task.",
            "If you want repo changes, generate a Codex prompt after the goal feels clear enough.",
        ]

        if mode in {"research", "law", "market", "exam"}:
            actions.insert(0, "Create a research task so the topic, goal, and limitations are saved honestly.")

        if isinstance(latest_summary, dict):
            next_step = latest_summary.get("next_recommended_step")
            if isinstance(next_step, str) and next_step.strip():
                actions.insert(0, next_step)

        if "memory" in message.lower():
            actions.insert(0, "Save the most important note to memory so Builder Core can reuse it later.")

        return list(dict.fromkeys(actions))[:5]

    def _build_memory_used(
        self,
        memory: list[dict[str, Any]],
        assistant_memory: list[dict[str, Any]],
        lessons: list[dict[str, Any]],
        latest_summary: dict[str, Any] | None,
    ) -> list[str]:
        items: list[str] = []

        for entry in memory[:3]:
            note = str(entry.get("note") or entry.get("command") or "").strip()
            if note:
                items.append(note)

        for entry in assistant_memory[:2]:
            note = str(entry.get("note") or entry.get("user_message") or "").strip()
            if note:
                items.append(note)

        for lesson in lessons[:2]:
            lesson_text = str(lesson.get("lesson_learned") or "").strip()
            if lesson_text:
                items.append(lesson_text)

        if isinstance(latest_summary, dict):
            next_step = str(latest_summary.get("next_recommended_step") or "").strip()
            if next_step:
                items.append(next_step)

        return list(dict.fromkeys(item for item in items if item))[:8]

    def _build_idea(
        self,
        title: str,
        why: str,
        difficulty: str,
        next_step: str,
        risk: str,
    ) -> dict[str, str]:
        return {
            "idea_title": title,
            "why_it_is_useful": why,
            "difficulty": difficulty,
            "possible_next_step": next_step,
            "risk_or_limitation": risk,
        }
