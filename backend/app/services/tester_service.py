from __future__ import annotations

from pathlib import Path

from app.services import builder_service


def test_result(plan_data: dict, files_created: list[str]) -> dict:
    if not plan_data.get("build_triggered"):
        return {
            "status": "skipped",
            "summary": "No build validation was needed.",
            "checks": [
                {
                    "name": "Workflow routing",
                    "passed": True,
                    "detail": "The request did not require code generation.",
                }
            ],
        }

    project_name = plan_data["project_name"]
    module_key = plan_data["module_key"]
    route_path = plan_data["route_path"]

    checks = []

    generated_files_ok = all(Path(file_path).exists() for file_path in files_created)
    checks.append(
        {
            "name": "Generated files exist",
            "passed": generated_files_ok,
            "detail": f"Verified {len(files_created)} file references.",
        }
    )

    route_file = builder_service.route_file_path(project_name, route_path)
    checks.append(
        {
            "name": "Module route file exists",
            "passed": route_file.exists(),
            "detail": str(route_file),
        }
    )

    registry = builder_service.read_registry(project_name)
    registry_ok = any(module.get("module_key") == module_key for module in registry.get("modules", []))
    checks.append(
        {
            "name": "Module registry updated",
            "passed": registry_ok,
            "detail": f"Registry contains {module_key}.",
        }
    )

    manifest_file = builder_service.manifest_path(project_name, module_key)
    checks.append(
        {
            "name": "Manifest file updated",
            "passed": manifest_file.exists(),
            "detail": str(manifest_file),
        }
    )

    shell_dir = builder_service.app_root(project_name, create=False)
    shell_ok = (shell_dir / "layout.tsx").exists() and (shell_dir / "page.tsx").exists()
    checks.append(
        {
            "name": "Project shell preserved",
            "passed": shell_ok,
            "detail": f"Checked shell files in {shell_dir}.",
        }
    )

    passed_checks = sum(1 for check in checks if check["passed"])
    status = "success" if passed_checks == len(checks) else "failed"
    return {
        "status": status,
        "summary": f"{passed_checks}/{len(checks)} structural checks passed.",
        "checks": checks,
    }
