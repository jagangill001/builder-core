# Builder Core

Builder Core is a manual Codex Prompt Command Center with an Intelligence Center. It helps the user turn one command into a safer research plan, a stronger Codex prompt, saved project memory, and reusable lessons.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Files Changed In This Upgrade
- `backend/app/main.py`
- `backend/app/intelligence.py`
- `backend/app/prompt_builder.py`
- `backend/app/storage.py`
- `backend/app/learning.py`
- `backend/app/services/task_service.py`
- `frontend/src/app/page.tsx`
- `README.md`
- `COMMAND_CENTER.md`
- `PROJECT_PROGRESS.md`

## What Changed
- Added an Intelligence Center for:
  - safe research
  - law and policy planning
  - market analysis
  - exam planning
  - forecasting
  - language learning
  - video transcript learning
  - self-improvement memory
- Added backend intelligence endpoints:
  - `POST /intelligence/plan`
  - `GET /intelligence`
- Extended `POST /prompts/codex` so each generated prompt includes intelligence context, a safety firewall, memory signals, and learning signals.
- Extended storage so Builder Core now saves:
  - latest intelligence brief
  - intelligence history
  - prompt history
  - latest summary
- Extended learning so pasted Codex summaries can carry intelligence mode context into lessons.
- Rebuilt the frontend page so the Intelligence Center is a first-class part of the manual Codex workflow.

## Main Workflow
1. User enters one command.
2. Builder Core creates an intelligence brief and a tracked task.
3. Builder Core generates a Codex prompt.
4. User copies the prompt into Codex manually.
5. Codex makes repo changes outside Builder Core.
6. User pastes Codex's final summary back into Builder Core.
7. Builder Core saves:
   - task history
   - memory entries
   - latest summary
   - lesson learned
   - next recommended step

## Why This Is Safer
- Builder Core does not pretend to edit GitHub automatically.
- The user remains in control of the actual repo-change step.
- Legal, market, forecasting, and transcript work stays structured and honest.
- The app keeps memory and learning without claiming it trained a real AI model.

## What Is Real Now
- real intelligence brief generation
- real prompt generation
- real task ID creation
- real prompt storage
- real intelligence history storage
- real Codex summary storage
- real project memory updates
- real learning lesson creation
- real latest summary updates

## What Is Still Manual
- copying the generated prompt into Codex
- running Codex
- reviewing what Codex changed
- pasting Codex's summary back into Builder Core

## What Is Still Disabled
- real GitHub automatic repo editing
- real Codex execution from the backend
- real automatic deployment control

No real repo changes can happen from Builder Core alone until bridge credentials and a real executor are added.

## Intelligence Center Modes
- Safe Research
- Law and Policy Planning
- Market Analysis
- Exam Planning
- Forecasting
- Language Learning
- Video Transcript Learning
- Self-Improvement Memory

## Safety Firewall
The Intelligence Center adds explicit guardrails:
- do not invent sources, legal conclusions, or market data
- do not imply Builder Core replaced a qualified professional
- separate verified facts from assumptions
- keep manual verification steps visible
- stay honest about missing context

## Backend Endpoints

### Intelligence and prompt flow
- `POST /intelligence/plan`
- `GET /intelligence`
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`

### Existing task, memory, and learning routes kept
- `GET /system/status`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `POST /tasks`
- `GET /memory`
- `POST /memory`
- `GET /learning`
- `POST /learning/scan`

## Storage Used Today

### Task history
- `backend/runtime_data/automation_tasks.json`

### Project memory, prompt history, intelligence history, and latest summary
- `backend/runtime_data/project_memory.json`

### File metadata
- `backend/runtime_data/storage_files.json`

### Local file fallback
- `backend/runtime_data/storage_files/`

## Storage Limits On Cloud Run
This local JSON storage works for development and fallback use, but Cloud Run local storage is temporary.

Future upgrade options:
- Firestore
- Cloud SQL
- Supabase
- another persistent database or hosted store

## Learning System

### What it can do now
- remember commands
- remember prompt history
- remember intelligence briefs
- remember pasted Codex summaries
- extract likely files changed
- extract likely completed work
- extract likely remaining setup
- create lessons
- recommend next steps

### What it cannot do yet
- train a custom AI model
- execute Codex automatically
- modify GitHub automatically
- guarantee perfect parsing of every pasted summary

Builder Core is learning from project history and saved summaries. It is not training a new AI model.

## Required Environment Variables
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

## Run Locally

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
- Backend and frontend stay as separate Cloud Run services.
- Backend entrypoint remains `backend/app/main.py` exporting `app`.
- Frontend still uses the existing `API_BASE` flow.
- No new secrets were added to the frontend.

## Legal And Safety Note
- Write original repo-specific code
- Do not copy external copyrighted code
- Do not add secrets to the frontend
- Do not fake GitHub, Codex, or deployment success
- Keep research and expert-style planning honest and limited
