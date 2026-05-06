from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class Phase1CommandSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_status(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "Builder Core Running"})

    def test_system_status_includes_phase_1_fields(self) -> None:
        response = self.client.get("/system/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["phase"], "phase_1_core_command_system")
        self.assertFalse(body["live_search_connected"])
        self.assertFalse(body["codex_direct_connection"])
        self.assertTrue(body["security_firewall"])
        self.assertTrue(body["audit_log"])
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
                self.assertEqual(len(data["process_steps"]), 5)

    def test_research_mentions_live_search_is_not_connected(self) -> None:
        data = self._command("Check if this news is fake")
        summary = data["final_result"]["summary"].lower()
        self.assertIn("live internet search is not connected", summary)

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
