# Builder Core Command Center

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Product Direction
Builder Core is now a manual Codex Prompt Command Center.

That means:
- Builder Core generates the Codex prompt
- the user copies it into Codex manually
- Codex performs the repo work
- the user pastes Codex’s final summary back into Builder Core
- Builder Core stores memory and learning from that result

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

## Main Workflow
1. User enters one command.
2. Frontend calls `POST /prompts/codex`.
3. Backend creates a real task and generates a Codex prompt.
4. Frontend shows the prompt and task ID.
5. User copies the prompt into Codex manually.
6. Codex makes the repo changes outside Builder Core.
7. User pastes Codex’s final summary back into Builder Core.
8. Frontend calls `POST /tasks/{task_id}/codex-summary`.
9. Backend saves the summary, updates memory, creates a lesson, and updates the latest summary.

## Why This Mode Is Better Right Now
- safer than pretending the backend already controls GitHub and Codex
- easy to verify
- easy to explain
- still builds real project memory and lessons

## What Was Kept
- backend task storage
- task history
- bridge status
- memory storage
- learning storage
- latest summary storage
- project structure scan

## What Became Secondary
- automatic-style backend task runner stages
- bridge-execution expectations
- deploy-check style progress as the main product story

Those systems still exist, but the main user workflow is now prompt generation plus manual Codex handoff.

## Prompt Content
The generated prompt now includes:
- project name
- repo URL
- main folders
- main files
- user command
- recent memory
- recent lessons
- known issues
- legal and safety rules
- testing instructions
- documentation update instructions
- final summary requirements

## New Endpoints
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`

## What Is Real Now
- real prompt generation
- real task ID creation
- real prompt storage
- real Codex summary storage
- real memory updates
- real lesson creation
- real latest summary updates

## What Is Still Manual
- user copies the prompt into Codex
- user runs Codex
- user pastes the Codex result back

## What May Be Automated Later
- automatic Codex execution after approval
- automatic GitHub write actions
- automatic deployment tracking from real credentials
- Firestore as the default task and memory store

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

## Deploy
- Backend and frontend remain separate Cloud Run services.
- Frontend still calls backend using `API_BASE`.
- No frontend secrets are introduced.

## Important Honesty Rule
Builder Core does not claim to edit GitHub automatically in this workflow.

If a real repo change depends on missing credentials or a missing executor, Builder Core must stay honest and say so.
