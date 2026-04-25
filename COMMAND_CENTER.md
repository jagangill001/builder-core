# Builder Core Command Center

## What This Is
This file explains a simple workflow for using ChatGPT as the command center for Builder Core.

The idea is:
- You use ChatGPT from your phone.
- You describe what you want.
- ChatGPT turns your request into a clean Codex task.
- Codex updates this repo.
- Codex commits to `main`.
- GitHub Actions deploys the latest version.
- You test the live frontend.

## Simple Workflow
1. You open ChatGPT on your phone.
2. You describe the feature, fix, or change you want.
3. ChatGPT rewrites your idea into a clear Codex task.
4. Codex reads the repo and updates the right files.
5. Codex explains what it changed.
6. Codex runs checks if possible.
7. Codex commits the changes to `main`.
8. GitHub Actions runs and deploys the updated app.
9. You open the live frontend and test the result.

## Example Flow
You say:
- Add a better project history panel.
- Fix the frontend so it uses the deployed backend.
- Improve the dashboard for phone screens.

ChatGPT should turn that into a Codex-ready task that includes:
- the goal
- the files to inspect
- what must not break
- what to test after the change

## Rules For Codex
Codex should always follow these rules when working in this repo.

### 1. Explain the files changed
Codex must always say:
- which files were changed
- why each file changed
- what behavior changed

### 2. Do not delete working features
Codex must not remove or overwrite working features unless the task clearly requires it.

If something looks risky, Codex should keep the current behavior safe and make the smallest practical change.

### 3. Run checks when possible
Codex should run the smallest useful checks it can.

Examples:
- backend tests
- frontend build
- lint checks
- API smoke checks

If checks cannot run, Codex should say that clearly.

### 4. Give testing steps
Codex must always give beginner-friendly testing steps after making changes.

That should include:
- what URL to open
- what button or page to test
- what result should appear

### 5. Keep changes focused
Codex should avoid unrelated refactors.

If the request is about one fix, Codex should not rewrite the whole app.

## Safe Prompt Pattern For ChatGPT
When you ask ChatGPT for a repo change, include:
- the goal
- the repo name
- what is broken
- what must stay working
- what success looks like

Example:

> Repo: jagangill001/builder-core
> Goal: Improve the frontend-backend connection.
> Keep backend routes working.
> Do not redesign the UI.
> Explain files changed and give testing steps.

## What To Do After Codex Finishes
After Codex completes a change:
1. Read the summary.
2. Review the files changed.
3. Check the testing steps.
4. Wait for GitHub Actions to finish.
5. Open the live frontend.
6. Confirm the feature or fix works.

## Live Deployment Reminder
The normal path is:
- Codex updates repo
- commit goes to `main`
- GitHub Actions runs
- Cloud Run deploys latest code
- you test the live app

## Keep It Simple
If you are unsure what to ask, start with one clear instruction.

Examples:
- Fix the login page.
- Add project search.
- Improve mobile layout.
- Connect the frontend to the deployed backend.

Small clear requests are easier to implement safely.
