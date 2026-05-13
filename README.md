# Builder Core

Builder Core is an AI command center for the `jagangill001/builder-core` project. The goal is a real backend-owned operating system for commands, not a frontend demo that invents progress.

## What Phases 5-25 Added

Phases 5-20 added the first command OS foundation:

- Backend task engine with task ids, stages, logs, progress, results, warnings, errors, summaries, and source records.
- Brain/router that classifies stable, current, weather, news, coding, GitHub, Codex, deployment, project, memory, admin, and unknown commands.
- Honest connector system for search, weather, news, GitHub, Codex bridge, deployment, database, memory, and future Google connectors.
- Safety firewall for secret-exposure requests, unsafe automation, destructive commands, and confirmation-needed actions.
- Admin-token foundation for protected write actions.
- SQLite-backed persistence layer with in-memory fallback when the DB is unavailable.
- Worker queue abstraction that processes immediately today and can move to a real queue later.
- GitHub connector foundation for repo reads and branch/issue/file/PR writes when env vars are configured.
- Codex task package builder. It does not claim real Codex execution.
- Project memory, lessons learned, and recommendations endpoints.
- Deployment awareness with health checks and rollback placeholder.
- Next.js dashboard that only displays backend-owned task state.

Phases 21-25 add the next reliability layer:

- Durable SQLite task/memory/audit storage when DB is available.
- Admin-protected `GET /audit/logs`.
- Connector provider fields and `provider_missing` responses for search, weather, and news.
- GitHub dry-run mode, task branch naming, and direct-main write protection.
- Deployment health endpoint with URL reachability, status code, response time, and environment checklist.
- Self-test and release-checklist endpoints.
- Frontend panels for DB status, connector execution state, deployment health, self-test, and release readiness.

## Backend Architecture

Backend entrypoint: `backend/app/main.py`

Key areas:

- `backend/app/tasks`: task models, store, engine, and routes.
- `backend/app/brain`: command router, answer brain, source ranker, recommendations.
- `backend/app/connectors`: connector implementations and registry.
- `backend/app/auth`: admin-token auth foundation.
- `backend/app/safety`: safety firewall.
- `backend/app/db`: DB tables, status, persistence, and in-memory fallback.
- `backend/app/audit`: durable audit log helpers and admin route.
- `backend/app/memory`: project memory, session summaries, lessons.
- `backend/app/coding`: repo map, context selector, Codex instruction/package builder.
- `backend/app/deployment`: deployment status/checklist/rollback placeholder.
- `backend/app/system`: self-test and release checklist.
- `backend/app/workflows`: workflow graph returned for a task.
- `backend/app/workers`: queue and worker placeholders.

## Frontend Architecture

Frontend entrypoint: `frontend/src/app/page.tsx`

The frontend:

- Posts commands to `POST /tasks/create`.
- Polls `GET /tasks/{task_id}` while tasks are active.
- Displays backend-owned task status, progress, current stage, logs, result, sources, warnings, and errors.
- Shows project summary, connector cards, GitHub status, deployment status, lessons learned, recommendations, and admin mode.
- Sends admin token as an `Authorization: Bearer ...` header only when entered in browser state.

## Real Features

- Task records, stage logs, progress, summaries, warnings, and errors are created by the backend.
- Stable built-in answers work without live search.
- Safety blocks secret-exposure commands before routing or connector execution.
- Connector status is real and based on environment configuration.
- Admin-only routes reject missing or invalid admin tokens.
- Project summary, lessons, recommendations, workflow graph, system status, and connector status endpoints work.
- GitHub API calls are real when `GITHUB_TOKEN`, `GITHUB_REPO_OWNER`, and `GITHUB_REPO_NAME` are configured.
- SQLite persistence works locally outside OneDrive locks and falls back to memory only when DB setup fails.
- GitHub dry-run write planning works without real GitHub network calls.
- Deployment health checks make real HTTP requests to configured public URLs.

## Placeholders

- Search, weather, and news have honest provider placeholders. API keys can be detected, but no provider adapter is implemented yet.
- Codex bridge creates a structured task package only. It does not execute Codex.
- External worker queue is a foundation. Tasks process immediately today.
- Deployment rollback is admin-protected but does not execute Cloud Run rollback.
- Gmail, Drive, and Calendar are listed as future connector placeholders.
- Repeated issue detection records lessons now, but deeper clustering is future work.
- Release checklist reports manual checks honestly instead of pretending tests already ran.

## Environment Variables

Copy `backend/.env.example` and set values in your runtime environment. Never commit real values.

Required for admin/write features:

- `ADMIN_TOKEN`
- `GITHUB_TOKEN`
- `GITHUB_REPO_OWNER`
- `GITHUB_REPO_NAME`

Optional or future connectors:

- `SEARCH_API_KEY`
- `WEATHER_API_KEY`
- `NEWS_API_KEY`
- `CODEX_API_KEY`
- `DATABASE_URL`
- `BUILDER_CORE_SQLITE_DIR`
- `BUILDER_CORE_FORCE_WORKSPACE_DB`
- `SEARCH_PROVIDER`
- `WEATHER_PROVIDER`
- `NEWS_PROVIDER`
- `GITHUB_DRY_RUN`
- `FRONTEND_ORIGIN`
- `BACKEND_PUBLIC_URL`
- `FRONTEND_PUBLIC_URL`
- `CORS_ALLOWED_ORIGINS`
- `BUILDER_CORE_DATA_DIR`

## Run Locally

Backend:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Open the frontend at `http://localhost:3000`.

## SQLite Storage

Default local SQLite is documented as `sqlite:///./data/builder_core.db`. Because this workspace is inside OneDrive, SQLite rollback journals can fail with disk I/O errors. Builder Core detects that case and stores the active default DB in a non-synced temp-local Builder Core data folder unless you set `DATABASE_URL`, `BUILDER_CORE_SQLITE_DIR`, or `BUILDER_CORE_FORCE_WORKSPACE_DB=true`.

To reset local DB state, stop the backend, then remove the active DB path shown in `GET /system/status` under `database.database_path`. Do not commit `.db` or `.db-*` files.

## Test Command Flow

1. Start the backend.
2. Start the frontend.
3. Send `What is Builder Core status?`.
4. Confirm the dashboard shows a real task id, backend stages, logs, final result, warnings, and connector status.

Backend direct test:

```powershell
cd backend
python -m pytest -q
```

If local bytecode cache permissions fail, run with:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s tests -v
```

Syntax check:

```powershell
python -m compileall app tests
```

## Admin Mode

Set `ADMIN_TOKEN` in the backend environment. In the frontend, enter the same token in the Admin token input. Protected routes include memory updates, GitHub writes, Codex packaging, and rollback placeholder.

## GitHub Connector

Set:

- `GITHUB_TOKEN`
- `GITHUB_REPO_OWNER`
- `GITHUB_REPO_NAME`

Then test:

- `GET /github/repo`
- `GET /github/commits`
- `POST /github/issues` with admin token
- `POST /github/branch` with admin token
- `POST /github/file` with admin token
- `POST /github/pull-request` with admin token

Write actions use the GitHub API. They do not expose the token.

`GITHUB_DRY_RUN=true` makes GitHub write endpoints return planned actions without calling GitHub. File writes to `main` or `master` are blocked by default; use generated branches such as `builder-core/task-{task_id}-{short-slug}`.

## Codex Package

Use:

```http
POST /integrations/codex/package-task
Authorization: Bearer <ADMIN_TOKEN>
```

Body:

```json
{
  "instruction": "Fix frontend/backend task polling",
  "repo": "jagangill001/builder-core"
}
```

The response is a structured package for Codex. It is not proof that Codex executed.

## Next Recommended Build Steps

- Add concrete provider adapters for search, weather, and news.
- Move task processing to a real worker queue for long-running work.
- Wire GitHub workflow/run status into deployment status.
- Add real Cloud Run rollback controls with audit logs and confirmation.
- Add persistent user/role storage if more than admin-token auth is needed.

## Push Flow

Before pushing:

```powershell
cd backend
python -m pytest -q
python -m compileall app tests
cd ..\frontend
npm run lint
npm run build
cd ..
git status
```

Confirm no secrets and no DB files are staged, then commit and push.
