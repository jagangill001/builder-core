from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ROADMAP_ITEMS: list[dict[str, Any]] = [
    {
        "id": "stabilize-core",
        "title": "Stabilize core build and endpoint smoke tests",
        "status": "in_progress",
        "priority": "high",
        "notes": "Keep backend imports, frontend build, and core endpoint checks passing before expanding features.",
    },
    {
        "id": "verify-live-storage",
        "title": "Verify live Firestore and protected admin routes",
        "status": "next",
        "priority": "high",
        "notes": "Confirm Cloud Run has the expected environment variables and service-account permissions.",
    },
    {
        "id": "harden-knowledge-workflows",
        "title": "Harden knowledge and one-page URL learning workflows",
        "status": "planned",
        "priority": "medium",
        "notes": "Add richer validation, clearer UI states, and live regression checks after the foundation is stable.",
    },
    {
        "id": "operator-dashboard",
        "title": "Improve the operator dashboard",
        "status": "planned",
        "priority": "medium",
        "notes": "Keep advanced panels collapsed and make manual setup/testing states easier to scan.",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RoadmapService:
    def get_roadmap(self) -> dict[str, Any]:
        return {
            "ok": True,
            "items": ROADMAP_ITEMS,
            "count": len(ROADMAP_ITEMS),
            "last_updated": utc_now_iso(),
            "future_expansion": "Later passes can move roadmap storage into Firestore and add owner/due-date fields.",
        }

    def get_next(self) -> dict[str, Any]:
        for status in ("in_progress", "next", "planned"):
            for item in ROADMAP_ITEMS:
                if item.get("status") == status:
                    return {"ok": True, "item": item, "last_updated": utc_now_iso()}
        return {"ok": True, "item": {}, "last_updated": utc_now_iso()}
