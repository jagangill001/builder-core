# Builder Core

Builder Core is now a unified internal-tools command chat for planning, private search, research, market analysis, app planning, manual Codex prompt building, memory, learning, and cloud-ready storage.

## Builder Core OS Vision
Builder Core is growing into Builder Core OS: a local-first internal agent platform and virtual company operating system. The current system is a foundation-stage OS layer, not AGI, not human consciousness, and not a trained chatbot. It uses internal tools, private search, memory, safe URL learning, defensive security monitoring, agent roles, approvals, and storage adapters.

The architecture is intentionally layered:
- plain Python core logic where possible
- storage behind local JSON and Firestore adapters
- model access behind the model router
- runtime detection behind the platform adapter
- URL learning behind safe ingest modules
- high-risk actions behind permission and approval checks

## Builder Core OS Framework
Current backend OS endpoints:
- `GET /os/status`
- `GET /platform/status`
- `GET /agents/roles`
- `GET /agents/roles/{agent_id}`
- `POST /agents/tasks`
- `GET /agents/tasks`
- `GET /approvals`
- `POST /approvals/request`
- `GET /security/status`
- `GET /security/events`
- `GET /security/report`
- `GET /security/hardening`
- `GET /account-agent/status`
- `POST /account-agent/search`
- `GET /connectors`
- `POST /agent/run`
- `GET /agent/status`
- `GET /agent/history`
- `POST /agent/learn-url`
- `POST /agent/crawl-plan`

## Portability Roadmap
Builder Core OS does not claim to run on every old or future machine today. The roadmap is graceful degradation:
1. Cloud Run plus Firestore
2. Local server mode
3. SQLite or local file mode
4. Android-ready wrapper
5. Low-memory mode
6. Local model adapter
7. Hardware or simulator adapters
8. Certified real-world integrations only after safety and legal review

## Agent Roles And Approvals
Virtual employee roles now include CEO, operations, research, developer, market, sales, support, teacher, cybersecurity, finance/trading analyst, legal research assistant, medical info assistant, engineering planner, firewall defense, incident response, and simulation safety. Medical, legal, trading, vehicle, aircraft, defense, customer-payment, deployment, account, and external cybersecurity actions are decision-support only unless the approval system allows a specific safe action.

Blocked by default:
- malware
- credential theft
- hack-back
- offensive exploitation
- private scraping
- dark web access
- paywall/login/CAPTCHA bypass
- doxxing
- autonomous weapon, vehicle, aircraft, live-trading, or medical-treatment control

## Defensive Security
The defensive security monitor logs suspicious paths, injection-looking query strings, suspicious user agents, high-severity secret/config probing, repeated errors, and rate-limit events. It redacts sensitive headers and stores events in `security_events`.

IP metadata is limited. Builder Core records the best available client IP from `X-Forwarded-For`, `X-Real-IP`, `Forwarded`, or the request client host. Header IPs can be spoofed unless a trusted proxy configuration is enforced. Geo lookup is not configured, so location is not exact and does not identify a person.

## Account Agent And Connectors
The account agent is read-only first. It can search connected internal sources now:
- Firestore/local memory
- private search
- uploaded or pasted documents
- safe URL ingest records

Future-ready only:
- Google Drive
- Gmail
- YouTube transcript
- browser session

These future connectors are not faked and do not ask for passwords.

## No-API Learning
Builder Core can learn from one user-provided safe public URL at a time through `POST /agent/learn-url`. It blocks localhost, private IPs, `.onion`, non-http schemes, login/paywall bypass, and uncontrolled crawling. The mini crawler endpoint creates a plan only.

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

## Admin Authentication
Builder Core protects internal dashboard endpoints with an admin key.

- Environment variable: `ADMIN_API_KEY`
- Request header: `X-Admin-Key`
- Do not commit a real key.
- Do not put the key in frontend source code.
- The frontend only stores a manually entered key in browser `localStorage`.

Cloud Run setup:
1. Open Cloud Run.
2. Select `builder-core`.
3. Choose Edit & deploy new revision.
4. Open Variables & Secrets.
5. Add `ADMIN_API_KEY=your-long-random-admin-key`.
6. Deploy the revision.

Protected endpoints include `/security/events`, `/security/report`, `/security/hardening`, `/approvals`, `/agents/tasks`, `/agent/history`, `/account-agent/status`, `/account-agent/search`, `/connectors`, `/memory`, `/learning`, `/self-improvement`, `/storage/test`, `/knowledge/seed`, `/knowledge/scan-project`, and `/tools`.

Public safe endpoints include `/system/status`, `/os/status`, `/platform/status`, `/security/status`, and `/storage/status`. They expose status only and never reveal the admin key.

## System-Safety Routing Fix
The `/command` brain now recognizes system-safety and defensive security questions such as:

- `check security`
- `protect Builder Core`
- `system safety`
- `security status`
- `security report`
- `harden system`
- `firewall`
- `rate limiter`
- `incident report`

Security workflows return a defensive status object with monitor state, rate limiter state, event counts, highest severity, hardening summaries, recommendations, and this limit: IP/location data is approximate and does not identify a person. Builder Core does not retaliate.

## Safe Authorized Defensive Checks
Run these only against your own Builder Core backend:

```powershell
curl.exe -sS https://builder-core-599596796788.us-central1.run.app/security/status
curl.exe -H "X-Admin-Key: YOUR_ADMIN_KEY" -sS https://builder-core-599596796788.us-central1.run.app/security/report
curl.exe -H "X-Admin-Key: YOUR_ADMIN_KEY" -sS https://builder-core-599596796788.us-central1.run.app/security/events
curl.exe -i https://builder-core-599596796788.us-central1.run.app/.env
```

These checks do not test third-party targets, exploit vulnerabilities, bypass protections, or retaliate. The suspicious-path check only verifies defensive logging on your own backend.

## Knowledge Feeding System
Builder Core can now save and search knowledge entries from:

- manual notes
- pasted text
- safe one-page public URLs provided by the user
- seed packs
- safe project file summaries
- agent results and future research summaries

Knowledge endpoints:
- `POST /knowledge/add`
- `GET /knowledge`
- `GET /knowledge/{knowledge_id}`
- `POST /knowledge/search`
- `GET /knowledge/status`
- `POST /knowledge/seed` with admin key
- `POST /knowledge/scan-project` with admin key

Seed packs cover Builder Core OS architecture, defensive security, agents, business and market analysis, app building, teaching, trucking business basics, and high-risk safety limits.

## One-Chat Learning
The main chat now understands:

- `Remember this: ...`
- `Learn this: ...`
- `Add this to knowledge: ...`
- `Search your knowledge for ...`
- `What do you know about ...`
- `Learn this URL https://example.com`

This is knowledge-base learning only. It saves records to Firestore or local fallback, indexes them into private search, and uses them in future answers. It is not model training and it does not create internet-wide knowledge.

## Agent Answer Quality
Agent answers now include goal, selected role, what was checked, analysis, plan, risks and limitations, missing knowledge, tools used, next actions, memory saved status, and approval status. Specialized roles add their own structure, such as CEO 7-day plans, research evidence gaps, developer files/tests, defensive security recommendations, teaching practice tasks, and finance/legal/medical disclaimers.

## Knowledge Confidence
Builder Core reports confidence as:

- `low` when no saved source or only weak notes exist
- `medium` when saved notes or seed entries support the answer
- `high` when multiple clear saved sources support the answer

If confidence is low or medium, add more notes or safe public URLs. Builder Core does not fake missing knowledge.
