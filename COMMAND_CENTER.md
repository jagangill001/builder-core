# Builder Core Command Center

## Purpose
Builder Core is becoming a cloud-first AI command center that can accept one instruction, respond through backend chat, record a real task, track rollout progress, and prepare for future automation without depending on laptop storage.

## Current Workflow
User -> Command Center -> `/chat` + `/automation/tasks` -> task polling -> deploy polling -> review

### What happens now
1. The user enters a command in the Command tab.
2. Builder Core calls `POST /chat` for the assistant reply, plan, Codex-ready task, and next steps.
3. At the same time, Builder Core creates a task with `POST /automation/tasks`.
4. The frontend stores the returned task ID and polls `GET /automation/tasks/{id}`.
5. The compact task bar now runs each stage from `1%` to `100%` automatically.
6. The manual `Next` button remains as the fallback after a stage completes.
7. The Progress tab calls `GET /automation/deploy-status` for the latest GitHub workflow and live deploy state.
8. Review guidance stays visible after the task completes.

## Live Backend Endpoints

### Task storage
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`
- `PATCH /automation/tasks/{id}`

### GitHub tracking
- `GET /automation/github-status`
- `GET /automation/deploy-status`

### File storage
- `POST /storage/files`
- `GET /storage/files`
- `GET /storage/files/{id}`
- `DELETE /storage/files/{id}`

## Task Storage Model
Each automation task stores:
- `id`
- `command`
- `status`
- `current_stage`
- `progress`
- `github_commit`
- `workflow_status`
- `created_at`
- `updated_at`

### Storage behavior
- Firestore-ready structure exists now through the backend task service.
- Local JSON fallback is used automatically when Firestore is not enabled.
- This keeps the API stable while the storage backend changes later.

## File Storage Foundation
Builder Core now includes a file storage service abstraction.

### Local fallback today
- metadata file
- local runtime files

### Cloud-ready direction
- Firestore for task and history records
- Google Cloud Storage for uploaded or generated files
- Secret Manager for GitHub tokens, API keys, and future Codex credentials

## Environment Variables
These belong on the backend only.

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
- `BACKEND_PUBLIC_URL=https://builder-core-599596796788.us-central1.run.app`
- `FRONTEND_PUBLIC_URL=https://builder-core-frontend-599596796788.us-central1.run.app`

If GitHub is not configured, Builder Core returns a safe message instead of failing:
- `GitHub status not connected`
- The token stays on the backend only and is never exposed to the frontend.

## Cloud-First Architecture

### Firestore
- commands
- tasks
- progress
- history

### Cloud Storage
- uploaded files
- generated files

### Secret Manager
- GitHub token
- API keys
- future Codex credentials

### Cloud Run
- backend runtime
- frontend runtime

### GitHub
- code source of truth

Important note:
- Laptop and phone are control devices only, not permanent storage.

## Future Workflow
User -> Builder Core -> backend task -> auto Codex -> GitHub -> deploy -> status polling -> app refresh

### Next automation phase
1. User submits the command directly in Builder Core.
2. Backend creates the persistent cloud task.
3. After authentication and approval, Builder Core triggers Codex automatically.
4. GitHub receives the change request.
5. GitHub Actions deploys after checks pass.
6. Builder Core polls task, workflow, and deploy status from the backend.
7. The UI updates automatically and refreshes when the rollout is live.

## What Is Automatic Now
- Planning progress no longer stays stuck at `1%`.
- Each stage advances from `1%` to `100%`.
- Deploy tracking now polls `GET /automation/deploy-status`.
- GitHub Deploying and Cloud Run Live can react to live backend deploy signals when they belong to the current task.

## What Is Still Manual
- The `Next` button is still the fallback when a stage completes.
- Real Codex execution is still planned, not automatic.
- Firestore and Cloud Storage are still optional cloud backends until runtime config enables them.

## Future Endpoints
Still planned:
- `GET /automation/history`
- `POST /storage/files` with signed-upload support
- `GET /storage/files` with richer cloud metadata

## Navigation Meaning
- `Command`: talk to Builder Core and submit the next request
- `Progress`: watch the tracked stage bar and GitHub status
- `Review`: confirm the latest task result before trusting it
- `Download`: install the app on your phone or copy the live link
- `Help`: quick guidance for the current operating flow

## Logs, Auth, And Safety
- Authentication is required before future automation can act.
- Approval is required before automatic repo changes happen.
- Logs are required for every automated action.
- Codex should explain files changed, run checks when possible, and provide testing steps.

## Legal And Originality Rules
- Prefer original repo-specific implementations.
- Do not paste recognizable third-party snippets.
- Keep the code easy to read and easy to review.
- Use licensed frameworks such as Next.js, React, FastAPI, and SQLAlchemy in a normal supported way.
- Keep the project safe for commercial use by avoiding unknown copyrighted code.
