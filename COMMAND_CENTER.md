# Builder Core Command Center

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Product Direction
Builder Core is now a manual Codex Prompt Command Center with an Intelligence Center.

That means:
- Builder Core structures the task safely
- Builder Core generates the Codex prompt
- the user copies the prompt into Codex manually
- Codex performs the repo work
- the user pastes Codex's final summary back into Builder Core
- Builder Core stores memory, lessons, and the latest outcome

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

## Main Workflow
1. User enters one command.
2. Frontend calls `POST /prompts/codex`.
3. Backend builds an intelligence brief and a manual Codex prompt.
4. Frontend shows:
   - intelligence mode
   - safety firewall
   - research steps
   - evidence checklist
   - generated Codex prompt
5. User copies the prompt into Codex manually.
6. User runs Codex outside Builder Core.
7. User pastes Codex's final summary back into Builder Core.
8. Frontend calls `POST /tasks/{task_id}/codex-summary`.
9. Backend updates task history, memory, intelligence history, latest summary, and lessons.

## Intelligence Center Modes
- Safe Research
- Law and Policy Planning
- Market Analysis
- Exam Planning
- Forecasting
- Language Learning
- Video Transcript Learning
- Self-Improvement Memory

## What The Intelligence Center Does
- detects the most likely planning mode from the command
- creates a safe research and action structure
- adds a safety firewall
- prepares better context for the Codex prompt
- remembers what kind of work the user is doing

## Safety Firewall Rules
- do not invent facts, citations, legal conclusions, or market numbers
- do not claim Builder Core replaced a lawyer, analyst, teacher, or expert
- separate assumptions from verified evidence
- label manual verification steps clearly
- stay honest about missing information

## What Was Kept
- backend task storage
- task history
- bridge status
- project memory storage
- lesson storage
- latest summary storage
- local JSON fallback storage
- frontend/backend connection
- PWA install flow

## What Became Secondary
- automatic-style GitHub/Codex execution as the main story
- fake-seeming deployment progress as the main UI flow

These systems can stay in the codebase, but the main workflow is now manual Codex handoff plus saved intelligence, memory, and learning.

## What Is Real Now
- real intelligence brief generation
- real prompt generation
- real task creation
- real prompt history
- real intelligence history
- real manual summary save-back
- real memory updates
- real lesson creation

## What Is Still Manual
- copying prompt into Codex
- running Codex
- reviewing repo changes
- pasting the final summary back

## What May Be Automated Later
- authenticated Codex execution after approval
- authenticated GitHub write actions
- automatic deployment tracking from real credentials
- Firestore as the default task, memory, and intelligence store

## New Endpoints
- `POST /intelligence/plan`
- `GET /intelligence`
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`

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

If real repo work depends on missing credentials or a missing executor, Builder Core must stay honest and say so.
