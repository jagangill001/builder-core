# Builder Core Project Progress

## Current State

Builder Core has moved from a simple phase 1 command classifier toward a phase 5-25 command operating system foundation.

The backend is now the source of truth for tasks, progress, stages, logs, results, sources, warnings, errors, and summaries. The frontend dashboard displays backend state and no longer simulates command progress.

## Completed In Phases 5-20

- Better answer brain and command router.
- Source ranking model.
- Search, weather, and news connector placeholders with honest not-configured responses.
- Real task model, task store, task engine, and task routes.
- Frontend command center upgrade.
- GitHub connector foundation.
- Codex task package foundation.
- Project memory summary.
- Session/task summaries.
- Safety firewall.
- Admin-token auth foundation.
- SQLite persistence layer with in-memory fallback.
- Queue/worker foundation.
- GitHub automation endpoints.
- Coding agent package helpers.
- Connector registry and connector status endpoints.
- Deployment status/checklist/rollback placeholder.
- Workflow graph endpoint.
- Lessons learned and recommendations.
- Tests for task flow, status, connectors, memory, safety, and admin rejection.

## Completed In Phases 21-25

- Fixed local SQLite by moving active default storage away from OneDrive journal locking while keeping the documented `backend/data` default and clear status warnings.
- Added durable audit logging foundation and admin-only `GET /audit/logs`.
- Added connector provider status fields and provider-missing execution responses.
- Added GitHub dry-run mode, safe task branch naming, and direct-main write protection.
- Added deployment health checks with reachability, status code, response time, safe errors, and environment checklist.
- Added backend self-test and release checklist endpoints.
- Updated frontend with DB status, connector execution state, deployment health, self-test, and release checklist panels.

## Known Placeholders

- Search provider execution.
- Weather provider execution.
- News provider execution.
- Real Codex execution.
- External queue and worker.
- Cloud Run rollback execution.
- GitHub Actions status enrichment beyond connector API support.
- Deep repeated-error clustering.
- Future Gmail/Drive/Calendar integrations.

## SQLite Notes

The workspace is inside OneDrive, and SQLite rollback journals can report disk I/O errors there. Builder Core now detects OneDrive and stores the active default SQLite database in a non-synced temp-local Builder Core directory unless `DATABASE_URL`, `BUILDER_CORE_SQLITE_DIR`, or `BUILDER_CORE_FORCE_WORKSPACE_DB=true` is set.

The in-memory fallback remains in place if the DB fails.

To reset local DB state, stop the backend and delete the path shown by `/system/status` at `database.database_path`.

## Verification

Backend tests:

```powershell
cd backend
python -m pytest -q
python -m compileall app tests
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

## Next Build Steps

1. Add a real search provider adapter and source extraction.
2. Add weather and news provider adapters.
3. Add durable PostgreSQL/Cloud SQL setup for production.
4. Move task execution into a true background worker.
5. Connect GitHub Actions workflow status into deployment status.
6. Add real Cloud Run deployment and rollback controls with audit logs.
7. Wire a real Codex execution path only when it can report truthful results.
