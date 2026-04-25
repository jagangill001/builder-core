# Builder Core Command Center

## Purpose
Builder Core is moving toward a simple command center model.

Today you can use ChatGPT from your phone, generate a clean Codex prompt, update the repo, and deploy through GitHub Actions.

## Current Workflow
User -> ChatGPT -> Codex prompt -> GitHub -> Deploy

1. You give an idea or instruction in ChatGPT.
2. ChatGPT turns that request into a clean Codex task.
3. Codex inspects the repo and applies the change.
4. Codex commits to `main`.
5. GitHub Actions runs checks and deploys.
6. You test the live frontend.

## Future Workflow
User -> Builder Core -> Auto Codex -> GitHub -> Deploy -> Status in app

Future automation should work like this:
1. You enter a task directly in Builder Core.
2. Builder Core prepares a Codex-ready task.
3. After confirmation and authentication, Builder Core sends the task automatically.
4. GitHub receives the change request.
5. Deployment runs after checks pass.
6. Builder Core shows the task status, logs, and final result in the app.

## Safety Rules
- No automatic repo modification without user confirmation.
- Authentication is required before automation can act.
- Logs and transparency are required for every automated action.
- Codex must explain which files changed.
- Codex must not delete working features unless the task clearly requires it.
- Codex should run checks when possible.
- Codex must provide beginner-friendly testing steps.

## Legal And Originality Rules
- Prefer original repo-specific implementations.
- Do not paste recognizable third-party snippets.
- Keep the code easy to read and easy to review.
- Use licensed frameworks such as Next.js, React, and FastAPI in a normal supported way.
- Keep the project safe for commercial use by avoiding unknown copyrighted code.

## Manual Mode Today
Builder Core currently stays in manual mode.

That means:
- You decide what task to run.
- You review the prompt before using it.
- Nothing should modify the repo automatically without your approval.

## Simple Prompt Pattern
A good Builder Core prompt should include:
- repo name
- goal
- what must stay working
- what to test
- any safety rules

Example:

Repo: jagangill001/builder-core
Goal: Improve the mobile dashboard and keep the backend connection working.
Do not delete working features.
Explain files changed.
Provide testing steps.
