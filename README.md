# Builder Core

Builder Core is a cloud-first AI command center for planning repo changes, generating Codex-ready tasks, tracking rollout progress, and reviewing the latest result from phone or desktop.

## Live Services
- Frontend: https://builder-core-frontend-599596796788.us-central1.run.app
- Backend: https://builder-core-599596796788.us-central1.run.app

## What Works Now
- The Command Center sends instructions to `POST /chat` and shows the assistant reply inline.
- The frontend creates a real automation task with `POST /automation/tasks`.
- The app polls `GET /automation/tasks/{id}` to keep task ID, stage, progress, and workflow status in sync.
- The compact progress bar still runs with the manual `Next` fallback so the current flow stays safe.
- The Progress tab reads GitHub workflow data from `GET /automation/github-status`.
- The app keeps working on phone with the existing PWA install flow.

## Current Backend Endpoints

### Chat And Builder
- `POST /chat`
- `POST /plan`
- `GET /projects`
- `POST /projects`
- `GET /history`
- `GET /project-files`
- `GET /run-info`
- `GET /system/status`

### Automation Tasks
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`
- `PATCH /automation/tasks/{id}`
- `GET /automation/github-status`

### File Storage
- `POST /storage/files`
- `GET /storage/files`
- `GET /storage/files/{id}`
- `DELETE /storage/files/{id}`

## Cloud-First Task Tracking
Builder Core now stores task state through a storage abstraction.

### Task fields
- `id`
- `command`
- `status`
- `current_stage`
- `progress`
- `github_commit`
- `workflow_status`
- `created_at`
- `updated_at`

### How it works today
- If Firestore is not enabled, tasks are stored in `backend/runtime_data/automation_tasks.json`.
- The frontend still works with the manual `Next` button, but the task record is now real and pollable.
- GitHub workflow details are synced into the task record from the frontend-safe backend flow.

## Cloud-First Storage Foundation

### Firestore
Planned source of truth for:
- commands
- tasks
- progress
- history

### Cloud Storage
Prepared for:
- uploaded files
- generated files

### Secret Manager
Recommended home for:
- GitHub token
- API keys
- future Codex credentials

### Cloud Run
- backend runtime
- frontend runtime

### GitHub
- code source of truth

Important note:
- Laptop is only the control device. All long-term task and file storage should live in cloud services.

## Environment Variables
Builder Core reads environment variables only from the backend runtime.

### Storage
- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`

### GitHub
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=builder-core`
- `GITHUB_DEFAULT_BRANCH=main`
- `GITHUB_CHECKS_WORKFLOW_NAME=Repo Checks`
- `GITHUB_DEPLOY_WORKFLOW_NAME=Deploy Cloud Run`

See [backend/.env.example](backend/.env.example) for the starter shape.

## Local Fallback Behavior
- If `FIRESTORE_ENABLED` is not `true`, Builder Core uses local JSON task storage.
- If `GCS_BUCKET_NAME` is missing, Builder Core uses local file storage metadata plus local file fallback.
- If `GITHUB_TOKEN` is missing, the backend returns `GitHub status not connected` instead of failing the UI.

## Future Endpoints
These are still planned for the next automation phase:
- `GET /automation/history`
- `POST /storage/files` with direct signed-upload flow
- `GET /storage/files` with richer cloud metadata

## Deployment Notes
- Backend and frontend are deployed separately to Cloud Run.
- The frontend uses `NEXT_PUBLIC_API_BASE_URL` or `NEXT_PUBLIC_API_URL` and falls back to the deployed backend URL.
- GitHub status is requested only through the backend so secrets never reach the frontend.

## Legal And Originality Note
This project is intended to use original, repo-specific code plus licensed open-source libraries such as Next.js, React, FastAPI, and SQLAlchemy.

When adding features:
- prefer fresh implementations over copied snippets
- avoid unknown copyrighted code
- refactor generic patterns into the repo's own structure
- keep the result readable, safe, and suitable for commercial use

## License
This project is released under the MIT License. See `LICENSE` for details.
