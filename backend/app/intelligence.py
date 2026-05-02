from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


INTELLIGENCE_MODES: dict[str, dict[str, Any]] = {
    "safe_research": {
        "title": "Safe Research",
        "overview": "Create a grounded research brief with clear questions, evidence needs, and a safe scope before any code or product change.",
        "keywords": ["research", "study", "investigate", "compare", "analyze", "analyse"],
        "research_steps": [
            "Clarify the exact user goal and the decision this research should support.",
            "Break the topic into factual questions that can be answered separately.",
            "List what evidence must be verified before any recommendation is trusted.",
            "Separate facts, assumptions, and unknowns in the final brief.",
        ],
        "evidence_checklist": [
            "Primary source or official source identified",
            "Date or timeframe recorded",
            "Assumptions separated from verified facts",
            "Open questions listed clearly",
        ],
        "next_questions": [
            "What decision will this research change?",
            "Which facts matter most right now?",
            "What would make this research unsafe or incomplete?",
        ],
        "codex_focus": [
            "Add or improve Builder Core research planning surfaces without claiming automatic fact verification.",
            "Keep all outputs beginner-friendly and explicit about uncertainty.",
        ],
        "output_outline": [
            "Goal summary",
            "Research questions",
            "Evidence checklist",
            "Safe next step",
        ],
    },
    "law": {
        "title": "Law and Policy Planning",
        "overview": "Provide a structured legal-information workflow for general education, not a substitute for a lawyer or jurisdiction-specific advice.",
        "keywords": ["law", "legal", "policy", "contract", "compliance", "terms", "privacy"],
        "research_steps": [
            "Identify the exact legal or policy question in plain language.",
            "Separate general educational guidance from anything that would require licensed counsel.",
            "List jurisdiction, dates, parties, and documents that must be verified manually.",
            "Prepare a lawyer-ready question list instead of pretending to provide final legal advice.",
        ],
        "evidence_checklist": [
            "Jurisdiction captured",
            "Official policy, statute, or contract source identified",
            "Date sensitivity noted",
            "Manual legal review step included",
        ],
        "next_questions": [
            "Which jurisdiction controls this issue?",
            "Is the user asking for education, drafting help, or a legal conclusion?",
            "What part must be escalated to a real lawyer?",
        ],
        "codex_focus": [
            "Frame the Intelligence Center as general informational support only.",
            "Add strong disclaimers and clear manual review requirements.",
        ],
        "output_outline": [
            "Question and jurisdiction",
            "General background only",
            "Documents or facts to verify",
            "Escalate to lawyer when needed",
        ],
    },
    "market_analysis": {
        "title": "Market Analysis",
        "overview": "Turn broad business questions into structured competitor, customer, and positioning analysis without inventing market data.",
        "keywords": ["market", "competitor", "pricing", "business", "customer", "industry", "product strategy"],
        "research_steps": [
            "Define the market question and target customer clearly.",
            "List competitor, customer, pricing, and channel questions separately.",
            "Record which claims require real market evidence before action.",
            "Summarize opportunities, risks, and data gaps honestly.",
        ],
        "evidence_checklist": [
            "Target customer segment defined",
            "Competitor list verified",
            "Pricing assumptions labeled clearly",
            "Missing market data called out",
        ],
        "next_questions": [
            "Which customer segment matters most first?",
            "What competitor evidence do we already have?",
            "Which claim would be dangerous to guess?",
        ],
        "codex_focus": [
            "Design Builder Core market-planning flows around evidence, assumptions, and next questions.",
            "Never present guessed market numbers as real facts.",
        ],
        "output_outline": [
            "Market question",
            "Customer and competitor map",
            "Evidence gaps",
            "Safe next move",
        ],
    },
    "exam_planning": {
        "title": "Exam Planning",
        "overview": "Convert a large exam goal into a realistic revision plan, study schedule, and progress review workflow.",
        "keywords": ["exam", "study", "revision", "syllabus", "prep", "test prep", "course"],
        "research_steps": [
            "List exam topics, timing, and the learner's current baseline.",
            "Split the plan into manageable study blocks and review loops.",
            "Identify weak areas, deadlines, and practice requirements.",
            "Turn the result into a realistic study schedule, not a motivational slogan.",
        ],
        "evidence_checklist": [
            "Exam date known",
            "Topics or syllabus captured",
            "Time available per week estimated",
            "Practice method defined",
        ],
        "next_questions": [
            "What is the exam date?",
            "Which topics feel weakest right now?",
            "How much study time is actually available each week?",
        ],
        "codex_focus": [
            "Support learning structure, study cadence, and review loops.",
            "Keep the plan practical for phone-first use.",
        ],
        "output_outline": [
            "Exam goal",
            "Study schedule",
            "Practice routine",
            "Review checkpoints",
        ],
    },
    "forecasting": {
        "title": "Forecasting",
        "overview": "Build scenario-based forecasts with assumptions, ranges, and explicit uncertainty instead of pretending to predict the future with certainty.",
        "keywords": ["forecast", "predict", "projection", "scenario", "trend", "outlook"],
        "research_steps": [
            "Define the forecast question and the decision it informs.",
            "List the baseline assumptions and what could change them.",
            "Create best-case, base-case, and risk-case scenarios.",
            "Highlight uncertainty and the trigger signals to watch next.",
        ],
        "evidence_checklist": [
            "Forecast horizon defined",
            "Baseline assumptions listed",
            "Scenarios separated clearly",
            "Uncertainty explained honestly",
        ],
        "next_questions": [
            "What period are we forecasting?",
            "Which assumptions are strongest and weakest?",
            "What signals would prove this forecast wrong?",
        ],
        "codex_focus": [
            "Keep all forecasts scenario-based and assumption-driven.",
            "Never imply guaranteed outcomes.",
        ],
        "output_outline": [
            "Forecast question",
            "Assumptions",
            "Three scenarios",
            "Monitoring triggers",
        ],
    },
    "language_learning": {
        "title": "Language Learning",
        "overview": "Create a structured learning workflow for vocabulary, grammar, speaking, and review without pretending the learner is already fluent.",
        "keywords": ["language", "vocabulary", "grammar", "speaking", "listening", "fluency", "spanish", "french"],
        "research_steps": [
            "Define the learner's target language and immediate goal.",
            "Break the work into comprehension, speaking, vocabulary, and review loops.",
            "Keep the plan small enough to repeat consistently.",
            "Track progress with practice tasks, not vague confidence claims.",
        ],
        "evidence_checklist": [
            "Target language named",
            "Goal and timeframe defined",
            "Practice loop identified",
            "Review method identified",
        ],
        "next_questions": [
            "What language is the learner targeting?",
            "Is the goal travel, work, exams, or conversation?",
            "What kind of practice is easiest to sustain daily?",
        ],
        "codex_focus": [
            "Prioritize repeatable practice and memory support.",
            "Keep study prompts short and beginner-friendly.",
        ],
        "output_outline": [
            "Goal",
            "Daily practice loop",
            "Weekly review",
            "Progress check",
        ],
    },
    "video_transcript_learning": {
        "title": "Video Transcript Learning",
        "overview": "Turn provided transcript material into notes, study plans, and learning prompts without claiming a transcript exists when it has not been supplied.",
        "keywords": ["transcript", "video", "lecture", "podcast", "youtube", "recording"],
        "research_steps": [
            "Confirm whether the user already has a transcript or only rough notes.",
            "Extract topics, timestamps, and action items from provided material.",
            "Convert the material into notes, flashcards, or study prompts.",
            "Mark any missing transcript sections as unknown instead of inventing them.",
        ],
        "evidence_checklist": [
            "Transcript or notes source provided",
            "Missing sections flagged",
            "Key topics extracted",
            "Learning output chosen",
        ],
        "next_questions": [
            "Do we have the actual transcript or only notes?",
            "Should the output become notes, flashcards, or study questions?",
            "What parts of the recording matter most?",
        ],
        "codex_focus": [
            "Only work from user-provided transcript content or honest placeholders.",
            "Keep copyrighted transcript boundaries explicit.",
        ],
        "output_outline": [
            "Source status",
            "Key ideas",
            "Learning notes",
            "Open gaps",
        ],
    },
    "self_improvement_memory": {
        "title": "Self-Improvement Memory",
        "overview": "Capture repeatable lessons, habits, and next steps so Builder Core becomes a personal progress memory system over time.",
        "keywords": ["habit", "improve", "reflection", "journal", "memory", "goal", "coach"],
        "research_steps": [
            "Clarify the habit, behavior, or skill the user wants to improve.",
            "Record the smallest repeatable next action.",
            "Save patterns, blockers, and wins into memory.",
            "Turn the lesson into a realistic next-step recommendation.",
        ],
        "evidence_checklist": [
            "Improvement goal named",
            "Blockers recorded",
            "Small next action defined",
            "Memory note saved",
        ],
        "next_questions": [
            "What should Builder Core remember for next time?",
            "What small win can be repeated tomorrow?",
            "What blocker keeps coming back?",
        ],
        "codex_focus": [
            "Strengthen memory capture, review loops, and lightweight coaching prompts.",
            "Keep the tone supportive and specific.",
        ],
        "output_outline": [
            "Goal",
            "Pattern seen",
            "Next action",
            "Memory note",
        ],
    },
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_supported_modes() -> list[dict[str, str]]:
    return [
        {
            "id": mode_id,
            "title": config["title"],
            "overview": config["overview"],
        }
        for mode_id, config in INTELLIGENCE_MODES.items()
    ]


def detect_intelligence_mode(command: str) -> str:
    lowered = command.lower()

    for mode_id, config in INTELLIGENCE_MODES.items():
        for keyword in config.get("keywords", []):
            if keyword in lowered:
                return mode_id

    return "safe_research"


def build_safety_firewall(mode_id: str, command: str) -> dict[str, Any]:
    lowered = command.lower()
    config = INTELLIGENCE_MODES[mode_id]
    blocked_keywords = ["suicide", "self-harm", "kill myself", "harm myself"]
    blocked = any(keyword in lowered for keyword in blocked_keywords)

    risk_level = "moderate"
    manual_limits = [
        "Do not present guesses as verified facts.",
        "Do not claim Builder Core completed research it did not actually perform.",
        "Escalate to a qualified human professional when the topic requires it.",
    ]
    do_list = [
        "Organize the task into clear questions and safe next steps.",
        "Label uncertainty and manual verification needs.",
        "Keep the output usable for a beginner.",
    ]
    do_not_list = [
        "Do not invent citations, market data, or legal conclusions.",
        "Do not imply that Builder Core replaced a licensed expert.",
        "Do not hide missing context or missing evidence.",
    ]

    message = f"{config['title']} mode is active. Builder Core will structure the work safely and honestly."

    if mode_id == "law":
        risk_level = "high"
        manual_limits.append("Legal outputs are general educational guidance only and must be reviewed by a qualified lawyer.")
    elif mode_id in {"market_analysis", "forecasting"}:
        risk_level = "high"
        manual_limits.append("Separate assumptions from verified evidence before making business or financial decisions.")
    elif mode_id == "video_transcript_learning":
        manual_limits.append("Only use transcript content the user already has rights to provide.")

    if blocked:
        risk_level = "blocked"
        message = "High-risk wellbeing language was detected. Builder Core should not handle this alone."
        do_not_list.insert(0, "Do not continue as a normal planning task.")
        manual_limits.insert(0, "Escalate to immediate human help or emergency support when safety is at risk.")

    return {
        "risk_level": risk_level,
        "blocked": blocked,
        "message": message,
        "do": do_list,
        "do_not": do_not_list,
        "manual_limits": manual_limits,
    }


def build_intelligence_brief(
    command: str,
    project_memory: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    latest_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mode_id = detect_intelligence_mode(command)
    config = INTELLIGENCE_MODES[mode_id]
    firewall = build_safety_firewall(mode_id, command)
    memory_signals = _extract_memory_signals(project_memory)
    lesson_signals = _extract_lesson_signals(lessons)
    recent_summary_note = _extract_latest_summary_note(latest_summary)

    recommended_memory_note = (
        f"User is currently using Builder Core for {config['title'].lower()} work. Keep future prompts structured, safe, and explicit about manual verification."
    )

    return {
        "id": f"brief_{uuid4().hex[:12]}",
        "command": command,
        "mode": mode_id,
        "title": config["title"],
        "overview": config["overview"],
        "status_message": firewall["message"],
        "safety_firewall": firewall,
        "research_steps": config["research_steps"],
        "evidence_checklist": config["evidence_checklist"],
        "next_questions": config["next_questions"],
        "codex_focus": config["codex_focus"],
        "output_outline": config["output_outline"],
        "memory_signals": memory_signals,
        "lesson_signals": lesson_signals,
        "recent_summary_note": recent_summary_note,
        "recommended_memory_note": recommended_memory_note,
        "created_at": utc_now_iso(),
    }


def _extract_memory_signals(project_memory: list[dict[str, Any]]) -> list[str]:
    signals: list[str] = []
    for entry in project_memory[:5]:
        note = str(entry.get("note") or entry.get("command") or "").strip()
        if note:
            signals.append(note)

    return signals or ["No strong memory signals were saved yet."]


def _extract_lesson_signals(lessons: list[dict[str, Any]]) -> list[str]:
    signals: list[str] = []
    for lesson in lessons[:5]:
        text = str(lesson.get("lesson_learned") or "").strip()
        if text:
            signals.append(text)

    return signals or ["No lessons were saved yet."]


def _extract_latest_summary_note(latest_summary: dict[str, Any] | None) -> str:
    if not isinstance(latest_summary, dict):
        return "No latest summary was saved yet."

    message = str(latest_summary.get("message") or "").strip()
    return message or "A latest summary exists, but it does not include a clear message."
