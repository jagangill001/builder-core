# Builder Core Command Center

## Purpose
Builder Core is moving toward a simple command center model.

Today you can use ChatGPT from your phone, generate a clean Codex prompt, review the plan, track the pipeline, and deploy through GitHub Actions.

## Current Workflow
User -> ChatGPT -> Codex -> GitHub -> Deploy

1. You give an idea or instruction in ChatGPT.
2. ChatGPT or the in-app planner organizes the task.
3. Codex receives a clean prompt and updates the repo.
4. GitHub Actions runs checks and deploys.
5. You review the result and test the live frontend.

## Future Workflow
User -> Builder Core -> Auto Codex -> GitHub -> Deploy -> App status

Future automation should work like this:
1. You enter a task directly in Builder Core.
2. Builder Core prepares the planner output and Codex-ready task.
3. After confirmation and authentication, Builder Core sends the task automatically.
4. GitHub receives the change request.
5. Deployment runs after checks pass.
6. Builder Core shows task status, review notes, logs, and final result in the app.

## In-App Sections
- `Command Center`: generates the Codex-ready task.
- `ChatGPT Planner`: breaks work into steps, risks, and tests.
- `Automation Pipeline`: tracks the simulated delivery flow.
- `Codex Result Review`: reviews summaries and deploy results.
- `Download / Install`: helps users install the app on phone.

## Automation Pipeline
Builder Core now includes a visual automation pipeline with these stages:
1. Sent to Codex
2. Codex Working
3. Code Done
4. GitHub Deploying
5. Cloud Run Live
6. App Refreshed

### Current Manual Simulation
For now, the pipeline is still manual and safe:
- `Send to Codex` marks the task as handed off and starts the Codex working step.
- `Mark Codex Done` moves the task into the deployment phase.
- `Mark Deploy Done` marks the deploy as live and makes the app refresh step active.
- `Refresh App` completes the last step and reloads the frontend.

### Future Automation Sources
Later, these steps can be updated automatically from:
- Codex task status
- GitHub Actions status
- Cloud Run deploy status
- backend webhook events

## Future Backend Automation Prep
Planned backend endpoints:
- `POST /automation/tasks`
- `GET /automation/tasks`
- `GET /automation/tasks/{id}`

Planned frontend behavior:
- `Send to Codex` will later call `POST /automation/tasks`.
- The app will later load task lists from `GET /automation/tasks`.
- The app will later show one task status from `GET /automation/tasks/{id}`.
- Backend webhooks can later advance pipeline steps automatically.

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
- any legal rules

Example:

Repo: jagangill001/builder-core
Goal: Improve the mobile dashboard and keep the backend connection working.
Do not delete working features.
Explain files changed.
Provide testing steps.
Use original code and licensed frameworks only.
