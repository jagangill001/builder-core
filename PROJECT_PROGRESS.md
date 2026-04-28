# Builder Core Progress Summary

This file is a quick handoff for ChatGPT or Codex so they can understand what Builder Core already does, what changed recently, and what still needs work.

## Current Purpose
Builder Core is becoming a cloud-first AI command center for:
- receiving user instructions in one app UI
- responding through backend chat
- generating planning output and Codex-ready tasks
- tracking task progress
- checking GitHub workflow state
- preparing for real automation and cloud storage

## What Works Right Now
- Frontend and backend are deployed separately on Cloud Run.
- Frontend talks to backend through `API_BASE` using the deployed backend URL fallback.
- Backend health indicator checks `GET /system/status`.
- Command Center chat calls `POST /chat` and shows real assistant replies.
- The frontend creates real automation task records with `POST /automation/tasks`.
- The frontend polls `GET /automation/tasks/{id}` and syncs stage progress back with `PATCH /automation/tasks/{id}`.
- The stage progress bug is fixed so each stage now runs from `1%` to `100%`.
- Deploy tracking now reads `GET /automation/deploy-status`.
- The app is installable on phone through the existing PWA setup.

## Current Backend Endpoints
### Chat and builder
- `POST /chat`
- `POST /plan`
- `GET /projects`
- `POST /projects`
- `GET /history`
- `GET /project-files`
- `GET /run-info`
- `GET /system/status`

### Automation
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`
- `PATCH /automation/tasks/{id}`
- `GET /automation/github-status`
- `GET /automation/deploy-status`

### Storage
- `POST /storage/files`
- `GET /storage/files`
- `GET /storage/files/{id}`
- `DELETE /storage/files/{id}`

## Storage Model Today
### Task storage
- Firestore-ready service abstraction exists.
- If `FIRESTORE_ENABLED=true` and Google client setup is available, the backend can switch to Firestore.
- Otherwise it falls back to local JSON in `backend/runtime_data/automation_tasks.json`.

### File storage
- Google Cloud Storage-ready service abstraction exists.
- If `GCS_BUCKET_NAME` and Google client setup are available, the backend can switch to GCS.
- Otherwise it falls back to local metadata and files under `backend/runtime_data/`.

## GitHub Tracking
- Backend checks public repo and workflow state through GitHub API.
- If `GITHUB_TOKEN` is missing, the app returns a safe message instead of failing.
- Frontend shows repo, branch, latest commit, checks workflow, deploy workflow status, and live deploy health.

## Frontend UX Status
- Unified Command Center UI is in place.
- Compact task bar is in place.
- Progress automatically runs each stage from `1%` to `100%`.
- Manual `Next` is now the fallback instead of the primary way to move through the flow.
- Review, download/install, and help sections still exist.
- Mobile navigation and PWA install remain available.

## Environment Variables
### Storage
- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`
- `BACKEND_PUBLIC_URL=https://builder-core-599596796788.us-central1.run.app`
- `FRONTEND_PUBLIC_URL=https://builder-core-frontend-599596796788.us-central1.run.app`

### GitHub
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=builder-core`
- `GITHUB_DEFAULT_BRANCH=main`
- `GITHUB_CHECKS_WORKFLOW_NAME=Repo Checks`
- `GITHUB_DEPLOY_WORKFLOW_NAME=Deploy Cloud Run`

## Recent Milestones
- Added unified Command Center experience.
- Wired frontend command flow to backend `/chat`.
- Added compact task progress system.
- Added GitHub status tracking.
- Added cloud-first task storage foundation.
- Added Google Cloud SDK dependencies for future Firestore, Cloud Storage, and Secret Manager work.

## What Is Automatic Now
- Stage progress automatically runs from `1%` to `100%`.
- Deploy detection polls `GET /automation/deploy-status`.
- GitHub Deploying and Cloud Run Live can react to live backend signals when they match the current task.

## What Is Still Manual
- `Next` is still available as the fallback when a stage completes.
- Codex is not auto-triggered yet.
- Task history is not yet persisted in Firestore by default.
- Storage uploads are still local fallback unless cloud configuration is enabled.

## Best Next Upgrades
- Enable Firestore-backed task storage in production.
- Add `GET /automation/history`.
- Add Cloud Storage signed-upload flow.
- Add richer deploy history and rollback-aware rollout tracking.
- Add authenticated approval flow before automatic repo actions.

## Legal And Safety Notes
- Prefer original repo-specific code.
- Avoid blind copying from third-party sources.
- Use licensed frameworks normally.
- Keep automation gated by approval, auth, and logs.
