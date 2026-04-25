# Builder Core Command Center

## Purpose
Builder Core is becoming a single unified AI Command Center for phone and desktop use.

The goal is one place where the user can type an instruction, see the planner output, prepare the Codex task, track deployment progress, review the result, and refresh the app without hopping across multiple sections.

## Current Workflow
User -> Command Center -> Planner -> Codex task -> Builder Core backend -> Manual pipeline -> Deploy review

1. The user enters an instruction in one command bar.
2. Builder Core generates the planner output inline.
3. Builder Core generates the Codex-ready task inline.
4. Builder Core still sends the same instruction through the existing backend request flow.
5. The automation popup simulates the delivery pipeline.
6. Review notes appear inline after the deploy step.
7. The app auto-refreshes when the simulated deploy completes.

## Future Workflow
User -> Command Center -> Backend task -> Auto Codex -> GitHub -> Deploy -> Status polling -> App refresh

Future automation should work like this:
1. The user enters a task directly in Builder Core.
2. The backend creates the task record.
3. After confirmation and authentication, Builder Core triggers Codex automatically.
4. GitHub receives the change request.
5. GitHub Actions deploys after checks pass.
6. The frontend polls task and deploy status.
7. The UI updates automatically and refreshes when the release is live.

## Cloud-First Storage Plan
Builder Core is designed to move toward cloud-first storage.

### Firestore
- commands
- tasks
- statuses
- history

### Cloud Storage
- files
- generated outputs

### Secret Manager
- API keys

### Cloud Run
- backend
- frontend

### GitHub
- code

Important note:
- The laptop is a control device only, not storage.

## Future Backend Endpoints
Planned backend automation endpoints:
- `POST /automation/tasks`
- `GET /automation/tasks/{id}`
- `GET /automation/history`

Planned storage endpoints:
- `POST /storage/files`
- `GET /storage/files`

## Automation Pipeline
The unified app now shows a visual automation pipeline with these stages:
1. Task Received
2. Planning
3. Codex Ready
4. Codex Working
5. GitHub Deploying
6. Cloud Run Live
7. App Refreshed

### Current Manual Simulation
For now, the pipeline is still manual and safe:
- `Run Command` prepares the planner output and Codex task.
- `Send to Codex` moves the task into Codex Working.
- `Mark Codex Done` moves the task into GitHub Deploying.
- `Mark Deploy Done` marks Cloud Run Live and starts the refresh countdown.
- `Refresh Now` forces the final refresh step immediately.

### Future Automation Sources
Later, these steps can update automatically from:
- Codex task status
- GitHub Actions status
- Cloud Run deploy status
- backend webhook events

## Approval, Auth, And Logs
- Authentication is required before automation can act.
- Approval is required before any automatic repo change.
- Logs are required for every automated action.

## Legal And Originality Rules
- Prefer original repo-specific implementations.
- Do not paste recognizable third-party snippets.
- Keep the code easy to read and easy to review.
- Use licensed frameworks such as Next.js, React, and FastAPI in a normal supported way.
- Keep the project safe for commercial use by avoiding unknown copyrighted code.
