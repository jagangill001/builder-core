# Builder Core Command Center

The command center is a backend-owned workflow. The frontend sends commands and displays returned state; it does not invent progress.

## Task Engine Flow

1. `POST /tasks/create` receives the command.
2. Backend creates a `task_id`.
3. Backend records `received`.
4. Safety firewall runs.
5. Router classifies the command.
6. Answer brain or connector workflow runs.
7. Backend writes logs, result, warnings, errors, and sources.
8. Backend saves a task summary.
9. Frontend polls `GET /tasks/{task_id}` and displays state.

## Task Fields

Every task includes:

- `task_id`
- `original_message`
- `normalized_message`
- `detected_intents`
- `workflow`
- `status`
- `progress`
- `current_stage`
- `logs`
- `result`
- `sources`
- `warnings`
- `errors`
- `created_at`
- `updated_at`

## Stages

- `received`
- `safety_check`
- `planning`
- `routing`
- `executing`
- `summarizing`
- `completed`
- `failed`

## Core Endpoints

- `POST /tasks/create`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/logs`
- `GET /tasks/{task_id}/workflow`
- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/retry`
- `GET /system/status`
- `GET /system/self-test`
- `GET /system/release-checklist`
- `GET /connectors`
- `GET /connectors/{name}/status`
- `GET /project/summary`
- `POST /project/memory/update`
- `GET /project/lessons`
- `GET /project/recommendations`
- `GET /deployment/status`
- `GET /deployment/checklist`
- `GET /deployment/health`
- `POST /deployment/rollback`
- `GET /audit/logs`
- `GET /integrations/status`
- `POST /integrations/github/create-issue`
- `POST /integrations/codex/package-task`
- `GET /github/repo`
- `GET /github/commits`
- `POST /github/issues`
- `POST /github/branch`
- `POST /github/file`
- `POST /github/pull-request`
- `POST /github/plan-change`
- `POST /github/create-branch`
- `POST /github/create-file-change`
- `POST /github/open-pr`

## Command Examples

These commands work honestly:

- `What is Builder Core status?`
- `Check backend connection`
- `Create a GitHub issue for frontend bug`
- `Package this task for Codex`
- `Summarize project progress`
- `Show connector status`
- `Show deployment checklist`
- `What should I build next?`

Some commands return placeholders because real external execution is not connected yet. For example, weather/news/search provider execution, Codex execution, external workers, and rollback controls are labeled clearly.

Connector cards show `Real`, `Placeholder`, or `Not configured` based on backend connector status. Search, weather, and news support `SEARCH_PROVIDER`, `WEATHER_PROVIDER`, and `NEWS_PROVIDER` values of `none`, `placeholder`, or `custom`; no provider currently performs real external execution.

## Errors The UI Should Surface

- Backend unavailable.
- Task failed.
- Connector not configured.
- Invalid command.
- Auth required.
- Admin required.

## Admin Controls

Admin-only actions require `ADMIN_TOKEN` on the backend and a matching bearer token in the request. The frontend stores the token only in browser state.

Admin-only actions include:

- Updating project memory.
- Creating GitHub issues.
- Packaging Codex tasks.
- Deployment rollback placeholder.
- GitHub branch/file/PR writes.
- Reading audit logs.

## Audit Logs

Protected write actions record safe audit entries with timestamp, action, route, success/failure, actor role label, and warning/error summaries. Tokens are never stored.

## Self-Test And Release Checklist

`GET /system/self-test` runs backend checks for task creation, task store, DB status, connector registry, project memory, safety blocking, and admin-route protection.

`GET /system/release-checklist` lists manual release checks. It does not pretend backend tests, frontend lint, or frontend build have passed.
