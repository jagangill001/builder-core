# Builder Core Command Center

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Current Product Direction
Builder Core is now:
- a local-first Builder Core Assistant
- a manual Codex Prompt Command Center
- a safe research task tracker
- a memory and lesson system
- a self-improvement note system

## Files Changed In This Upgrade
- `backend/app/main.py`
- `backend/app/chat_assistant.py`
- `backend/app/research_tasks.py`
- `backend/app/self_improvement.py`
- `backend/app/storage.py`
- `backend/app/prompt_builder.py`
- `backend/app/learning.py`
- `backend/.env.example`
- `frontend/src/app/page.tsx`
- `README.md`
- `COMMAND_CENTER.md`
- `PROJECT_PROGRESS.md`

## Main User Flow
1. User opens Builder Core.
2. User chats with Builder Core Assistant.
3. User can:
   - save useful info to memory
   - generate ideas
   - create a research task
   - generate a Codex prompt
4. User copies the prompt into Codex manually.
5. Codex performs the repo work outside Builder Core.
6. User pastes Codex's final summary back into Builder Core.
7. Builder Core saves:
   - task history
   - prompt history
   - codex summary
   - memory
   - lessons
   - self-improvement notes

## Builder Core Assistant

### Endpoints
- `POST /assistant/chat`
- `GET /assistant/history`
- `POST /assistant/idea`

### What it does
- understands the current project context
- uses saved memory and lessons
- gives natural local-first replies
- suggests next actions
- can save useful chats to memory
- can propose ideas for:
  - app features
  - coding improvements
  - business ideas
  - research angles
  - exam strategies
  - legal-information structure
  - market-analysis structure
  - project improvements

### Honest assistant statements
The assistant should keep saying clearly:
- `I can research this when you ask me.`
- `I can save this to memory.`
- `I can create a research task.`
- `I can use previous memory and lessons.`
- `I do not automatically know new internet information unless research is run.`

### Local-first mode
If `OPENAI_API_KEY` is missing:
- `Local assistant mode is running. Add OPENAI_API_KEY later for stronger AI replies.`

## Codex Prompt Command Center

### Endpoints
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`

### What happens
- Builder Core generates the prompt
- user copies it into Codex
- Codex edits the repo manually outside Builder Core
- user pastes the final Codex summary back
- Builder Core stores that result for memory and learning

## Research Tasks

### Endpoints
- `POST /research/tasks`
- `GET /research/tasks`
- `GET /research/tasks/{research_id}`

### What happens
- research tasks are created and saved
- research can use:
  - memory
  - user notes placeholder
  - web placeholder
- research results are stored honestly

### Safety rule
Web research is not connected yet in this build.

Builder Core must not fake live internet findings.

When web research is requested, it says:
- `Web research is not connected yet. This task was saved and can use provided notes/memory only.`

## Self-Improvement Notes

### Endpoints
- `GET /self-improvement`
- `POST /self-improvement`

### What it stores
- user messages
- assistant replies
- what worked
- what failed
- repeated preferences
- better future instructions
- project lessons
- next recommended improvement

This is memory-based improvement only.
It is not real AI model training.

## What Is Real Now
- assistant chat
- assistant history
- idea generation
- research task creation
- research task storage
- self-improvement notes
- prompt generation
- summary save-back
- memory and lesson updates

## What Is Still Manual
- copying the prompt into Codex
- running Codex
- reviewing Codex changes
- pasting Codex's final summary back

## What Is Not Real Yet
- real Codex execution from Builder Core
- real GitHub automatic repo editing
- real live web research
- real secret background scheduling

## Why This Is Safer
- user stays in control of repo changes
- the app does not invent internet research
- the app does not pretend it trained an AI model
- storage and memory remain visible and understandable
- future automation can be added later with approval

## Local Storage And Cloud Plan

### Local fallback today
- `backend/runtime_data/automation_tasks.json`
- `backend/runtime_data/project_memory.json`
- `backend/runtime_data/storage_files.json`

### Cloud-ready direction
- Firestore for:
  - assistant memory
  - chat history
  - research tasks
  - project memory
  - lessons
  - self-improvement notes
- Google Cloud Storage for:
  - uploaded files
  - generated outputs
- Secret Manager for:
  - GitHub token
  - future assistant API keys
  - future Codex credentials

Cloud Run local storage is temporary, so local JSON is still only a fallback.

## Future Scheduled Research
Scheduled research can be added later only if:
- the user explicitly approves it
- the schedule is visible
- the scope is limited
- the sources are clear
- the logs are visible
- the app stays honest about missing web access

No secret background work should be added.

## How To Run Locally

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

### Frontend build
```powershell
cd frontend
npm run build
```

## How To Deploy
- Push to `main`
- Let the existing GitHub Actions / Cloud Run flow deploy backend and frontend
- Keep frontend and backend as separate Cloud Run services

## Required Environment Variables
- `STORAGE_MODE=local`
- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`
- `OPENAI_API_KEY=`
- `ASSISTANT_MODE=local`
- `ASSISTANT_MODEL=`
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=jagangill001/builder-core`
- `GITHUB_BRANCH=main`
- `CODEX_API_KEY=`
- `CODEX_MODE=disabled`
- `FRONTEND_URL=https://builder-core-frontend-599596796788.us-central1.run.app`
- `BACKEND_URL=https://builder-core-599596796788.us-central1.run.app`
