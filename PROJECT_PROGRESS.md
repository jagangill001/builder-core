# Builder Core Progress Summary

This file is the quickest handoff for ChatGPT or Codex before the next Builder Core upgrade.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Latest Direction Change
Builder Core is now centered on manual Codex prompting instead of full automatic repo execution.

Main flow:
- Builder Core generates a strong Codex prompt
- user copies it into Codex
- Codex changes the repo
- user pastes Codex’s final summary back
- Builder Core saves memory and lessons

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

## What Works Now
- `POST /prompts/codex` creates a real task and a real saved prompt
- `GET /prompts/latest` returns the latest saved prompt
- `POST /tasks/{task_id}/codex-summary` stores the pasted Codex summary
- `GET /memory` returns memory, latest prompt, latest summary, and prompt history
- `GET /learning` returns lessons, known issues, recommended next steps, and project structure summary
- existing task, storage, bridge, and learning systems remain in place

## What Was Kept
- backend task storage
- project memory storage
- lesson storage
- bridge status checks
- local JSON fallback storage
- frontend/backend connection
- PWA install flow

## What Became Secondary
- automatic-feeling backend progress as the primary story
- full GitHub/Codex execution expectations
- deploy-tracking as the main user flow

## What Is Real Now
- prompt generation
- prompt storage
- task history
- Codex summary storage
- memory updates
- lesson creation
- latest summary updates

## What Is Still Manual
- copying prompt into Codex
- running Codex
- pasting Codex result back

## Storage Used Today
- Task history: `backend/runtime_data/automation_tasks.json`
- Memory and latest summary: `backend/runtime_data/project_memory.json`
- File metadata: `backend/runtime_data/storage_files.json`
- Local file fallback: `backend/runtime_data/storage_files/`

## Learning Status

### What it can do
- remember commands
- remember prompt history
- remember pasted Codex summaries
- extract likely files changed
- extract likely completed work
- extract likely remaining setup
- create a lesson
- recommend a next step

### What it cannot do
- train a custom AI model
- execute Codex automatically
- modify GitHub automatically
- guarantee perfect parsing of every Codex summary

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

## Current Honest Constraint
No real GitHub automatic execution remains enabled in the main workflow.

## Next Safe Upgrades
- improve Codex summary parsing
- add authenticated summary submission
- move prompt, memory, and lessons to Firestore
- add per-project prompt templates
- optionally automate Codex or GitHub later only after approval

## Latest Codex Work Summary
- Date/time: 2026-05-02 America/Toronto
- Folder used: `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`
- Files changed:
  - `backend/app/main.py`
  - `backend/app/prompt_builder.py`
  - `backend/app/storage.py`
  - `backend/app/learning.py`
  - `backend/app/services/task_service.py`
  - `frontend/src/app/page.tsx`
  - `README.md`
  - `COMMAND_CENTER.md`
  - `PROJECT_PROGRESS.md`
- Problem fixed:
  - Builder Core no longer needs fake full automation to be useful
  - prompt generation and summary return are now the main workflow
  - memory and learning still update after Codex finishes externally
- Current status:
  - manual Codex prompt workflow is real
  - task storage, memory, and lessons are real
  - automatic GitHub/Codex execution remains disabled as the main path
- Remaining setup required:
  - improve prompt templates over time
  - optionally add real bridge automation later
  - migrate local JSON fallback to Firestore or another persistent cloud database
