from __future__ import annotations

import os
import platform as platform_module
import sys
from typing import Any


def _env_truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def _storage_mode() -> str:
    requested = (os.environ.get("STORAGE_MODE") or "local").strip().lower()
    firestore_ready = _env_truthy("FIRESTORE_ENABLED") and bool((os.environ.get("GCP_PROJECT_ID") or "").strip())
    if requested == "firestore" and firestore_ready:
        return "firestore"
    if requested in {"firestore", "local"}:
        return "local" if requested != "firestore" or not firestore_ready else requested
    return "unknown"


def _detect_platform() -> str:
    if os.environ.get("K_SERVICE") or os.environ.get("K_REVISION") or os.environ.get("CLOUD_RUN_JOB"):
        return "cloud_run"
    system = platform_module.system().lower()
    if "linux" in system:
        return "linux"
    if "windows" in system:
        return "windows"
    return "unknown"


def get_runtime_mode() -> str:
    platform_name = _detect_platform()
    low_memory = (os.environ.get("BUILDER_CORE_LOW_MEMORY") or "").strip().lower() in {"1", "true", "yes"}
    offline = (os.environ.get("OFFLINE_MODE") or "").strip().lower() in {"1", "true", "yes"}
    if low_memory:
        return "low_memory"
    if offline:
        return "offline_ready"
    if platform_name == "cloud_run":
        return "cloud"
    if platform_name in {"linux", "windows"}:
        return "local"
    return "unknown"


def get_resource_profile() -> dict[str, str]:
    memory_mode = "low" if get_runtime_mode() == "low_memory" else "normal"
    if _detect_platform() == "unknown":
        memory_mode = "unknown"
    return {
        "memory_mode": memory_mode,
        "storage_mode": _storage_mode(),
    }


def get_supported_capabilities() -> dict[str, list[str]]:
    runtime_mode = get_runtime_mode()
    storage_mode = _storage_mode()
    supported = [
        "local_rule_based_assistant",
        "private_search",
        "document_ingest",
        "safe_single_url_ingest",
        "crawler_planning_only",
        "agent_roles",
        "agent_tasks",
        "approval_queue",
        "defensive_security_monitor",
        "in_memory_rate_limit",
        "human_approval_for_high_risk_actions",
    ]
    disabled = [
        "autonomous_crawling",
        "internet_wide_search",
        "hack_back",
        "malware",
        "credential_theft",
        "captcha_bypass",
        "dark_web_access",
        "autonomous_trading",
        "medical_treatment_control",
        "vehicle_or_aircraft_control",
        "weapons_control",
    ]
    if storage_mode == "firestore":
        supported.append("firestore_storage")
    else:
        supported.append("local_json_storage")
    if runtime_mode == "offline_ready":
        disabled.extend(["live_url_fetch", "external_model_calls"])
    return {
        "supported_capabilities": supported,
        "disabled_capabilities": list(dict.fromkeys(disabled)),
    }


def get_degraded_mode_plan() -> list[str]:
    return [
        "Use local JSON storage when Firestore is not configured or unavailable.",
        "Use local rule-based responses when optional model providers are disabled.",
        "Keep crawler work as explicit plans until a user-approved safe executor exists.",
        "Keep high-risk domains as decision-support only with human approval gates.",
        "Prefer smaller memory/search operations in low-memory mode.",
    ]


def get_future_portability_notes() -> list[str]:
    return [
        "Cloud Run plus Firestore is the current cloud target.",
        "Local server mode can run the same FastAPI core with local JSON storage.",
        "A future SQLite adapter can improve local/offline durability.",
        "Android-ready and low-memory modes should use the same storage/model/platform adapters.",
        "Hardware and simulator adapters must remain separated from core planning logic.",
        "Certified real-world integrations need legal, safety, and human-operator review before control actions.",
    ]


def get_platform_status() -> dict[str, Any]:
    capabilities = get_supported_capabilities()
    warnings = [
        "Runtime detection is best-effort and depends on environment variables plus the host OS.",
        "Future portability notes describe architecture direction, not finished support for every target.",
    ]
    if _storage_mode() != "firestore":
        warnings.append("Firestore is not currently detected as the active configured storage mode; local fallback should remain available.")

    return {
        "platform": _detect_platform(),
        "runtime_mode": get_runtime_mode(),
        "python_version": sys.version.split()[0],
        "resource_profile": get_resource_profile(),
        "supported_capabilities": capabilities["supported_capabilities"],
        "disabled_capabilities": capabilities["disabled_capabilities"],
        "portability_notes": get_future_portability_notes(),
        "degraded_mode_plan": get_degraded_mode_plan(),
        "warnings": warnings,
    }
