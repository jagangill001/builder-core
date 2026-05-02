# Builder Core

Builder Core is now a Codex Prompt Command Center. It creates a real backend task, generates a strong Codex prompt, lets the user copy that prompt into Codex manually, then stores the pasted Codex result back into project memory and lessons.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Files Changed In This Upgrade
- `backend/app/main.py`
- `backend/app/prompt_builder.py`
- `backend/app/storage.py`
- `backend/app/learning.py`
- `backend/app/services/task_service.py`
- `frontend/src/app/page.tsx`
- `README.md`
- `COMMAND_CENTER.md`
- `PROJECT_PROGRESS.md`

## New Main Workflow
1. User enters a command in Builder Core.
2. Builder Core calls `POST /prompts/codex`.
3. Backend creates a real task and generates a Codex prompt.
4. Frontend shows the prompt in a copy box.
5. User copies the prompt into Codex manually.
6. Codex changes the repo outside Builder Core.
7. User pastes Codex’s final summary back into Builder Core.
8. Builder Core saves that summary into task history, memory, latest summary, and lessons.

## Why This Is Safer
- Builder Core does not pretend to change GitHub automatically.
- The user stays in control of the repo change step.
- Memory, learning, and task history are still real.
- Bridge status remains honest about missing GitHub or Codex credentials.

## What Is Real Now
- `POST /prompts/codex` creates a real task and real saved prompt.
- `GET /prompts/latest` returns the latest generated prompt.
- `POST /tasks/{task_id}/codex-summary` saves the pasted Codex result back into the backend.
- `GET /memory` returns memory, latest prompt, and latest summary.
- `GET /learning` returns lessons, known issues, recommended next steps, and project structure summary.
- The old backend task system, bridge status, storage, and learning remain in place.

## What Is Still Manual
- Copying the generated prompt into Codex
- Running Codex against the repo
- Pasting Codex’s final summary back into Builder Core

## What Still Needs Real Credentials Later
- real GitHub write automation
- real Codex execution from the backend
- real fully automatic deploy flow

No real GitHub automatic execution is part of the main workflow right now.

## Backend Endpoints

### Prompt workflow
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`

### Existing status, memory, and learning
- `GET /system/status`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `GET /memory`
- `POST /memory`
- `GET /learning`
- `POST /learning/scan`

### Existing builder routes still kept
- `POST /chat`
- `POST /plan`
- `GET /projects`
- `POST /projects`
- `GET /history`
- `GET /project-files`
- `GET /run-info`

## Storage Added And Used

### Task history
- Local fallback: `backend/runtime_data/automation_tasks.json`
- Stores:
  - task ID
  - command
  - status
  - stage
  - progress
  - generated prompt
  - pasted Codex summary
  - files changed
  - known issues
  - summary

### Project memory and latest summary
- Local fallback: `backend/runtime_data/project_memory.json`
- Stores:
  - memory entries
  - latest prompt
  - prompt history
  - latest summary
  - latest bridge status
  - lessons
  - project structure summary

### File storage
- Local fallback metadata: `backend/runtime_data/storage_files.json`
- Local fallback files: `backend/runtime_data/storage_files/`

## Cloud Storage Foundation
- Firestore-ready task abstraction still exists
- GCS-ready file abstraction still exists
- Local JSON fallback remains active until cloud configuration is enabled

Important:
- Cloud Run local storage is temporary.
- This fallback is good for development and MVP use, but later it should move to Firestore, Cloud SQL, Supabase, or another persistent database.

## Learning System

### What it can do now
- remember commands
- remember prompt generation history
- remember pasted Codex summaries
- extract likely files changed
- extract what was completed
- extract what still remains
- create a lesson
- recommend a next step

### What it cannot do yet
- train a custom AI model
- automatically understand all repo semantics
- automatically apply Codex changes

Builder Core is learning from project history, not training a new AI model.

## Required Environment Variables
Builder Core reads these on the backend:

- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=jagangill001/builder-core`
- `GITHUB_BRANCH=main`
- `CODEX_API_KEY=`
- `CODEX_MODE=disabled`
- `FRONTEND_URL=https://builder-core-frontend-599596796788.us-central1.run.app`
- `BACKEND_URL=https://builder-core-599596796788.us-central1.run.app`

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
- Keep backend and frontend deployed separately on Cloud Run.
- Backend entrypoint remains `backend/app/main.py` exporting `app`.
- Frontend still uses `API_BASE` and the current PWA setup.

## Legal And Safety Note
- Write original repo-specific code
- Do not copy external copyrighted code
- Do not add secrets to the frontend
- Do not fake GitHub, Codex, or deployment success
- Keep the manual Codex workflow explicit and honest
