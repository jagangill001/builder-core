# Builder Core Command Center

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## What Changed In This Upgrade
- Builder Core now creates real backend tasks with `POST /tasks`.
- The backend runs those tasks in the background.
- The frontend polls task status from `GET /tasks/{task_id}`.
- Progress is now driven by backend stage updates.
- Project memory and learning data are stored persistently in local JSON fallback files.
- GitHub and Codex bridge checks are honest and backend-only.

## Files Edited
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

## Current Workflow
1. User enters one command in the frontend.
2. Frontend calls `POST /tasks`.
3. Backend creates a persistent task record.
4. Backend starts the task runner in the background.
5. Frontend polls `GET /tasks/{task_id}`.
6. Backend updates stage, progress, logs, errors, and final summary.
7. Frontend shows real task state, memory, and learning panels.

## Current Task Stages
- `received`
- `planning`
- `bridge_check`
- `codex_working`
- `testing`
- `deploy_check`
- `summary`
- `completed`
- `failed`

## What The Backend Checks During A Task

### Planning
- records the command
- builds a simple safe plan

### Bridge check
- checks `GITHUB_TOKEN`
- checks `GITHUB_REPO`
- checks `GITHUB_BRANCH`
- checks `CODEX_API_KEY`
- checks `CODEX_MODE`
- records missing configuration honestly

### Codex working
- does **not** fake repo changes
- if bridge credentials are missing or Codex mode is disabled, Builder Core records that honestly

### Testing
- verifies important backend routes exist
- verifies task storage works
- verifies memory storage works

### Deploy check
- checks GitHub workflow status if the token exists
- checks backend `/system/status`
- checks the frontend URL

### Summary
- saves a final task summary
- saves a project memory entry
- saves a learning lesson

## Honest Bridge Rule
If the repo bridge is not ready, Builder Core must say:

`No real repo changes can happen until credentials are added.`

That means:
- no fake GitHub commit success
- no fake Codex execution
- no fake deploy success

## What Is Automatic Now
- real backend task creation
- real backend task polling
- real backend logs
- real backend errors
- real final summary generation
- real saved task history
- real saved project memory
- real saved learning lessons

## What Is Still Manual Or Missing
- real Codex execution
- real repo commits from the backend
- real automatic GitHub write actions
- Firestore as the default storage backend
- Cloud Storage as the default upload backend

## Cloud-First Architecture

### Cloud Run
- frontend runtime
- backend runtime

### Firestore
Planned long-term home for:
- tasks
- commands
- progress
- history
- memory entries
- lessons

### Cloud Storage
Planned long-term home for:
- uploaded files
- generated files

### Secret Manager
Recommended home for:
- `GITHUB_TOKEN`
- `CODEX_API_KEY`
- future provider keys

### GitHub
- source of truth for code

### Laptop And Phone
- control devices only
- not long-term storage

## Future Backend Endpoints
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`
- `GET /automation/history`
- `POST /storage/files`
- `GET /storage/files`

## Local Storage Paths Today
- Task history: `backend/runtime_data/automation_tasks.json`
- Memory and latest summary: `backend/runtime_data/project_memory.json`
- File storage metadata: `backend/runtime_data/storage_files.json`

## Limits Of Current Storage
- Local files on Cloud Run are temporary.
- They are fine for development or fallback use.
- They should be replaced later with Firestore, Cloud SQL, Supabase, or another persistent cloud database.

## Running Locally

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

## Required Environment Variables
- `FIRESTORE_ENABLED`
- `GCP_PROJECT_ID`
- `GCS_BUCKET_NAME`
- `GITHUB_TOKEN`
- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_BRANCH`
- `CODEX_API_KEY`
- `CODEX_MODE`
- `FRONTEND_URL`
- `BACKEND_URL`

## Legal And Safety Rules
- Write original code for this repo
- Do not copy external project code blindly
- Keep secrets backend-only
- Keep logs and summary honest
- Explain missing credentials clearly
