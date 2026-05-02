# Builder Core Progress Summary

This file is the quickest handoff for ChatGPT or Codex before the next Builder Core upgrade.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Current Direction
Builder Core is no longer just a prompt generator.

It now combines:
- Builder Core Assistant
- manual Codex prompt workflow
- research task storage
- project memory
- learning lessons
- self-improvement notes

Main flow:
- user chats with Builder Core
- Builder Core can save memory and ideas
- Builder Core can generate a Codex prompt
- user runs Codex manually
- user pastes Codex's final summary back
- Builder Core stores that result and creates lessons

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

## What Works Now
- `POST /assistant/chat`
- `GET /assistant/history`
- `POST /assistant/idea`
- `POST /research/tasks`
- `GET /research/tasks`
- `GET /research/tasks/{research_id}`
- `GET /self-improvement`
- `POST /self-improvement`
- `POST /prompts/codex`
- `GET /prompts/latest`
- `POST /tasks/{task_id}/codex-summary`
- `GET /memory`
- `GET /learning`

## What The Assistant Can Do Now
- chat naturally in local-first mode
- use project memory and lessons
- save useful assistant chats
- generate ideas
- create research tasks
- suggest next actions
- remind the user of system limits honestly

## What Research Tasks Can Do Now
- save topic, goal, category, sources, summary, findings, limitations, and next steps
- use memory as a source
- stay honest when web research is not connected
- create a research lesson

## What Is Real Now
- assistant chat endpoint
- assistant history endpoint
- idea generator
- research task system
- self-improvement notes
- prompt generation
- prompt history
- Codex summary save-back
- memory updates
- learning updates

## What Is Still Manual
- copying prompts into Codex
- running Codex
- reviewing actual repo changes
- pasting Codex's final summary back

## What Is Still Local / Fallback Only
- project memory storage
- assistant memory storage
- chat history storage
- research task storage
- self-improvement storage
- learning lesson storage

These still live in local JSON fallback and Cloud Run local storage is temporary.

## What Needs Google Cloud Setup Later
- Firestore for permanent task, memory, research, and lesson storage
- Google Cloud Storage for uploaded files and generated outputs
- Secret Manager for assistant or bridge secrets

## Required Environment Variables
- `STORAGE_MODE`
- `FIRESTORE_ENABLED`
- `GCP_PROJECT_ID`
- `GCS_BUCKET_NAME`
- `OPENAI_API_KEY`
- `ASSISTANT_MODE`
- `ASSISTANT_MODEL`
- `GITHUB_TOKEN`
- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_BRANCH`
- `CODEX_API_KEY`
- `CODEX_MODE`
- `FRONTEND_URL`
- `BACKEND_URL`

## Honest Limits
- no real web research yet
- no secret background work
- no real AI model training
- no real automatic GitHub editing
- no real Codex execution from the backend

## Next Recommended Step
- connect a real optional LLM path for assistant replies while keeping the local fallback
- or move memory, research tasks, and self-improvement notes from local JSON to Firestore

## Latest Codex Work Summary
- Date/time: 2026-05-02 America/Toronto
- Folder used: `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`
- Files changed:
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
- What was added:
  - Builder Core Assistant
  - assistant history
  - idea generator
  - research task system
  - self-improvement notes
  - cloud-ready storage categories
- What is working:
  - assistant chat
  - idea generation
  - research task creation
  - self-improvement notes
  - Codex prompt generation
  - Codex summary save-back
  - memory and learning refresh
- What is still local/fallback only:
  - chat history
  - assistant memory
  - research tasks
  - self-improvement notes
  - latest summary and lessons
- What needs Google Cloud setup:
  - Firestore for permanent memory
  - Google Cloud Storage for file memory later
  - optional assistant API key
- Next recommended step:
  - connect a real optional LLM path or move the new memory categories to Firestore
