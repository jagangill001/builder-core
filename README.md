# Builder Core

Builder Core is a mobile-friendly command center for planning changes, generating Codex-ready prompts, and managing the live app experience across the frontend and backend.

## Live Services
- Frontend: https://builder-core-frontend-599596796788.us-central1.run.app
- Backend: https://builder-core-599596796788.us-central1.run.app

## What The App Does
- Lets you create and choose projects.
- Sends build requests from the frontend to the backend.
- Shows backend health at the top of the dashboard.
- Generates a structured Codex prompt from the new Command Center section.
- Keeps automation in manual mode until a future authenticated workflow is added.

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

## Repo Structure
- `backend/`: FastAPI backend and builder services.
- `frontend/`: Next.js frontend and installable phone experience.
- `.github/workflows/`: CI and Cloud Run deployment workflows.
- `COMMAND_CENTER.md`: Command workflow and future automation design.

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
