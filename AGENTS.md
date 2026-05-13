# Builder Core Repo Guide

## Scope
- Work only inside this `builder-core` repo unless a task explicitly says otherwise.
- Keep backend and frontend deployable as separate Cloud Run services.

## Architecture Invariants
- Backend entrypoint stays `backend/app/main.py` exporting `app`.
- Backend Cloud Run startup stays `backend/Procfile` with `uvicorn app.main:app --host 0.0.0.0 --port 8080`.
- Frontend stays a separate Next.js service with `npm start` running on port `8080`.
- Frontend API calls must use `NEXT_PUBLIC_API_URL`; do not hardcode deployed or local API hosts except for a guarded local fallback.
- Current orchestration lives under `backend/app/api`, `backend/app/core`, `backend/app/bees`, `backend/app/memory`, and `backend/app/services`. Extend those layers before adding parallel patterns elsewhere.
- Treat `backend/generated/` as user or system output. Do not rewrite or delete generated project folders unless the task specifically requires it.

## Change Strategy
- Prefer additive helpers and service-layer extensions over large rewrites.
- Preserve existing routes and response schemas unless the task is explicitly about changing them.
- Keep Cloud Run source deployment compatibility. Do not add Docker unless there is a clear blocker.
- When changing deployment behavior, explain backend and frontend impact separately.

## Ownership And Originality Rules
- Prefer fresh, repo-specific implementations over generic boilerplate.
- Do not paste recognizable code from third-party repos, tutorials, or boilerplates.
- Refactor generic-looking code into the current house style when touching it.
- Include a short originality review for each major change in the final handoff.
- Flag any file that still looks template-derived or high-risk after the change.
- Keep dependencies minimal and call out any license review that may be needed.

## Codex Workflow
- Prefer feature branches such as `codex/<task-name>` and open a pull request into `main`.
- Do not bypass CI for routine changes.
- When the Codex bridge is in use, submit work through the GitHub issue or PR flow and keep `main` review-only.
- Run the narrowest relevant checks before finishing work:
  - Backend: `python -m compileall app`
  - Backend: `python -m unittest discover -s tests -v`
  - Frontend: `npm run lint`
  - Frontend: `npm run build`
- If a task changes deploy or runtime config, update the workflow or instructions in the same change.

## Secrets And Safety
- Never commit credentials, `.env.local`, service-account keys, or generated auth files.
- Prefer GitHub OIDC plus Google Workload Identity Federation over long-lived keys.
- Keep deployment automation branch-first: validate in CI, merge to `main`, then deploy from `main`.
