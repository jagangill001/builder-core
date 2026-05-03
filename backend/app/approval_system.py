from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from app.action_permissions import check_action_permission
    from app.storage import ProjectStorageService
except ImportError:
    from action_permissions import check_action_permission
    from storage import ProjectStorageService


APPROVAL_REQUIRED_ACTIONS = [
    "send_email",
    "make_trade",
    "financial_decision",
    "legal_filing",
    "medical_recommendation",
    "customer_refund",
    "publish_content",
    "create_github_pr",
    "deploy_app",
    "external_account_action",
    "hardware_control",
    "vehicle_control",
    "aircraft_control",
    "defense_system_action",
    "modify_cloud_resources",
    "delete_data",
    "rotate_secrets",
    "block_ip",
    "change_security_policy",
]

BLOCKED_BY_DEFAULT_ACTIONS = [
    "autonomous_weapon_action",
    "bypass_security",
    "malware",
    "hacking",
    "deleting_user_data_without_confirmation",
    "pretending_to_be_human_deceptively",
    "medical_diagnosis_or_treatment_without_professional_review",
    "live_trading_without_human_confirmation",
    "aircraft_or_vehicle_control_without_certification_and_human_operator",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalSystemService:
    def __init__(self, storage: ProjectStorageService) -> None:
        self.storage = storage

    def request_approval(
        self,
        action_type: str,
        description: str,
        requested_by_agent: str = "system",
        risk_level: str | None = None,
    ) -> dict[str, Any]:
        permission = check_action_permission(action_type, description)
        approval_id = f"approval_{uuid4().hex[:12]}"
        normalized_risk = risk_level or permission.get("risk_level") or "medium"
        status = "pending"
        warnings: list[str] = []

        if permission.get("blocked"):
            status = "rejected"
            warnings.append("This action is blocked by default and cannot be approved from this queue.")
        elif not permission.get("requires_confirmation") and permission.get("allowed"):
            warnings.append("This action is normally allowed internally, but an approval record was created for audit visibility.")

        approval = {
            "id": approval_id,
            "approval_id": approval_id,
            "action_type": action_type,
            "description": description,
            "risk_level": normalized_risk,
            "status": status,
            "requested_by_agent": requested_by_agent or "system",
            "permission": permission,
            "warnings": warnings,
            "created_at": utc_now_iso(),
            "resolved_at": utc_now_iso() if status == "rejected" else None,
        }
        return self.storage.save_record("approvals", approval)

    def approve(self, approval_id: str) -> dict[str, Any] | None:
        existing = self.get_approval(approval_id)
        if existing is None:
            return None
        if existing.get("permission", {}).get("blocked"):
            return self.storage.update_record(
                "approvals",
                approval_id,
                {
                    "status": "rejected",
                    "resolved_at": utc_now_iso(),
                    "resolution_note": "Blocked-by-default actions cannot be approved here.",
                },
            )
        return self.storage.update_record(
            "approvals",
            approval_id,
            {
                "status": "approved",
                "resolved_at": utc_now_iso(),
            },
        )

    def reject(self, approval_id: str, reason: str = "") -> dict[str, Any] | None:
        existing = self.get_approval(approval_id)
        if existing is None:
            return None
        return self.storage.update_record(
            "approvals",
            approval_id,
            {
                "status": "rejected",
                "resolved_at": utc_now_iso(),
                "resolution_note": reason or "Rejected by human operator.",
            },
        )

    def list_approvals(self, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        items = self.storage.list_records("approvals", max(1, min(limit, 200)))
        if status:
            return [item for item in items if item.get("status") == status]
        return items

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        return self.storage.get_record("approvals", approval_id)

    def count_pending(self) -> int:
        return len(self.list_approvals(limit=200, status="pending"))
