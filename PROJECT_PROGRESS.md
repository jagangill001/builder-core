# Builder Core Progress Summary

This file is the fastest handoff for ChatGPT or Codex before doing the next Builder Core upgrade.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## What Changed In This Upgrade
- Added a real backend task runner.
- Added real backend task polling endpoints.
- Added persistent local JSON task history with logs, errors, summary, and bridge status.
- Added project memory storage.
- Added learning storage and project structure scanning.
- Replaced frontend fake progress with backend stage and progress polling.
- Added honest bridge checks for GitHub and Codex configuration.

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

## Current Purpose
Builder Core is now a real command center shell with:
- one command input
- real backend task creation
- real backend stage tracking
- real task logs and errors
- real saved summaries
- real project memory
- simple learning from project history

## What Is Real Now
- `POST /tasks` creates a real backend task record.
- `GET /tasks/{task_id}` returns real backend progress, logs, errors, and summary.
- `GET /tasks` returns recent saved tasks.
- `GET /memory` returns project memory and the latest summary.
- `GET /learning` returns lessons, known issues, recommended next steps, and project structure summary.
- `GET /automation/deploy-status` returns real backend health checks and real GitHub workflow status when the token exists.

## What Is Still Not Real
- Real Codex repo execution is not implemented yet.
- Real GitHub write actions are not implemented from the backend yet.
- Real repo changes cannot happen until bridge credentials are added and a real executor is built.
- Firestore and Cloud Storage are still optional future backends.

## Storage Used Today
- Task history: `backend/runtime_data/automation_tasks.json`
- Memory and latest summary: `backend/runtime_data/project_memory.json`
- File storage metadata: `backend/runtime_data/storage_files.json`
- Local file storage fallback: `backend/runtime_data/storage_files/`

## Cloud-First Direction
- Firestore: future task, history, memory, and lesson storage
- Cloud Storage: future uploaded and generated file storage
- Secret Manager: future GitHub, Codex, and API credentials
- Cloud Run: frontend and backend runtime
- GitHub: code source of truth

Important:
- Laptop and phone are control devices only.
- Current local JSON storage is a fallback, not a permanent cloud database.

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

## Learning System Status

### What it can do now
- scan project structure
- save lessons from each task
- save known issues from recent failures
- recommend next steps based on recent summaries and bridge problems

### What it cannot do yet
- train a new AI model
- reason over the full repo deeply
- make autonomous repo changes
- infer real code changes without a real bridge/executor

Builder Core is learning from:
- project structure
- saved tasks
- saved summaries
- saved lessons

It is **not** training a custom AI model.

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

## Next Safe Upgrade
- Add a real backend executor once GitHub and Codex credentials are available.
- Move memory and lessons from local JSON fallback to Firestore.
- Move file storage from local fallback to Cloud Storage.
- Add authenticated approval before any real repo write action.

## Latest Codex Work Summary
- Date/time: 2026-05-02 America/Toronto
- Folder used: `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`
- Files changed:
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
- Problem fixed:
  - fake frontend-only progress was replaced with backend task tracking
  - Builder Core now saves task history, memory, and learning notes
  - bridge status is now honest about missing GitHub or Codex credentials
- Current status:
  - backend task system is real
  - storage is real with local JSON fallback
  - learning is real as a saved knowledge system
  - no real repo changes can happen until credentials are added
- Remaining setup required:
  - add `GITHUB_TOKEN`
  - add `CODEX_API_KEY`
  - choose whether to keep `CODEX_MODE=disabled` or enable it later
  - migrate task, memory, and lesson storage to Firestore or another real database for long-term Cloud Run persistence
