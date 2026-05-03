from __future__ import annotations

from typing import Any


def get_cloud_run_hardening_checklist() -> list[str]:
    return [
        "Use least-privilege IAM for the Cloud Run service account.",
        "Keep secrets in Secret Manager, not environment files or frontend code.",
        "Add authentication before exposing admin-only endpoints.",
        "Use Cloud Armor later for WAF rules and production rate limiting.",
        "Monitor Cloud Run logs for repeated 404, 500, and suspicious paths.",
        "Disable unused endpoints if the public surface grows too large.",
    ]


def get_firestore_hardening_checklist() -> list[str]:
    return [
        "Restrict Firestore access through the backend service account.",
        "Do not expose Firestore credentials to the frontend.",
        "Use IAM least privilege and review service account permissions.",
        "Back up Firestore data on a schedule before relying on it for production memory.",
        "Keep audit logs for high-risk write actions.",
    ]


def get_secret_safety_checklist() -> list[str]:
    return [
        "Do not commit API keys, tokens, service account JSON, or passwords.",
        "Rotate exposed secrets immediately.",
        "Use Secret Manager for production keys.",
        "Redact Authorization, Cookie, token, key, and secret headers from logs.",
        "Never ask users to paste account passwords into Builder Core.",
    ]


def get_frontend_security_checklist() -> list[str]:
    return [
        "Keep secrets out of frontend environment variables.",
        "Use the backend as the only write path for memory and storage.",
        "Avoid rendering untrusted HTML from documents or URL ingest.",
        "Add admin-only dashboard protection before exposing security events publicly.",
        "Keep the frontend simple and lightweight for low-memory devices.",
    ]


def get_incident_response_steps() -> list[str]:
    return [
        "Review recent high-severity events and affected paths.",
        "Confirm whether events are expected health checks, scanners, or real abuse.",
        "Rotate exposed secrets if any sensitive route or key may have leaked.",
        "Patch misconfigurations and deploy with human approval.",
        "Add Cloud Armor/API Gateway rules for repeated abusive patterns.",
        "Document the incident and next prevention step.",
    ]


def get_future_security_upgrade_path() -> list[str]:
    return [
        "Add admin authentication and role-based access controls.",
        "Move rate limits to Firestore, Redis/Memorystore, or Cloud Armor.",
        "Add alerting for repeated high-severity events.",
        "Add signed audit logs for approvals and security decisions.",
        "Add Cloud Armor managed rules and API Gateway quotas.",
        "Add safe security testing in isolated lab environments only.",
    ]


def get_security_hardening_payload() -> dict[str, Any]:
    return {
        "cloud_run": get_cloud_run_hardening_checklist(),
        "firestore": get_firestore_hardening_checklist(),
        "secret_safety": get_secret_safety_checklist(),
        "frontend_security": get_frontend_security_checklist(),
        "incident_response": get_incident_response_steps(),
        "future_security_upgrade_path": get_future_security_upgrade_path(),
        "policy": [
            "No hack-back.",
            "No malware.",
            "No credential theft.",
            "No exact attacker identity claims from IP metadata.",
            "External cybersecurity actions require human approval.",
        ],
    }
