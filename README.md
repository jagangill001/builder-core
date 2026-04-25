# Builder Core

Builder Core is a cloud-first AI Command Center for planning changes, generating Codex-ready tasks, tracking deployment progress, reviewing outcomes, and operating the live app experience across the frontend and backend.

## Live Services
- Frontend: https://builder-core-frontend-599596796788.us-central1.run.app
- Backend: https://builder-core-599596796788.us-central1.run.app

## What The App Does
- Accepts one instruction in a unified command bar.
- Generates a planner output and a Codex-ready task inline.
- Keeps the existing backend request flow working.
- Tracks a simulated deployment pipeline in a floating popup.
- Shows inline review suggestions after deployment.
- Supports phone installation with no App Store needed.

## Install On Your Phone
### iPhone or iPad
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
