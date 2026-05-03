from __future__ import annotations

from typing import Any

try:
    from app.knowledge_manager import KnowledgeManagerService
except ImportError:
    from knowledge_manager import KnowledgeManagerService


SEED_PACKS: list[dict[str, Any]] = [
    {
        "knowledge_id": "seed_builder_core_os_architecture",
        "title": "Builder Core OS Architecture",
        "category": "ai_os",
        "tags": ["builder-core", "ai-os", "architecture", "firestore", "agents"],
        "content": (
            "Builder Core OS is a foundation-stage internal AI operating system. It uses a unified /command endpoint, "
            "Firestore or local JSON storage, private search, agent roles, a safety firewall, a human approval system, "
            "a defensive security monitor, an account agent for authorized sources, connector registry, model router, "
            "and platform adapter. OpenAI and outside search APIs are optional; local and rule-based paths must continue working."
        ),
    },
    {
        "knowledge_id": "seed_safe_defensive_system",
        "title": "Safe Defensive System",
        "category": "security",
        "tags": ["defensive", "security", "rate-limit", "cloud-run", "secret-manager"],
        "content": (
            "Builder Core security features are defensive only. The monitor logs suspicious request paths, redacts sensitive headers, "
            "uses in-memory rate limiting, and creates incident reports. It follows a no-retaliation policy. IP/location metadata is "
            "approximate and does not identify a person. Future hardening should add admin authentication, Cloud Armor, API Gateway, "
            "Secret Manager, least-privilege IAM, backups, alerting, and audit logs."
        ),
    },
    {
        "knowledge_id": "seed_ai_agent_system",
        "title": "AI Agent System",
        "category": "ai_os",
        "tags": ["agents", "tasks", "memory", "approval"],
        "content": (
            "Builder Core agents are internal task controllers, not AGI or consciousness. Agent roles plan work, choose internal tools, "
            "record tasks and steps, save memory, and show limitations. High-risk roles such as finance, legal, medical, security, "
            "vehicles, aircraft, and defense remain decision-support only and require human approval before real-world action."
        ),
    },
    {
        "knowledge_id": "seed_business_market_analysis",
        "title": "Business and Market Analysis",
        "category": "business",
        "tags": ["business", "market", "mvp", "revenue"],
        "content": (
            "Business analysis in Builder Core should identify target users, pain points, competitors, market risks, revenue models, "
            "cost areas, MVP scope, validation steps, and a practical roadmap. It should separate saved evidence from assumptions and "
            "avoid pretending to have live market data unless the user provided current sources."
        ),
    },
    {
        "knowledge_id": "seed_app_building_workflow",
        "title": "App Building Workflow",
        "category": "code",
        "tags": ["app-building", "backend", "frontend", "testing", "deployment"],
        "content": (
            "The Builder Core app workflow plans backend routes, frontend screens, storage collections, safety checks, tests, and deployment. "
            "Implementation prompts should be Codex-ready, mention exact files, preserve existing endpoints, run backend import checks, "
            "run frontend builds, and verify Cloud Run deployment after push."
        ),
    },
    {
        "knowledge_id": "seed_teaching_study_system",
        "title": "Teaching and Study System",
        "category": "teaching",
        "tags": ["teaching", "study", "practice", "quiz"],
        "content": (
            "Teaching answers should use simple explanations, lesson plans, practice tasks, examples, review questions, and a revision path. "
            "Builder Core should use saved knowledge when available and clearly say when more notes, PDFs, or URLs are needed."
        ),
    },
    {
        "knowledge_id": "seed_trucking_business_starter",
        "title": "Trucking Business Knowledge Starter",
        "category": "trucking",
        "tags": ["trucking", "dispatch", "owner-operators", "profit-per-mile"],
        "content": (
            "Trucking dispatch and small-fleet tools often need load board tracking, owner-operator workflows, small fleet management, "
            "profit per mile, fuel cost estimates, compliance reminders, invoices, factoring notes, route planning, and clear cost visibility."
        ),
    },
    {
        "knowledge_id": "seed_high_risk_safety_limits",
        "title": "Legal, Medical, and Finance Safety Limits",
        "category": "general",
        "tags": ["safety", "legal", "medical", "finance", "approval"],
        "content": (
            "Legal, medical, finance, trading, vehicle, aircraft, defense, and similar high-risk work is information-only or decision-support only. "
            "Builder Core must not create guaranteed outcomes, live trades, medical treatment decisions, legal filings, or physical control actions "
            "without qualified professional review, certification where required, and explicit human approval."
        ),
    },
]


class SeedKnowledgeService:
    def __init__(self, knowledge_manager: KnowledgeManagerService) -> None:
        self.knowledge_manager = knowledge_manager

    def seed_default_packs(self) -> dict[str, Any]:
        seeded_count = 0
        updated_count = 0
        skipped_count = 0
        for pack in SEED_PACKS:
            existing = self.knowledge_manager.get_knowledge_entry(pack["knowledge_id"])
            payload = {
                **pack,
                "source_type": "seed_pack",
                "confidence": "medium",
            }
            result = self.knowledge_manager.add_knowledge_entry(payload)
            if not result.get("ok"):
                skipped_count += 1
            elif existing:
                updated_count += 1
            else:
                seeded_count += 1
            self.knowledge_manager.storage.save_record(
                "knowledge_seed_packs",
                {
                    "id": pack["knowledge_id"],
                    "knowledge_id": pack["knowledge_id"],
                    "title": pack["title"],
                    "status": "updated" if existing else "seeded",
                },
            )
        return {
            "ok": True,
            "seeded_count": seeded_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "storage_used": "firestore" if self.knowledge_manager.storage.using_firestore else "local",
            "message": "Knowledge seed complete.",
        }
