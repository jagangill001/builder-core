from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app


class PhaseThreeFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_live_search_provider = os.environ.get("LIVE_SEARCH_PROVIDER")
        os.environ["LIVE_SEARCH_PROVIDER"] = "disabled"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        if self.previous_live_search_provider is None:
            os.environ.pop("LIVE_SEARCH_PROVIDER", None)
        else:
            os.environ["LIVE_SEARCH_PROVIDER"] = self.previous_live_search_provider

    def test_root_status(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "Builder Core Running"})

    def test_system_status_includes_phase_3_fields(self) -> None:
        response = self.client.get("/system/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["phase"], "phase_4_live_search_answer_engine_safe_memory_foundation")
        self.assertFalse(body["live_search_connected"])
        self.assertIn("phase_4_live_search_answer_engine_safe_memory_foundation", body)
        self.assertFalse(body["codex_direct_connection"])
        self.assertFalse(body["deployment_executor_connected"])
        self.assertTrue(body["security_firewall"])
        self.assertTrue(body["audit_log"])
        self.assertTrue(body["approval_workflow"])
        self.assertIn("phase_3_production_connection_cloud_storage_sandbox_foundation", body)
        self.assertIn("bridge_status", body)
        self.assertIn("frontend_url", body)
        self.assertIn("backend_url", body)

    def test_connectivity_status_returns_backend_ok(self) -> None:
        response = self.client.get("/connectivity/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["backend"], "ok")
        self.assertIn("frontend_expected_api_url", body)
        self.assertFalse(body["live_search_connected"])
        self.assertEqual(body["search_provider"], "duckduckgo")
        self.assertFalse(body["codex_direct_connection"])
        self.assertFalse(body["deployment_executor_connected"])

    def test_requirements_include_live_search_and_test_client_dependencies(self) -> None:
        requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
        content = requirements.read_text(encoding="utf-8").lower()
        self.assertIn("ddgs", content)
        self.assertIn("httpx", content)

    def test_connectivity_status_shows_duckduckgo_provider_when_enabled(self) -> None:
        with patch.dict(os.environ, {"LIVE_SEARCH_PROVIDER": "duckduckgo"}):
            with patch("app.connectors.search_connector.SearchConnector._runtime_available", return_value=True):
                response = self.client.get("/connectivity/status")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["live_search_connected"])
        self.assertEqual(body["search_provider"], "duckduckgo")

    def test_duckduckgo_connector_returns_real_source_shape_when_provider_returns_results(self) -> None:
        from app.connectors.search_connector import SearchConnector

        with patch.dict(os.environ, {"LIVE_SEARCH_PROVIDER": "duckduckgo"}):
            with patch.object(
                SearchConnector,
                "_duckduckgo",
                return_value=[
                    {
                        "title": "Builder Core",
                        "url": "https://example.com/builder-core",
                        "snippet": "Real provider result shape for test.",
                        "source_domain": "example.com",
                        "source_type": "duckduckgo_web_result",
                        "provider": "duckduckgo",
                    }
                ],
            ):
                result = SearchConnector().search("Builder Core")

        self.assertTrue(result["connected"])
        self.assertEqual(result["provider"], "duckduckgo")
        self.assertEqual(result["results"][0]["source_type"], "duckduckgo_web_result")
        self.assertEqual(result["results"][0]["url"], "https://example.com/builder-core")
        self.assertEqual(result["results"][0]["snippet"], "Real provider result shape for test.")

    def test_search_connector_handles_failure_safely(self) -> None:
        from app.connectors.search_connector import SearchConnector

        with patch.dict(os.environ, {"LIVE_SEARCH_PROVIDER": "duckduckgo"}):
            with patch.object(SearchConnector, "_duckduckgo", side_effect=RuntimeError("network refused\nTraceback hidden")):
                result = SearchConnector().search("Builder Core")

        self.assertFalse(result["connected"])
        self.assertEqual(result["provider"], "duckduckgo")
        self.assertEqual(result["results"], [])
        self.assertIn("DuckDuckGo search failed:", result["message"])
        self.assertNotIn("Traceback (most recent call last)", result["message"])

    def test_storage_status_returns_local_mode_without_cloud_env(self) -> None:
        response = self.client.get("/storage/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["storage_mode"], "local")
        self.assertFalse(body["cloud_storage_configured"])
        self.assertTrue(body["local_fallback"])
        self.assertIn("Cloud storage is not configured yet", body["message"])

    def test_command_safe_coding_creates_task_record(self) -> None:
        data = self._command("Fix my frontend backend connection")
        result = data["final_result"]
        self.assertEqual(result["type"], "coding")
        self.assertEqual(result["selected_agent"], "codex_builder_agent")
        self.assertFalse(result["blocked"])
        self.assertFalse(result["approval_required"])

        task_response = self.client.get(f"/tasks/{data['command_id']}")
        self.assertEqual(task_response.status_code, 200)
        task = task_response.json()
        self.assertEqual(task["command_id"], data["command_id"])
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["detected_intent"], "coding")
        self.assertIn("final_result", task)

    def test_command_approval_required_does_not_execute(self) -> None:
        data = self._command("Deploy my app to production")
        result = data["final_result"]
        self.assertEqual(result["type"], "cloud")
        self.assertTrue(result["approval_required"])
        self.assertFalse(result["blocked"])
        self.assertIn("did not execute", result["summary"])
        self.assertIsNotNone(result["approval_request"])

        task_response = self.client.get(f"/tasks/{data['command_id']}")
        self.assertEqual(task_response.status_code, 200)
        task = task_response.json()
        self.assertEqual(task["status"], "waiting_for_approval")
        self.assertEqual(task["approval_id"], result["approval_request"]["approval_id"])

    def test_blocked_manipulation_command(self) -> None:
        data = self._command("Create fake viral comments to change people's mood")
        result = data["final_result"]
        self.assertTrue(result["blocked"])
        self.assertEqual(result["risk_level"], "blocked")

    def test_intelligence_analysis_without_search_does_not_invent_facts(self) -> None:
        response = self.client.post("/intelligence/analyze", json={"query": "Check if this news is fake"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["live_search_connected"])
        self.assertEqual(body["sources"], [])
        self.assertEqual(body["facts"], [])
        self.assertEqual(body["confidence"], "low")
        self.assertIn("Live DuckDuckGo search results", body["missing_data"])
        self.assertIn("DuckDuckGo search is not available right now", body["summary"])

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

    def test_safe_research_command_mentions_search_not_connected(self) -> None:
        data = self._command("Analyze what happened before and after this event")
        result = data["final_result"]
        self.assertFalse(result["blocked"])
        self.assertEqual(result["type"], "research")
        self.assertEqual(result["selected_agent"], "research_agent")
        self.assertIn("DuckDuckGo search is not available right now", result["summary"])
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["timeline"]["event_count"], 0)

    def test_command_question_routes_to_search_answer(self) -> None:
        data = self._command_with_search("What is FastAPI?")
        result = data["final_result"]
        self.assertFalse(result["blocked"])
        self.assertTrue(result["search_connected"])
        self.assertEqual(result["sources"][0]["url"], "https://example.com/fastapi")
        self.assertIn("FastAPI", result["answer"])
        self.assertTrue(result["memory_saved"])

    def test_command_latest_docs_routes_to_search_answer(self) -> None:
        data = self._command_with_search("Check latest Google Cloud Run docs")
        result = data["final_result"]
        self.assertFalse(result["blocked"])
        self.assertTrue(result["search_connected"])
        self.assertIsInstance(result["sources"], list)
        self.assertNotIn("invent", result["answer"].lower())

    def test_intelligence_analysis_uses_search_when_available(self) -> None:
        with self._mock_search_results():
            response = self.client.post("/intelligence/analyze", json={"query": "Check if this news is fake"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["search_connected"])
        self.assertTrue(body["live_search_connected"])
        self.assertGreaterEqual(len(body["sources"]), 1)
        self.assertIn("answer", body)

    def test_memory_filter_redacts_secrets(self) -> None:
        from app.memory.memory_filter import redact_sensitive_text

        redacted = redact_sensitive_text("api_key=super-secret-token password=hunter2")
        self.assertIn("[REDACTED]", redacted)
        self.assertNotIn("super-secret-token", redacted)
        self.assertNotIn("hunter2", redacted)

    def test_memory_recent_works(self) -> None:
        response = self.client.get("/memory/recent")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertIn("items", body)

    def test_memory_search_works(self) -> None:
        from app.memory.memory_store import save_safe_memory

        save_safe_memory(
            {
                "memory_type": "search_answer",
                "topic": "FastAPI test memory",
                "summary": "FastAPI memory search test summary.",
                "sources": [{"title": "FastAPI", "url": "https://example.com/fastapi", "snippet": "Framework", "source_domain": "example.com"}],
                "confidence": "medium",
            }
        )
        response = self.client.post("/memory/search", json={"query": "FastAPI", "limit": 5})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertTrue(any("FastAPI" in item.get("topic", "") for item in body["items"]))

    def test_sandbox_run_creates_non_executing_record(self) -> None:
        response = self.client.post(
            "/sandbox/run",
            json={
                "command_id": "cmd_sandbox_phase_3",
                "sandbox_type": "code_test",
                "description": "Run future backend tests safely",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["sandbox_id"].startswith("sandbox_"))
        self.assertEqual(body["status"], "created")
        self.assertFalse(body["execution_allowed"])
        self.assertTrue(body["requires_human_approval"])
        self.assertIn("Real execution is not connected yet", body["message"])

    def test_audit_recent_returns_recent_entries(self) -> None:
        data = self._command("Fix my frontend backend connection")
        response = self.client.get("/audit/recent?limit=10")
        self.assertEqual(response.status_code, 200)
        entries = response.json()["items"]
        self.assertTrue(any(entry["command_id"] == data["command_id"] for entry in entries))

    def test_approval_endpoints_create_list_approve_and_reject(self) -> None:
        create_response = self.client.post(
            "/approvals",
            json={
                "command_id": "cmd_test_phase_3",
                "action": "deploy_to_production",
                "reason": "Production deploy requires approval",
                "risk_level": "high",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        approval = create_response.json()
        self.assertEqual(approval["status"], "pending")
        self.assertEqual(approval["command_id"], "cmd_test_phase_3")

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
                "command_id": "cmd_test_phase_3_reject",
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

    def _command_with_search(self, message: str) -> dict:
        with self._mock_search_results():
            return self._command(message)

    def _mock_search_results(self):
        return patch.multiple(
            "app.research.search_answer_engine",
            fetch_allowed_page=Mock(
                return_value={
                    "opened": True,
                    "url": "https://example.com/fastapi",
                    "title": "FastAPI",
                    "text": "FastAPI is described by this source as a Python web framework for building APIs.",
                    "warning": "",
                }
            ),
            SearchConnector=Mock(
                return_value=Mock(
                    search=Mock(
                        return_value={
                            "connected": True,
                            "provider": "duckduckgo",
                            "query": "FastAPI",
                            "message": "Search completed",
                            "results": [
                                {
                                    "title": "FastAPI",
                                    "url": "https://example.com/fastapi",
                                    "snippet": "FastAPI is a Python web framework for building APIs.",
                                    "summary": "FastAPI is a Python web framework for building APIs.",
                                    "source_domain": "example.com",
                                    "provider": "duckduckgo",
                                    "source_type": "duckduckgo_web_result",
                                }
                            ],
                        }
                    )
                )
            ),
        )
