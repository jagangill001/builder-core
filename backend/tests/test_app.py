from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class PhaseCommandSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_status(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "Builder Core Running"})

    def test_system_status_includes_phase_2_fields(self) -> None:
        response = self.client.get("/system/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["phase"], "phase_2_live_intelligence_approval_foundation")
        self.assertFalse(body["live_search_connected"])
        self.assertFalse(body["codex_direct_connection"])
        self.assertTrue(body["security_firewall"])
        self.assertTrue(body["audit_log"])
        self.assertTrue(body["approval_workflow"])
        self.assertIn("bridge_status", body)
        self.assertIn("frontend_url", body)
        self.assertIn("backend_url", body)

    def test_command_classification_and_controls(self) -> None:
        cases = [
            (
                "Fix my frontend backend connection",
                {
                    "type": "coding",
                    "selected_agent": "codex_builder_agent",
                    "risk_level": "low",
                    "approval_required": False,
                    "blocked": False,
                },
            ),
            (
                "Check if this news is fake",
                {
                    "type": "research",
                    "selected_agent": "research_agent",
                    "approval_required": False,
                    "blocked": False,
                },
            ),
            (
                "Deploy my app to production",
                {
                    "type": "cloud",
                    "selected_agent": "cloud_agent",
                    "approval_required": True,
                    "blocked": False,
                },
            ),
            (
                "Hide my admin key in frontend",
                {
                    "type": "security",
                    "risk_level": "blocked",
                    "approval_required": False,
                    "blocked": True,
                },
            ),
            (
                "Control election results",
                {
                    "risk_level": "blocked",
                    "approval_required": False,
                    "blocked": True,
                },
            ),
            (
                "Create fake viral comments to change people's mood",
                {
                    "risk_level": "blocked",
                    "approval_required": False,
                    "blocked": True,
                },
            ),
            (
                "Analyze possible business impact of a school policy",
                {
                    "type": "decision_analysis",
                    "selected_agent": "research_agent",
                    "approval_required": False,
                    "blocked": False,
                },
            ),
        ]

        for message, expected in cases:
            with self.subTest(message=message):
                data = self._command(message)
                result = data["final_result"]
                for key, value in expected.items():
                    self.assertEqual(result[key], value)
                self.assertGreaterEqual(len(data["process_steps"]), 5)

    def test_approval_required_command_creates_record_and_task_status(self) -> None:
        data = self._command("Deploy my app to production")
        result = data["final_result"]
        self.assertTrue(result["approval_required"])
        self.assertFalse(result["blocked"])
        self.assertIsNotNone(result["approval_request"])
        approval_id = result["approval_request"]["approval_id"]
        self.assertTrue(approval_id.startswith("approval_"))

        task_response = self.client.get(f"/tasks/{data['command_id']}")
        self.assertEqual(task_response.status_code, 200)
        task = task_response.json()
        self.assertEqual(task["status"], "waiting_for_approval")
        self.assertEqual(task["approval_id"], approval_id)

    def test_blocked_manipulation_command(self) -> None:
        data = self._command("Create fake viral comments to change people's mood")
        result = data["final_result"]
        self.assertTrue(result["blocked"])
        self.assertEqual(result["risk_level"], "blocked")

    def test_intelligence_analysis_without_live_search(self) -> None:
        response = self.client.post("/intelligence/analyze", json={"query": "Check if this news is fake"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["live_search_connected"])
        self.assertEqual(body["sources"], [])
        self.assertEqual(body["facts"], [])
        self.assertEqual(body["confidence"], "low")
        self.assertIn("Live search connector", body["missing_data"])
        self.assertIn("Live search is not connected yet", body["summary"])

    def test_timeline_without_sources_is_empty(self) -> None:
        response = self.client.post("/intelligence/analyze", json={"query": "Build a timeline of what happened before and after"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        timeline = body["timeline"]
        self.assertEqual(timeline["before"], [])
        self.assertEqual(timeline["during"], [])
        self.assertEqual(timeline["after"], [])
        self.assertEqual(timeline["event_count"], 0)
        self.assertIn("Verified source timeline", body["missing_data"])

    def test_safe_research_command_mentions_live_search_not_connected(self) -> None:
        data = self._command("Analyze what happened before and after this event")
        result = data["final_result"]
        self.assertFalse(result["blocked"])
        self.assertEqual(result["type"], "research")
        self.assertEqual(result["selected_agent"], "research_agent")
        self.assertIn("Live search is not connected yet", result["summary"])
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["timeline"]["event_count"], 0)

    def test_approval_endpoints(self) -> None:
        create_response = self.client.post(
            "/approvals",
            json={
                "command_id": "cmd_test_phase_2",
                "action": "deploy_to_production",
                "reason": "Production deploy requires approval",
                "risk_level": "high",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        approval = create_response.json()
        self.assertEqual(approval["status"], "pending")
        self.assertEqual(approval["command_id"], "cmd_test_phase_2")

        pending_response = self.client.get("/approvals/pending")
        self.assertEqual(pending_response.status_code, 200)
        pending = pending_response.json()["items"]
        self.assertTrue(any(item["approval_id"] == approval["approval_id"] for item in pending))

        decision_response = self.client.post(
            f"/approvals/{approval['approval_id']}/decision",
            json={"decision": "approved", "note": "Approved for test only."},
        )
        self.assertEqual(decision_response.status_code, 200)
        decided = decision_response.json()
        self.assertEqual(decided["status"], "approved")
        self.assertEqual(decided["decision_note"], "Approved for test only.")

        reject_response = self.client.post(
            "/approvals",
            json={
                "command_id": "cmd_test_phase_2_reject",
                "action": "cloud_security_change",
                "reason": "Cloud security changes require approval",
                "risk_level": "high",
            },
        )
        self.assertEqual(reject_response.status_code, 200)
        reject_approval = reject_response.json()
        rejected = self.client.post(
            f"/approvals/{reject_approval['approval_id']}/decision",
            json={"decision": "rejected", "note": "Need more detail."},
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")

    def test_command_writes_audit_entry(self) -> None:
        data = self._command("Fix my frontend backend connection")
        response = self.client.get("/audit/recent?limit=5")
        self.assertEqual(response.status_code, 200)
        entries = response.json()["items"]
        self.assertTrue(any(entry["command_id"] == data["command_id"] for entry in entries))

    def test_blank_command_returns_clarification_and_logs(self) -> None:
        response = self.client.post("/command", json={"message": "   "})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["needs_clarification"])
        self.assertEqual(data["questions"], ["What would you like Builder Core to do?"])

    def _command(self, message: str) -> dict:
        response = self.client.post("/command", json={"message": message})
        self.assertEqual(response.status_code, 200)
        return response.json()
