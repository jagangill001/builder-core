# Builder Core

Builder Core is a cloud-first AI command center for planning changes, generating Codex-ready tasks, tracking progress stage by stage, reviewing outcomes, and operating the live app from phone or desktop.

## Live Services
- Frontend: https://builder-core-frontend-599596796788.us-central1.run.app
- Backend: https://builder-core-599596796788.us-central1.run.app

## What The App Does
- Accepts one instruction in the Command tab.
- Calls the backend `/chat` route and shows the assistant reply inline.
- Generates planner output and a Codex-ready task in the same conversation flow.
- Runs a compact stage bar that moves one stage at a time with a single `Next` button.
- Shows review guidance after a task completes.
- Supports phone installation with no App Store needed.

## Simplified Task Progress
Builder Core now uses a simple stage-by-stage task system.

### Stages
1. Planning
2. Codex Working
3. GitHub Deploying
4. Cloud Run Live
5. App Refreshed

### How it works
- A task starts in `Planning` at `1%`.
- The current stage automatically advances to `100%`.
- When it reaches `100%`, Builder Core pauses and tells the user to press `Next`.
- Pressing `Next` starts the next stage at `1%`.
- The final stage ends with `Done - ready for next task`.

## Install On Your Phone
### iPhone Or iPad
1. Open the frontend URL in Safari.
2. Tap the Share button.
3. Tap Add to Home Screen.
4. Open Builder Core from your home screen.

### Android
1. Open the frontend URL in Chrome.
2. Open the browser menu.
3. Tap Install app or Add to Home screen.
4. Open Builder Core from the installed icon.

## Cloud-First Plan
Builder Core is moving toward cloud-first storage and automation.

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
These are documented for the next automation phase and are not implemented yet.

### Automation
- `POST /automation/tasks`
- `GET /automation/tasks/{id}`
- `GET /automation/history`

### Storage
- `POST /storage/files`
- `GET /storage/files`

## Deployment Notes
- Backend is deployed separately to Cloud Run.
- Frontend is deployed separately to Cloud Run.
- The frontend uses `NEXT_PUBLIC_API_BASE_URL` or `NEXT_PUBLIC_API_URL` and falls back to the deployed backend URL.

## Legal And Originality Note
This project is intended to use original, repo-specific code plus licensed open-source libraries such as Next.js, React, and FastAPI.

When adding new features:
- Prefer fresh implementations over copied snippets.
- Avoid unknown copyrighted code.
- Refactor generic patterns into the repo's own structure.
- Keep changes readable, safe, and suitable for commercial use.

## License
This project is released under the MIT License. See `LICENSE` for details.
