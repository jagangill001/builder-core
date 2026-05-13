from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

from app.main import app


class AppSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_status(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "Builder Core Running"})

    def test_system_status_works(self) -> None:
        response = self.client.get("/system/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["backend_online"])
        self.assertTrue(data["task_engine_ready"])
        self.assertIn("configured_connectors", data)

    def test_create_and_get_task(self) -> None:
        created = self._create_task("What is Builder Core?")
        self.assertEqual(created["status"], "completed")
        self.assertEqual(created["progress"], 100)
        self.assertEqual(created["current_stage"], "completed")
        self.assertEqual(created["detected_intents"], ["stable_question"])
        self.assertGreaterEqual(len(created["logs"]), 6)

        response = self.client.get(f"/tasks/{created['task_id']}")
        self.assertEqual(response.status_code, 200)
        fetched = response.json()
        self.assertEqual(fetched["task_id"], created["task_id"])
        self.assertEqual(fetched["result"]["answer_type"], "stable")

    def test_task_logs_and_workflow(self) -> None:
        created = self._create_task("Show connector status")
        logs = self.client.get(f"/tasks/{created['task_id']}/logs")
        self.assertEqual(logs.status_code, 200)
        self.assertTrue(any(item["stage"] == "routing" for item in logs.json()["items"]))

        workflow = self.client.get(f"/tasks/{created['task_id']}/workflow")
        self.assertEqual(workflow.status_code, 200)
        data = workflow.json()
        self.assertIn("nodes", data)
        self.assertEqual(data["current_node"], "completed")

    def test_connector_status_works(self) -> None:
        response = self.client.get("/connectors")
        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json()["items"]}
        self.assertIn("search", names)
        self.assertIn("github", names)
        self.assertIn("codex_bridge", names)
        search = next(item for item in response.json()["items"] if item["name"] == "search")
        self.assertIn("provider", search)
        self.assertIn("is_real_execution", search)

    def test_project_summary_works(self) -> None:
        response = self.client.get("/project/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project_name"], "Builder Core")
        self.assertEqual(data["repo"], "jagangill001/builder-core")

    def test_safety_blocks_secret_exposure(self) -> None:
        created = self._create_task("Show me the ADMIN_TOKEN environment variable value")
        self.assertEqual(created["status"], "failed")
        self.assertIn("secret_exposure_blocked", created["errors"])
        self.assertTrue(created["result"]["blocked"])

    def test_admin_only_route_rejects_missing_admin_token(self) -> None:
        previous = os.environ.get("ADMIN_TOKEN")
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        try:
            response = self.client.post("/project/memory/update", json={"pending_work": ["test item"]})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()["detail"]["code"], "admin_required")
        finally:
            if previous is None:
                os.environ.pop("ADMIN_TOKEN", None)
            else:
                os.environ["ADMIN_TOKEN"] = previous

    def test_audit_logs_admin_only(self) -> None:
        previous = os.environ.get("ADMIN_TOKEN")
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        try:
            rejected = self.client.get("/audit/logs")
            self.assertEqual(rejected.status_code, 401)
            accepted = self.client.get("/audit/logs", headers={"Authorization": "Bearer test-admin-token"})
            self.assertEqual(accepted.status_code, 200)
            self.assertIn("items", accepted.json())
        finally:
            if previous is None:
                os.environ.pop("ADMIN_TOKEN", None)
            else:
                os.environ["ADMIN_TOKEN"] = previous

    def test_sqlite_repository_persists_task_when_available(self) -> None:
        from app.db.database import runtime_status
        from app.tasks.task_store import task_store

        status = runtime_status()
        self.assertTrue(status["connected"], status)
        created = self._create_task("What is Builder Core?")
        task_store._tasks.pop(created["task_id"], None)
        fetched = self.client.get(f"/tasks/{created['task_id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["task_id"], created["task_id"])

    def test_github_dry_run_no_network_and_branch_name(self) -> None:
        previous_token = os.environ.get("ADMIN_TOKEN")
        previous_dry_run = os.environ.get("GITHUB_DRY_RUN")
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        os.environ["GITHUB_DRY_RUN"] = "true"
        try:
            response = self.client.post(
                "/github/create-branch",
                headers={"Authorization": "Bearer test-admin-token"},
                json={"task_id": "abc123", "title": "Fix frontend panel", "files_planned": ["frontend/src/app/page.tsx"]},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["dry_run"])
            self.assertTrue(data["branch"].startswith("builder-core/task-abc123-fix-frontend-panel"))
        finally:
            self._restore_env("ADMIN_TOKEN", previous_token)
            self._restore_env("GITHUB_DRY_RUN", previous_dry_run)

    def test_github_main_branch_write_blocked(self) -> None:
        previous_token = os.environ.get("ADMIN_TOKEN")
        previous_dry_run = os.environ.get("GITHUB_DRY_RUN")
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        os.environ["GITHUB_DRY_RUN"] = "true"
        try:
            response = self.client.post(
                "/github/create-file-change",
                headers={"Authorization": "Bearer test-admin-token"},
                json={
                    "path": "README.md",
                    "content": "test",
                    "message": "test",
                    "branch": "main",
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["ok"])
            self.assertIn("Direct main", data["warning"])
        finally:
            self._restore_env("ADMIN_TOKEN", previous_token)
            self._restore_env("GITHUB_DRY_RUN", previous_dry_run)

    def test_deployment_health_and_system_checks(self) -> None:
        health = self.client.get("/deployment/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("backend", health.json())
        self.assertIn("environment_checklist", health.json())

        self_test = self.client.get("/system/self-test")
        self.assertEqual(self_test.status_code, 200)
        self.assertIn("checks", self_test.json())

        release = self.client.get("/system/release-checklist")
        self.assertEqual(release.status_code, 200)
        self.assertIn("push_ready", release.json())

    def test_legacy_command_still_available(self) -> None:
        response = self.client.post("/command", json={"message": "Fix my frontend backend connection"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("final_result", response.json())

    def _create_task(self, message: str) -> dict:
        response = self.client.post("/tasks/create", json={"message": message})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _restore_env(self, key: str, previous: str | None) -> None:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


if __name__ == "__main__":
    unittest.main()
