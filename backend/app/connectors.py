from __future__ import annotations

from typing import Any


CONNECTORS: list[dict[str, Any]] = [
    {
        "connector_id": "firestore_memory",
        "name": "Firestore Memory",
        "status": "available",
        "read_supported": True,
        "write_supported": True,
        "requires_oauth": False,
        "requires_user_confirmation": False,
        "safety_notes": ["Uses backend storage abstraction only.", "Do not store secrets as memory."],
        "limitations": ["Available only when Firestore is configured; otherwise local fallback is used."],
    },
    {
        "connector_id": "private_search",
        "name": "Private Search",
        "status": "available",
        "read_supported": True,
        "write_supported": True,
        "requires_oauth": False,
        "requires_user_confirmation": False,
        "safety_notes": ["Searches saved Builder Core knowledge only."],
        "limitations": ["Not web-wide search and not a replacement for Google/Bing."],
    },
    {
        "connector_id": "document_ingest",
        "name": "Document Ingest",
        "status": "available",
        "read_supported": True,
        "write_supported": True,
        "requires_oauth": False,
        "requires_user_confirmation": False,
        "safety_notes": ["Only ingests user-provided text."],
        "limitations": ["No private scraping or hidden account access."],
    },
    {
        "connector_id": "safe_url_ingest",
        "name": "Safe URL Ingest",
        "status": "available",
        "read_supported": True,
        "write_supported": True,
        "requires_oauth": False,
        "requires_user_confirmation": False,
        "safety_notes": ["Only user-provided public http/https URLs.", "Blocks localhost, private IPs, onion links, logins, and paywall bypass."],
        "limitations": ["Single-page fetch; no uncontrolled crawling."],
    },
    {
        "connector_id": "google_drive_ready",
        "name": "Google Drive Ready",
        "status": "ready_not_connected",
        "read_supported": False,
        "write_supported": False,
        "requires_oauth": True,
        "requires_user_confirmation": True,
        "safety_notes": ["Future OAuth connector only; do not paste passwords."],
        "limitations": ["No current Drive connection is implemented."],
    },
    {
        "connector_id": "gmail_ready",
        "name": "Gmail Ready",
        "status": "ready_not_connected",
        "read_supported": False,
        "write_supported": False,
        "requires_oauth": True,
        "requires_user_confirmation": True,
        "safety_notes": ["Future OAuth connector only.", "Sending email would require explicit human confirmation."],
        "limitations": ["No current Gmail connection is implemented."],
    },
    {
        "connector_id": "youtube_transcript_ready",
        "name": "YouTube Transcript Ready",
        "status": "ready_not_connected",
        "read_supported": False,
        "write_supported": False,
        "requires_oauth": False,
        "requires_user_confirmation": True,
        "safety_notes": ["Future public transcript connector only if terms and access rules allow it."],
        "limitations": ["No transcript fetcher is implemented."],
    },
    {
        "connector_id": "browser_session_ready",
        "name": "Browser Session Ready",
        "status": "ready_not_connected",
        "read_supported": False,
        "write_supported": False,
        "requires_oauth": False,
        "requires_user_confirmation": True,
        "safety_notes": ["Future user-authorized browser session only.", "No CAPTCHA, login, paywall bypass, or hidden surveillance."],
        "limitations": ["No browser-session connector is implemented."],
    },
]


class ConnectorRegistryService:
    def list_connectors(self) -> list[dict[str, Any]]:
        return [dict(item) for item in CONNECTORS]

    def get_connector(self, connector_id: str) -> dict[str, Any] | None:
        for connector in CONNECTORS:
            if connector["connector_id"] == connector_id:
                return dict(connector)
        return None

    def get_status(self) -> dict[str, Any]:
        connectors = self.list_connectors()
        return {
            "total_connectors": len(connectors),
            "available": len([item for item in connectors if item["status"] == "available"]),
            "future_ready": len([item for item in connectors if item["status"] == "ready_not_connected"]),
            "blocked": len([item for item in connectors if item["status"] == "blocked"]),
            "items": connectors,
        }


def list_available_connectors() -> list[dict[str, Any]]:
    return ConnectorRegistryService().list_connectors()
