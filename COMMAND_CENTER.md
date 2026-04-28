# Builder Core Command Center

## Purpose
Builder Core is becoming a cloud-first AI command center that can accept one instruction, respond through backend chat, record a real task, track rollout progress, and prepare for future automation without depending on laptop storage.

## Current Workflow
User -> Command Center -> `/chat` + `/automation/tasks` -> task polling -> GitHub tracking -> review

### What happens now
1. The user enters a command in the Command tab.
2. Builder Core calls `POST /chat` for the assistant reply, plan, Codex-ready task, and next steps.
3. At the same time, Builder Core creates a task with `POST /automation/tasks`.
4. The frontend stores the returned task ID and polls `GET /automation/tasks/{id}`.
5. The compact task bar continues to run the simple stage flow with the single `Next` button.
6. The Progress tab calls `GET /automation/github-status` for the latest checks and deploy state.
7. Review guidance stays visible after the task completes.

## Live Backend Endpoints

### Task storage
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`
- `PATCH /automation/tasks/{id}`

### GitHub tracking
- `GET /automation/github-status`

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

If GitHub is not configured, Builder Core returns a safe message instead of failing:
- `GitHub status not connected`

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
