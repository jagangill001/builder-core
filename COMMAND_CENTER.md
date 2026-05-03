# Builder Core Command Center

## Builder Core OS Command Center
`POST /command` is now the main Builder Core OS brain surface. It still runs safety checks first, then routes to internal tools such as private search, research, market analysis, app planning, account-agent search, URL learning, crawler planning, security reporting, and agent roles.

New OS intents include:
- normal chat
- agent role request
- business planning
- market analysis
- app builder
- Codex prompt
- private search
- document ingest
- safe URL ingest
- crawler plan
- security check
- attack detection
- firewall hardening
- incident report
- account-agent search
- teaching
- legal research support
- medical information support
- finance analysis support
- engineering planning
- self-improvement
- storage status

The command response may include selected agent role, main answer, plan steps, tools used, approvals needed, security warnings, knowledge sources, confidence, limitations, memory saved, storage used, Codex prompt, and next actions.

## Approval And Permission Policy
Allowed internally:
- search memory and private index
- save memory when requested
- ingest pasted notes
- ingest one user-provided safe public URL
- create internal tasks
- generate plans, Codex prompts, and incident reports

Requires confirmation:
- email, public posting, trades, financial decisions, legal filings, medical recommendations, customer refunds, deployment, GitHub PRs, cloud changes, IP blocking, data deletion, account actions, and security-policy changes

Blocked:
- hacking, malware, credential theft, login/CAPTCHA/paywall bypass, dark web access, doxxing, hidden surveillance, private scraping, and unsafe autonomous physical control

## Security Center
Use:
- `GET /security/status`
- `GET /security/events`
- `GET /security/report`
- `GET /security/hardening`
- `GET /security/rate-limit`

The security monitor is defensive only. It logs suspicious traffic, rate limits sensitive endpoints, redacts secrets, and recommends hardening. It does not hack back or claim exact attacker identity/location.

## Account Agent
Use:
- `GET /account-agent/status`
- `POST /account-agent/search`
- `GET /connectors`

The account agent searches connected internal sources only. Gmail, Drive, YouTube transcript, and browser-session connectors are future-ready but not connected.

## Portability
The platform adapter reports cloud/local/low-memory/offline-ready signals and a degradation plan. Firestore is used only when configured; local JSON fallback remains available. Future SQLite, local model, mobile wrapper, and hardware/simulator adapters should stay behind adapter boundaries.

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

## Product Direction
Builder Core is now a one-message internal-tools command chat.

The main system does not require ChatGPT or OpenAI.

Default behavior:
- local rule-based assistant
- private search over saved knowledge
- internal research using saved documents and memory
- market-analysis framework
- app planning
- manual Codex prompt generation
- memory and lesson updates
- Firestore-ready storage

## Main User Flow
1. User opens Builder Core Command Chat.
2. User sends one message.
3. Builder Core runs:
   - safety firewall
   - command router
   - private search
   - research engine if needed
   - market analyzer if needed
   - app planner if needed
   - Codex prompt builder if needed
   - memory saver
   - learning updater
4. Builder Core returns one combined response in the same conversation.
5. If a Codex prompt is included, the user copies it into Codex manually.
6. If the user later pastes a Codex summary, Builder Core saves that result into memory and lessons.

## /command Endpoint
`POST /command`

Input:
```json
{
  "message": "Research trucking dispatch market and create an app to analyze it",
  "mode": "auto",
  "save_to_memory": true
}
```

Output includes:
- `reply`
- `detected_intents`
- `workflow`
- `internal_tools_used`
- `progress`
- `private_search`
- `research`
- `market_analysis`
- `app_plan`
- `codex_prompt`
- `summary`
- `storage_used`
- `memory_saved`
- `next_actions`
- `limitations`

## Supported Workflows
- `normal_chat`
- `research_only`
- `market_analysis`
- `app_builder`
- `research_to_app_plan`
- `codex_prompt_only`
- `save_summary`
- `cloud_storage_setup`
- `private_search`
- `document_ingest`
- `url_ingest`
- `crawler_plan`

## One-Message Market + App Workflow
Example:
- `Research trucking dispatch market and create an app to analyze it`

Builder Core can return in one response:
- clarified topic if needed
- research summary from private search and saved sources
- target users
- competitor questions
- risks and opportunities
- MVP app concept
- backend routes
- frontend screens
- storage collections
- Codex prompt
- next actions
- memory saved status
- storage used

If the exact market is missing, Builder Core stays honest and says it can start with a general market-analysis app template.

## Private Search
Builder Core private search is Builder Core’s own saved-knowledge index.

It can search:
- project memory
- assistant memory
- learning lessons
- research results
- codex summaries
- app plans
- market analysis
- user-ingested text
- safe URL-ingested public pages

It is not:
- Google scale
- DuckDuckGo scale
- live internet-wide search by default

## Document Ingest
`POST /documents/ingest-text`

Current scope:
- plain text only
- safety check first
- save original text
- chunk text
- add to private search
- save memory and lesson

Future-ready only:
- PDF parsing
- DOCX parsing
- spreadsheet parsing
- OCR

## URL Ingest Safety
`POST /search/ingest-url`

Current scope:
- one public `http` or `https` page at a time
- blocks `.onion`
- blocks `localhost`
- blocks private/internal IPs
- blocks `file://`
- does not bypass login or paywall
- does not start a multi-page crawl

If fetching is not available or fails, Builder Core returns a clear warning instead of pretending research happened.

## Crawler Planner
`POST /crawler/plan`

Current scope:
- plan only
- does not run a crawl
- explains limits
- stores the plan

Rules:
- public pages only
- respect robots.txt
- rate limit later
- no private pages
- no dark web
- no copyrighted redistribution

## Firestore Storage
The user already configured live Cloud Run environment values:
- `STORAGE_MODE=firestore`
- `FIRESTORE_ENABLED=true`
- `GCP_PROJECT_ID=project-b2c4a0ee-4467-42f1-88c`

Expected backend service account:
- `599596796788-compute@developer.gserviceaccount.com`

Required role:
- `Cloud Datastore User`

Builder Core now supports:
- Firestore primary storage through Google Application Default Credentials
- safe fallback to local JSON if Firestore import or permissions fail

Use:
- `GET /storage/status`
- `POST /storage/test`

to verify whether Firestore or fallback is active.

## Background Work Limits
Builder Core does not secretly run endless background jobs.

Current safe statuses:
- `created`
- `running`
- `completed`
- `blocked`
- `failed`

If live internet-wide research is not connected, Builder Core says:
- `Live internet-wide research is not connected yet. Builder Core can only search its own private index, saved knowledge, user notes, and safely ingested public URLs.`

Future safe background options only:
- Cloud Scheduler
- Cloud Tasks
- Pub/Sub
- Cloud Run Jobs

These are not enabled automatically.

## What Is Real Now
- unified one-message command chat
- tool registry
- model router
- safety firewall
- private search engine over saved knowledge
- document ingest
- safe URL ingest
- crawler planning
- research engine
- market analyzer
- app planner
- Firestore-ready storage abstraction

## What Is Still Local / Fallback Only
- local assistant reply generation by default
- private-search ranking
- internal research summaries when no live URL content exists
- local JSON fallback when Firestore is unavailable

## What Still Requires API Keys
- `OPENAI_API_KEY` only if the user later wants optional OpenAI mode
- `GITHUB_TOKEN` for GitHub bridge status or future automation
- `CODEX_API_KEY` for future backend-triggered Codex execution

## What Is Not Real Yet
- real automatic Codex execution
- real automatic GitHub repo editing
- full internet search engine
- uncontrolled crawler
- AI model self-training

## Local Test Commands
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

Build:
```powershell
cd "C:\Users\Jagan gill\OneDrive\Desktop\builder-core\frontend"
npm run build
```

## Deploy
- push to `main`
- let the existing GitHub Actions and Cloud Run setup deploy
- verify `/system/status`, `/storage/status`, and `/storage/test` on the live backend

## Next Recommended Step
After this upgrade, the clean next step is to verify Firestore on the live backend and then decide between:
- improving evidence display and private-search ranking
- enabling an optional local model endpoint while keeping local rule-based fallback

## Admin Authentication
Internal dashboard routes now require `X-Admin-Key` when `ADMIN_API_KEY` is configured.

Set it in Cloud Run:
1. Cloud Run
2. `builder-core`
3. Edit & deploy new revision
4. Variables & Secrets
5. Add `ADMIN_API_KEY=your-long-random-admin-key`
6. Deploy

The key is never hardcoded, never returned by status endpoints, never stored in Firestore, and never placed in frontend source. The frontend Admin Access panel stores the key only in browser `localStorage` after the admin enters it.

Protected internal routes:
- `/security/events`
- `/security/report`
- `/security/hardening`
- `/approvals`
- `/agents/tasks`
- `/agent/history`
- `/account-agent/status`
- `/account-agent/search`
- `/connectors`
- `/memory`
- `/learning`
- `/self-improvement`
- `/storage/test`
- `/knowledge/seed`
- `/knowledge/scan-project`
- `/tools`

## System-Safety Routing
The main `/command` workflow now routes defensive security and system-safety questions to `security_check` instead of `normal_chat`.

Examples:
- `Check Builder Core security and tell me if the system is protected`
- `Protect Builder Core`
- `Show security status`
- `Harden system`
- `Show incident report`

The response includes monitor status, rate-limit status, event count, highest severity, defensive recommendations, hardening checklist summaries, and a no-retaliation disclaimer.

## Safe Authorized Defensive Checks
Only run these against your own Builder Core backend:

```powershell
curl.exe -sS https://builder-core-599596796788.us-central1.run.app/security/status
curl.exe -H "X-Admin-Key: YOUR_ADMIN_KEY" -sS https://builder-core-599596796788.us-central1.run.app/security/report
curl.exe -H "X-Admin-Key: YOUR_ADMIN_KEY" -sS https://builder-core-599596796788.us-central1.run.app/security/events
curl.exe -i https://builder-core-599596796788.us-central1.run.app/.env
```

These are defensive logging and reporting checks. They do not scan third parties, exploit vulnerabilities, bypass protections, or retaliate.

## Knowledge Feeding System
Builder Core can now accept knowledge from manual notes, pasted text, safe public URLs provided by the user, seed packs, and safe project file summaries.

Endpoints:
- `POST /knowledge/add`
- `GET /knowledge`
- `GET /knowledge/{knowledge_id}`
- `POST /knowledge/search`
- `GET /knowledge/status`
- `POST /knowledge/seed` with admin key
- `POST /knowledge/scan-project` with admin key

Seed packs:
- Builder Core OS Architecture
- Safe Defensive System
- AI Agent System
- Business and Market Analysis
- App Building Workflow
- Teaching and Study System
- Trucking Business Knowledge Starter
- Legal, Medical, and Finance Safety Limits

## One-Chat Knowledge Workflows
The main chat can now handle:
- `Remember this: ...`
- `Learn this: ...`
- `Add this to knowledge: ...`
- `Search your knowledge for ...`
- `What do you know about ...`
- `Learn this URL https://example.com`

URL learning fetches one user-provided public page only. It blocks localhost, private IPs, `.onion`, and non-http/https schemes. It does not bypass login, CAPTCHA, paywalls, or site rules.

## No Fake Knowledge Policy
Builder Core answers from saved/internal knowledge, seed packs, user notes, and safely ingested URLs. Confidence is low, medium, or high based on saved source strength. It does not claim internet-wide knowledge and does not train a model.
