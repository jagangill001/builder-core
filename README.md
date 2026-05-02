# Builder Core

Builder Core is now a unified internal-tools command chat for planning, private search, research, market analysis, app planning, manual Codex prompt building, memory, learning, and cloud-ready storage.

## Repo Folder Used
- `C:\Users\Jagan gill\OneDrive\Desktop\builder-core`

## Files Changed In This Upgrade
- `backend/app/main.py`
- `backend/app/storage.py`
- `backend/app/services/task_service.py`
- `backend/app/chat_assistant.py`
- `backend/app/prompt_builder.py`
- `backend/app/model_router.py`
- `backend/app/safety.py`
- `backend/app/tool_registry.py`
- `backend/app/private_search.py`
- `backend/app/document_ingest.py`
- `backend/app/web_ingest.py`
- `backend/app/crawler_plan.py`
- `backend/app/research_engine.py`
- `backend/app/market_analyzer.py`
- `backend/app/app_planner.py`
- `backend/app/command_router.py`
- `backend/app/orchestrator.py`
- `backend/.env.example`
- `frontend/src/app/page.tsx`
- `README.md`
- `COMMAND_CENTER.md`
- `PROJECT_PROGRESS.md`

## What Changed
- Added a unified `POST /command` workflow that uses Builder Core internal tools in one backend response.
- Reworked storage so local JSON and Firestore share one generic record layer.
- Added `/storage/status` and `/storage/test`.
- Added a tool registry, model router, safety firewall, private search, document ingest, URL ingest, crawler planner, research engine, market analyzer, and app planner.
- Replaced the old multi-section main page with one command/chat interface plus collapsed advanced panels.

## Unified Command Chat
The main frontend now uses one message box.

Example:
- `Research trucking dispatch market and create an app to analyze it`

Builder Core can now respond in one message with:
- main reply
- detected workflow
- progress steps
- internal tools used
- private search results
- research result
- market analysis
- app plan
- Codex prompt
- summary
- memory saved status
- storage used
- limitations
- next actions

## Internal Tools
Builder Core now has these built-in modules:
- `assistant_chat`
- `command_router`
- `private_search`
- `document_ingest`
- `safe_url_ingest`
- `research_engine`
- `market_analyzer`
- `app_planner`
- `codex_prompt_builder`
- `memory_manager`
- `learning_engine`
- `self_improvement`
- `storage_manager`
- `safety_firewall`
- `model_router`
- `crawler_planner`

## Firestore Storage
Builder Core now supports:
- `STORAGE_MODE=firestore`
- `FIRESTORE_ENABLED=true`
- `GCP_PROJECT_ID=project-b2c4a0ee-4467-42f1-88c`

Expected Cloud Run service account:
- `599596796788-compute@developer.gserviceaccount.com`

Required role:
- `Cloud Datastore User`

When Firestore is enabled and permissions work:
- Builder Core uses Google Application Default Credentials from Cloud Run
- records are stored in Firestore collections
- local JSON fallback stays available if Firestore fails

When Firestore cannot initialize or permissions fail:
- Builder Core records a warning
- Builder Core falls back safely to local JSON if possible
- Builder Core does not crash

## What /storage/status Returns
`GET /storage/status` returns:
- `storage_mode`
- `storage_backend`
- `storage_message`
- `firestore_enabled`
- `gcp_project_id`
- `gcs_bucket_name`
- `using_firestore`
- `using_fallback`
- `warnings`
- `collections`
- record counts for memory, lessons, research, and private-search data
- `checked_at`

## What /storage/test Returns
`POST /storage/test`:
1. saves a test record
2. reads it back
3. reports whether Firestore or local storage was used

It returns:
- `ok`
- `storage_used`
- `record_id`
- `saved`
- `read_back`
- `warnings`

If Firestore is enabled but permission is missing, Builder Core returns a clear warning:
- `Firestore is enabled but the Cloud Run service account does not have permission. Add Cloud Datastore User role.`

## Collections Used
- `tasks`
- `command_history`
- `chat_history`
- `assistant_memory`
- `project_memory`
- `research_tasks`
- `research_results`
- `codex_prompts`
- `codex_summaries`
- `learning_lessons`
- `self_improvement`
- `app_plans`
- `market_analysis`
- `storage_tests`
- `search_documents`
- `search_chunks`
- `search_queries`
- `knowledge_base`
- `tool_registry`
- `document_ingest`
- `url_ingest_records`
- `crawler_plans`

## What Works Without Outside AI/Search APIs
- local rule-based assistant replies
- command routing
- private search over saved knowledge
- saved document indexing
- safe one-page URL ingest
- internal research over saved sources
- market-analysis structure
- app planning
- manual Codex prompt generation
- memory, lessons, and self-improvement notes

## What Still Uses Local / Rule-Based Logic
- assistant chat fallback brain
- command routing
- private search ranking
- market-analysis framework
- app planning
- research summaries from saved knowledge

OpenAI is optional only.

## What Is Real Now
- `/command`
- `/tools`
- `/assistant/model-status`
- `/search/status`
- `/search/add`
- `/search/query`
- `/search/rebuild`
- `/documents/ingest-text`
- `/search/ingest-url`
- `/crawler/plan`
- `/storage/status`
- `/storage/test`
- `/assistant/chat`
- `/prompts/codex`
- `/research/tasks`
- `/memory`
- `/learning`
- `/self-improvement`

## What Is Not Automatic Yet
- no automatic GitHub repo editing
- no automatic Codex execution
- no automatic deployment control
- no automatic internet-wide research
- no uncontrolled background crawler

## What Is Not Real Yet
- Builder Core private search is not Google/DuckDuckGo scale
- live internet-wide research is not connected by default
- the assistant is not a trained new AI model
- background research is not secretly running

## Safety Limits
Builder Core blocks:
- hacking
- malware
- stealing data
- bypassing passwords
- dark web access
- doxxing
- illegal surveillance
- paywall bypass
- fake evidence
- dangerous instructions
- guaranteed legal, financial, or political outcomes

## Local Storage Limits
If `STORAGE_MODE=local`, Builder Core stores data in:
- `backend/runtime_data/project_memory.json`
- `backend/runtime_data/automation_tasks.json`
- `backend/runtime_data/storage_files.json`

Cloud Run local storage is temporary.

For permanent storage later, move the same categories to:
- Firestore
- Cloud SQL
- Supabase
- another persistent hosted database

## Difference Between Learning And AI Training
Builder Core learning means:
- saving memory
- saving lessons
- saving research results
- saving summaries
- improving future prompts from saved project history

It does not mean:
- training a new foundation model
- secretly browsing the web forever
- inventing new knowledge without stored sources

## Required Environment Variables
- `STORAGE_MODE=local`
- `FIRESTORE_ENABLED=false`
- `GCP_PROJECT_ID=`
- `GCS_BUCKET_NAME=`
- `GOOGLE_APPLICATION_CREDENTIALS=`
- `ASSISTANT_MODE=local`
- `LOCAL_MODEL_PROVIDER=disabled`
- `LOCAL_MODEL_ENDPOINT=`
- `LOCAL_MODEL_NAME=`
- `OPENAI_API_KEY=`
- `GITHUB_TOKEN=`
- `GITHUB_OWNER=jagangill001`
- `GITHUB_REPO=jagangill001/builder-core`
- `GITHUB_BRANCH=main`
- `CODEX_API_KEY=`
- `CODEX_MODE=disabled`
- `FRONTEND_URL=https://builder-core-frontend-599596796788.us-central1.run.app`
- `BACKEND_URL=https://builder-core-599596796788.us-central1.run.app`

## Run Locally
Backend:
```powershell
cd "C:\Users\Jagan gill\OneDrive\Desktop\builder-core\backend"
uvicorn app.main:app --reload
```

Frontend:
```powershell
cd "C:\Users\Jagan gill\OneDrive\Desktop\builder-core\frontend"
npm install
npm run dev
```

Frontend production build:
```powershell
cd "C:\Users\Jagan gill\OneDrive\Desktop\builder-core\frontend"
npm run build
```

Backend import check:
```powershell
cd "C:\Users\Jagan gill\OneDrive\Desktop\builder-core\backend"
$env:PYTHONDONTWRITEBYTECODE='1'
& '.\venv\Scripts\python.exe' -c "from app.main import app; print('backend import ok', len(app.routes))"
```

## Deploy
- Push to `main`
- let the existing GitHub Actions and Cloud Run flow deploy backend and frontend
- verify live backend with `/system/status`
- verify live storage with `/storage/status` and `/storage/test`

## Next Recommended Step
Verify Firestore from the live Cloud Run backend by calling `/storage/status` and `/storage/test`, then decide whether the next upgrade should be:
- richer private-search ranking and evidence display
- optional local model integration
- safer scheduled background jobs with Cloud Scheduler, Cloud Tasks, Pub/Sub, or Cloud Run Jobs
