# Builder Core

Builder Core is a cloud-first AI command center for Builder Core repo work. The frontend sends one command, the backend creates a real tracked task, the task runs through backend-controlled stages, and the UI polls the backend for live logs, errors, and the final summary.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Files Edited In This Upgrade
- `backend/app/main.py`
- `backend/app/tasks.py`
- `backend/app/storage.py`
- `backend/app/bridge.py`
- `backend/app/learning.py`
- `backend/app/services/task_service.py`
- `backend/.env.example`
- `frontend/src/app/page.tsx`
- `README.md`
- `COMMAND_CENTER.md`
- `PROJECT_PROGRESS.md`

## What Changed
- Added a real backend task runner with background execution.
- Added `POST /tasks`, `GET /tasks`, `GET /tasks/{task_id}`, and `PATCH /tasks/{task_id}`.
- Added persistent local JSON task history with richer task fields such as logs, errors, summary, bridge status, and stage history.
- Added persistent project memory and learning storage.
- Added learning endpoints and a project structure scan.
- Added honest GitHub/Codex bridge checks.
- Replaced frontend fake progress with backend task polling.

## What Is Real Now
- Task creation is real and stored by the backend.
- Task stage, progress, logs, errors, and final summary come from the backend.
- The frontend polls real backend task state.
- Project memory is saved to local JSON storage.
- Learning lessons are saved from completed or failed task runs.
- Backend deploy health checks are real when URLs are reachable.
- GitHub workflow checks are real if `GITHUB_TOKEN` is configured.

## What Is Still Not Real
- No real Codex repo execution is implemented yet.
- No real GitHub repo change is performed by the backend.
- Firestore is not the default task or memory backend yet.
- Cloud Storage upload flow is still local fallback by default.

If bridge credentials are missing or Codex is disabled, Builder Core now says so clearly:

`No real repo changes can happen until credentials are added.`

## Backend Endpoints

### Core task runner
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`

### Memory and learning
- `GET /memory`
- `POST /memory`
- `GET /learning`
- `POST /learning/scan`

### Existing builder and status routes
- `POST /chat`
- `POST /plan`
- `GET /projects`
- `POST /projects`
- `GET /history`
- `GET /project-files`
- `GET /run-info`
- `GET /system/status`
- `GET /automation/github-status`
- `GET /automation/deploy-status`
- `POST /storage/files`
- `GET /storage/files`
- `GET /storage/files/{id}`
- `DELETE /storage/files/{id}`

## Storage Added

### Task history
- Stored through `AutomationTaskService`
- Local fallback path: `backend/runtime_data/automation_tasks.json`
- Firestore-ready abstraction remains in place for future production use

### Project memory and latest summary
- Stored through `ProjectStorageService`
- Local path: `backend/runtime_data/project_memory.json`

### File storage metadata
- Stored through `FileStorageService`
- Local fallback files:
  - `backend/runtime_data/storage_files.json`
  - `backend/runtime_data/storage_files/`

## Limits Of Local Storage On Cloud Run
- Cloud Run local filesystem storage is temporary.
- It is useful for development and MVP fallback, but it is not a reliable long-term production database.
- If the service restarts or scales differently, local files may not be durable.

## Future Storage Upgrade Path
- Firestore: tasks, commands, progress, history, memory entries, lessons
- Cloud SQL or Supabase: relational project history and richer reporting
- Google Cloud Storage: uploaded files and generated output files
- Secret Manager: GitHub token, API keys, future Codex credentials

## Learning System: What It Can Do Now
- Scan and summarize project structure
- Save lessons from successful or failed tasks
- Save known issues from recent errors
- Suggest recommended next steps based on project memory and bridge problems

## Learning System: What It Cannot Do Yet
- It does not train a custom AI model
- It does not automatically rewrite the repo
- It does not understand every file semantically
- It does not perform autonomous Codex execution

Learning in this phase means:
- storing project history
- recording outcomes
- summarizing patterns
- helping the next task start from better context

It does **not** mean training a new AI model.

## Required Environment Variables
Set these in Cloud Run backend settings when you are ready:

### Storage
- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`

### Bridge
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=jagangill001/builder-core`
- `GITHUB_BRANCH=main`
- `CODEX_API_KEY=`
- `CODEX_MODE=disabled`

### Public URLs
- `FRONTEND_URL=https://builder-core-frontend-599596796788.us-central1.run.app`
- `BACKEND_URL=https://builder-core-599596796788.us-central1.run.app`

See `backend/.env.example` for the full current template.

## Local Run

### Backend
```powershell
cd backend
uvicorn app.main:app --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

## Deploy
- Backend and frontend remain separate Cloud Run services.
- Backend entrypoint remains `backend/app/main.py` exporting `app`.
- Backend startup remains compatible with:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- Frontend still uses the existing `API_BASE` environment logic and PWA setup.

## Legal And Safety Note
- Prefer original repo-specific code
- Avoid copying third-party project code
- Use licensed frameworks normally
- Keep GitHub and Codex credentials backend-only
- Be honest about missing automation or missing credentials
