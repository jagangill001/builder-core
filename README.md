# Builder Core

Builder Core is now a manual Codex Prompt Command Center plus a local-first Builder Core Assistant.

It can:
- chat with the user naturally
- generate Codex prompts for manual repo work
- save Codex summaries back into task history
- store project memory
- create learning lessons
- save research tasks
- save self-improvement notes

It does not pretend to edit GitHub automatically in the main workflow.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

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

## What Changed
- Added `POST /assistant/chat` and `GET /assistant/history`
- Added `POST /assistant/idea`
- Added `POST /research/tasks`, `GET /research/tasks`, and `GET /research/tasks/{research_id}`
- Added `GET /self-improvement` and `POST /self-improvement`
- Extended storage for:
  - chat history
  - assistant memory
  - research tasks
  - research results
  - self-improvement notes
  - codex prompts
  - codex summaries
  - learning lessons
- Rebuilt the frontend into six clear sections:
  1. Builder Core Assistant
  2. Codex Prompt Command Center
  3. Research Tasks
  4. Builder Memory
  5. Project Learning
  6. Self-Improvement Notes

## Main Workflow
1. User chats with Builder Core Assistant.
2. Builder Core can save useful context to memory.
3. Builder Core can generate a Codex prompt.
4. User copies the prompt into Codex manually.
5. Codex makes repo changes outside Builder Core.
6. User pastes Codex's final summary back into Builder Core.
7. Builder Core saves:
   - task history
   - codex summary
   - project memory
   - lessons
   - self-improvement notes
8. Builder Core recommends the next safe step.

## Builder Core Assistant

### What it can do now
- chat in these modes:
  - general
  - coding
  - research
  - law
  - market
  - exam
  - project
  - creative
- use saved project memory
- use assistant memory
- use learning lessons
- use the latest saved Codex summary
- generate safe next-step suggestions
- generate ideas
- create research tasks
- save useful chats to memory

### Honest assistant rules
The assistant says clearly:
- `I can research this when you ask me.`
- `I can save this to memory.`
- `I can create a research task.`
- `I can use previous memory and lessons.`
- `I do not automatically know new internet information unless research is run.`

If `OPENAI_API_KEY` is missing, the assistant stays local-first and says:
- `Local assistant mode is running. Add OPENAI_API_KEY later for stronger AI replies.`

## Research Tasks

### What is real now
- research tasks are created and saved
- research tasks can run immediately in local safe mode
- research tasks can use:
  - memory
  - user_notes placeholder
  - web placeholder
- research results are saved
- research lessons are saved

### What is not real yet
- real web research is not connected
- no secret background browsing happens
- no dark web access exists
- no automatic forever-running research exists

When web research is requested, Builder Core stays honest:
- `Web research is not connected yet. This task was saved and can use provided notes/memory only.`

## Self-Improvement Memory
This is not real AI model training.

Builder Core can now save:
- user messages
- assistant replies
- what worked
- what failed
- better future instructions
- repeated user preferences
- project lessons
- next recommended improvements

This helps Builder Core improve future prompts and assistant responses using saved memory only.

## Storage Used Today

### Local JSON fallback
- Task history: `backend/runtime_data/automation_tasks.json`
- Memory, chat history, research tasks, self-improvement notes, prompts, summaries, and lessons: `backend/runtime_data/project_memory.json`
- File metadata: `backend/runtime_data/storage_files.json`
- Local file fallback: `backend/runtime_data/storage_files/`

### Cloud-first note
Cloud Run local storage is temporary.

For real permanent memory later, move this data to:
- Firestore
- Cloud SQL
- Supabase
- another real persistent database

## Google Cloud-Ready Plan
Builder Core is prepared for cloud-first storage later.

Planned cloud roles:
- Cloud Run:
  - backend runtime
  - frontend runtime
- Firestore:
  - project memory
  - assistant memory
  - chat history
  - research tasks
  - research results
  - learning lessons
  - self-improvement notes
- Google Cloud Storage:
  - uploaded files
  - generated outputs
- Secret Manager:
  - GitHub token
  - future assistant API keys
  - future Codex credentials

Laptop or phone should remain a control device only, not the permanent storage system.

## What Is Real Now
- assistant chat endpoint
- assistant history endpoint
- idea generation endpoint
- research task endpoints
- self-improvement endpoints
- prompt generation
- prompt storage
- Codex summary save-back
- project memory updates
- lesson creation
- recent task history

## What Still Needs API Keys
- stronger assistant replies with a future LLM path:
  - `OPENAI_API_KEY`
- real GitHub bridge work:
  - `GITHUB_TOKEN`
- real Codex execution later:
  - `CODEX_API_KEY`

## What Is Still Manual
- copying the generated prompt into Codex
- running Codex
- reviewing what Codex changed
- pasting Codex's final summary back

## What Is Not Automatic Yet
- no real Codex execution from Builder Core
- no real GitHub repo editing from Builder Core
- no real automatic deploy control from Builder Core
- no scheduled background research worker yet

Background work is intentionally not automatic yet because:
- the product is staying safe and honest
- research should not secretly run forever
- repo changes still need user control
- credentials are not always configured

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

## Backend Endpoints
- `GET /system/status`
- `POST /assistant/chat`
- `GET /assistant/history`
- `POST /assistant/idea`
- `POST /intelligence/plan`
- `GET /intelligence`
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`
- `POST /research/tasks`
- `GET /research/tasks`
- `GET /research/tasks/{research_id}`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `GET /memory`
- `POST /memory`
- `GET /learning`
- `POST /learning/scan`
- `GET /self-improvement`
- `POST /self-improvement`

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

### Frontend build check
```powershell
cd frontend
npm run build
```

## Deploy
- Backend and frontend remain separate Cloud Run services.
- Backend entrypoint remains `backend/app/main.py` exporting `app`.
- Frontend still uses the existing `API_BASE` logic.
- No secrets were added to the frontend.

## Legal And Safety Note
- Write original repo-specific code.
- Do not copy external copyrighted code.
- Do not add secrets into code.
- Do not fake web research.
- Do not fake background work.
- Do not claim Builder Core trained a real AI model.
- Keep the implementation simple, honest, safe, and beginner-friendly.
