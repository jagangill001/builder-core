# Builder Core Command Center

## Purpose
Builder Core is a cloud-first AI command center for phone and desktop use.

The goal is one place where the user can submit a request, see the planner output, review the Codex-ready task, track progress stage by stage, review the result, and move toward safe automation without depending on laptop storage.

## Current Workflow
User -> Command Center -> Backend chat -> Planner -> Codex task -> Stage bar -> GitHub tracking -> Review

1. The user enters one instruction in the Command tab.
2. Builder Core calls the backend `/chat` route.
3. The app shows the assistant reply, planner output, and Codex-ready prompt inline.
4. The compact task bar starts the progress flow at Planning.
5. The Progress tab also reads live GitHub repo and workflow status from `GET /github/status`.
6. Each stage advances from 1% to 100%.
7. When a stage completes, Builder Core pauses and waits for the user to press `Next`.
8. After the final stage, review guidance and next-upgrade ideas stay visible in the app.

## Simplified Task Bar
The old multi-button pipeline has been replaced with one compact task bar.

### What the task bar shows
- current task name
- current stage name
- stage progress percent
- progress bar
- one `Next` button

### Stages
1. Planning
2. Codex Working
3. GitHub Deploying
4. Cloud Run Live
5. App Refreshed

### How it works
- When a task starts, `Planning` begins at `1%`.
- The current stage automatically progresses to `100%`.
- When a stage reaches `100%`, Builder Core shows a completion message and waits.
- The user presses `Next` to move to the next stage.
- The next stage resets to `1%`.
- The final stage ends with `Done - ready for next task`.

## Approval And Permission
- Automation permission granted by user is shown in the app.
- Future: Codex will run automatically after approval.
- No real automatic repo modification happens yet.

## GitHub Tracking
Builder Core now includes a lightweight GitHub tracking layer for the current public repo.

### What it shows
- latest tracked commit
- latest `Repo Checks` workflow state
- latest `Deploy Cloud Run` workflow state
- current summary
- next suggested action

### Backend endpoint
- `GET /github/status`

### Configuration
- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_DEFAULT_BRANCH`
- `GITHUB_STATUS_TOKEN` for higher GitHub API limits
- `GITHUB_CHECKS_WORKFLOW_NAME`
- `GITHUB_DEPLOY_WORKFLOW_NAME`

## Future Workflow
User -> Builder Core -> Backend task -> Auto Codex -> GitHub -> Deploy -> Status polling -> App refresh

Future automation should work like this:
1. The user enters a task directly in Builder Core.
2. The backend creates a persistent cloud task record.
3. After approval and authentication, Builder Core triggers Codex automatically.
4. GitHub receives the change request.
5. GitHub Actions deploys after checks pass.
6. The app polls task and deploy status from the backend.
7. The UI updates automatically and the live app refreshes when the release is ready.

## Cloud-First Storage Plan
Builder Core is moving toward cloud-first storage and execution.

### Firestore
- tasks
- commands
- progress
- history

### Cloud Storage
- generated files
- uploads

### Secret Manager
- API keys

### Cloud Run
- backend
- frontend

### GitHub
- code source

Important note:
- Laptop is only control device. All data will live in cloud.

## Future Backend Endpoints
These endpoints are planned but not implemented yet:

### Automation
- `POST /automation/tasks`
- `GET /automation/tasks/{id}`
- `GET /automation/history`

### Storage
- `POST /storage/files`
- `GET /storage/files`

## App Navigation
Builder Core keeps app-style navigation so the main areas stay easy to reach on phone or desktop.

### Tabs
- `Command`: chat with Builder Core and submit the next request
- `Progress`: follow the compact stage bar and one-button flow
- `Review`: confirm the latest task result and safe next steps
- `Download`: install the app on your phone or copy the live link
- `Help`: get quick guidance when you are unsure what to do next

## Logs, Auth, And Safety
- Authentication is required before future automation can act.
- Approval is required before automatic repo changes happen.
- Logs are required for every automated action.
- Codex should explain files changed, run checks when possible, and provide testing steps.

## Legal And Originality Rules
- Prefer original repo-specific implementations.
- Do not paste recognizable third-party snippets.
- Keep the code easy to read and easy to review.
- Use licensed frameworks such as Next.js, React, and FastAPI in a normal supported way.
- Keep the project safe for commercial use by avoiding unknown copyrighted code.
