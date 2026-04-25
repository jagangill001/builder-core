"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const FRONTEND_APP_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";
const EMPTY_PROMPT_MESSAGE = "Generated Codex prompt will appear here.";
const EMPTY_PLANNER_MESSAGE = "Planner output will appear here.";
const MISSING_PROMPT_MESSAGE = "Add an instruction above to generate a Codex prompt.";
const MISSING_PLANNER_MESSAGE = "Add an instruction above to generate a planner.";

const PIPELINE_STEP_DEFINITIONS = [
  {
    key: "sent_to_codex",
    label: "Sent to Codex",
    description: "The task has been handed off from the Command Center."
  },
  {
    key: "codex_working",
    label: "Codex Working",
    description: "Codex is actively working through the instruction."
  },
  {
    key: "code_done",
    label: "Code Done",
    description: "The code changes are ready for the deployment pipeline."
  },
  {
    key: "github_deploying",
    label: "GitHub Deploying",
    description: "GitHub Actions is building and deploying the update."
  },
  {
    key: "cloud_run_live",
    label: "Cloud Run Live",
    description: "The new Cloud Run revision is live."
  },
  {
    key: "app_refreshed",
    label: "App Refreshed",
    description: "The frontend has reloaded and is showing the latest version."
  }
] as const;

type HistoryItem = {
  instruction: string;
  status: string;
  project_name: string;
  plan: string[];
  created_files?: string[];
};

type ProjectItem = {
  id: number;
  name: string;
};

type RunInfo = {
  project_name: string;
  project_path: string;
  run_script: string;
  commands: string[];
  url_hint: string;
};

type ExecutionStatus = "idle" | "prepared" | "sent" | "completed";

type CommandTask = {
  instruction: string;
  prompt: string;
  timestamp: string;
};

type PipelineStage = "idle" | "codex_working" | "deploying" | "refresh_ready" | "refreshed";

type PipelineStepStatus = "pending" | "active" | "done";

type PipelineStep = {
  key: string;
  label: string;
  description: string;
  status: PipelineStepStatus;
};

type ReviewStatus = "ready" | "attention";

type ReviewChecklistItem = {
  label: string;
  status: ReviewStatus;
  detail: string;
};

type ReviewSummary = {
  checklist: ReviewChecklistItem[];
  doItems: string[];
  avoidItems: string[];
};

function buildCodexPrompt(instruction: string, projectName: string) {
  return [
    "Repo: jagangill001/builder-core",
    `Selected project: ${projectName}`,
    "",
    "Goal:",
    instruction,
    "",
    "Safety rules:",
    "- Inspect the repo before editing.",
    "- Do not delete working features.",
    "- Commit directly to main.",
    "- Explain every file changed.",
    "- Provide testing steps.",
    "",
    "Legal rules:",
    "- Write original code for this repo.",
    "- Do not blindly copy third-party snippets.",
    "- Use licensed frameworks only.",
    "",
    "Do not break:",
    "- Existing frontend/backend connection",
    "- Current request submission flow",
    "- Backend health indicator",
    "- PWA install behavior",
    "",
    "Return:",
    "1. Files changed",
    "2. Short explanation of changes",
    "3. Testing steps"
  ].join("\n");
}

function buildPlannerPrompt(instruction: string, projectName: string) {
  return [
    "ChatGPT Planner",
    `Project: ${projectName}`,
    `Instruction: ${instruction}`,
    "",
    "Task Breakdown:",
    "1. Inspect the relevant frontend, backend, deployment, and documentation files.",
    "2. Translate the request into the smallest safe set of file changes.",
    "3. Preserve working features before adding or modifying behavior.",
    "4. Verify the result with focused checks before closing the task.",
    "",
    "Risks:",
    "- Breaking the frontend/backend connection or backend health indicator.",
    "- Regressing the request flow, Command Center, or mobile install behavior.",
    "- Making broad changes when a small targeted change is safer.",
    "",
    "Codex-ready Instruction:",
    buildCodexPrompt(instruction, projectName),
    "",
    "Testing Plan:",
    "- Confirm the backend health indicator still reports correctly.",
    "- Confirm the main request submission flow still works.",
    "- Confirm the new UI behaves correctly on desktop and phone widths.",
    "- Confirm the live frontend and backend URLs still load after deploy."
  ].join("\n");
}

function getExecutionStatusLabel(status: ExecutionStatus) {
  if (status === "prepared") {
    return "Prepared";
  }

  if (status === "sent") {
    return "Sent (waiting for Codex)";
  }

  if (status === "completed") {
    return "Completed";
  }

  return "Idle";
}

function formatTaskTimestamp(date: Date) {
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function buildAutomationPipeline(stage: PipelineStage): PipelineStep[] {
  const doneThresholdByStage: Record<PipelineStage, number> = {
    idle: -1,
    codex_working: 0,
    deploying: 2,
    refresh_ready: 4,
    refreshed: 5
  };

  const activeIndexByStage: Record<PipelineStage, number> = {
    idle: -1,
    codex_working: 1,
    deploying: 3,
    refresh_ready: 5,
    refreshed: -1
  };

  const doneThreshold = doneThresholdByStage[stage];
  const activeIndex = activeIndexByStage[stage];

  return PIPELINE_STEP_DEFINITIONS.map((step, index) => {
    let status: PipelineStepStatus = "pending";

    if (index <= doneThreshold) {
      status = "done";
    } else if (index === activeIndex) {
      status = "active";
    }

    return {
      ...step,
      status
    };
  });
}

function getPipelineStatusBadgeClass(status: PipelineStepStatus) {
  if (status === "done") {
    return "border border-green-200 bg-green-100 text-green-700";
  }

  if (status === "active") {
    return "border border-blue-200 bg-blue-100 text-blue-700";
  }

  return "border border-gray-200 bg-gray-100 text-gray-600";
}

function getPipelineCardClass(status: PipelineStepStatus) {
  if (status === "done") {
    return "border-green-200 bg-green-50";
  }

  if (status === "active") {
    return "border-blue-200 bg-blue-50";
  }

  return "border-gray-200 bg-white";
}

function getPipelineDotClass(status: PipelineStepStatus) {
  if (status === "done") {
    return "bg-green-600";
  }

  if (status === "active") {
    return "bg-blue-600";
  }

  return "bg-gray-300";
}

function getReviewBadgeClass(status: ReviewStatus) {
  if (status === "ready") {
    return "border border-green-200 bg-green-100 text-green-700";
  }

  return "border border-amber-200 bg-amber-100 text-amber-700";
}

function buildReviewSummary(reviewText: string, backendState: "checking" | "online" | "offline"): ReviewSummary {
  const normalized = reviewText.toLowerCase();
  const matchesAny = (patterns: RegExp[]) => patterns.some((pattern) => pattern.test(normalized));

  const filesChanged = matchesAny([/files?\s+changed/, /changed files/, /modified/, /created/, /updated/, /edited/]);
  const buildPassed = matchesAny([/build\s+(passed|successful|succeeded)/, /compiled successfully/, /tests?\s+passed/, /lint\s+passed/]);
  const actionsGreen = matchesAny([/github actions.*(green|passed|successful)/, /ci\s+(passed|green)/, /workflow\s+(passed|successful)/, /checks\s+passed/]);
  const frontendDeployed = matchesAny([/frontend.*deployed/, /cloud run live/, /deploy(ed)? successfully/, /frontend live/, /new revision live/, /service updated/]);
  const backendStillOnline = backendState === "online" || matchesAny([/backend.*online/, /system status.*ok/, /backend live/]);

  const checklist: ReviewChecklistItem[] = [
    {
      label: "Files changed?",
      status: filesChanged ? "ready" : "attention",
      detail: filesChanged ? "The summary mentions changed files." : "Confirm the exact files changed before approving the result."
    },
    {
      label: "Build passed?",
      status: buildPassed ? "ready" : "attention",
      detail: buildPassed ? "The result indicates the build or tests passed." : "Run or verify a clean build before trusting the change."
    },
    {
      label: "GitHub Actions green?",
      status: actionsGreen ? "ready" : "attention",
      detail: actionsGreen ? "The summary suggests CI finished successfully." : "Wait for GitHub Actions to turn green before calling this complete."
    },
    {
      label: "Frontend deployed?",
      status: frontendDeployed ? "ready" : "attention",
      detail: frontendDeployed ? "The summary points to a live frontend deploy." : "Open the live frontend and confirm the new revision is visible."
    },
    {
      label: "Backend still online?",
      status: backendStillOnline ? "ready" : "attention",
      detail: backendStillOnline ? "The backend health signal looks healthy." : "Recheck /system/status before approving the rollout."
    }
  ];

  const doItems = [
    filesChanged ? "Review the changed files against the original instruction." : "Capture the exact files changed before moving forward.",
    buildPassed ? "Do a quick smoke test in the live app." : "Run or confirm a build before accepting the change.",
    actionsGreen ? "Open the successful GitHub Actions run and note the revision." : "Wait for GitHub Actions to finish green.",
    frontendDeployed ? "Confirm the latest frontend revision is serving the expected UI." : "Verify the live frontend is actually updated.",
    backendStillOnline ? "Keep the backend health indicator visible while testing." : "Recheck backend health before approving the result."
  ];

  const avoidItems = [
    "Do not stack risky follow-up changes on top of an unverified deploy.",
    "Do not delete working features to make a fix easier.",
    "Do not assume Cloud Run is healthy until both frontend and backend checks pass."
  ];

  return {
    checklist,
    doItems,
    avoidItems
  };
}

export default function Home() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState("No request submitted yet.");
  const [status, setStatus] = useState("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [commandCenterInput, setCommandCenterInput] = useState("");
  const [codexPrompt, setCodexPrompt] = useState(EMPTY_PROMPT_MESSAGE);
  const [plannerOutput, setPlannerOutput] = useState(EMPTY_PLANNER_MESSAGE);
  const [commandCenterMessage, setCommandCenterMessage] = useState("");
  const [plannerMessage, setPlannerMessage] = useState("");
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>("idle");
  const [pipelineStage, setPipelineStage] = useState<PipelineStage>("idle");
  const [lastTask, setLastTask] = useState<CommandTask | null>(null);
  const [reviewInput, setReviewInput] = useState("");
  const [reviewResult, setReviewResult] = useState<ReviewSummary | null>(null);
  const [reviewMessage, setReviewMessage] = useState("");
  const [installMessage, setInstallMessage] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectFiles, setProjectFiles] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState("Default Project");
  const [newProjectName, setNewProjectName] = useState("");
  const [runInfo, setRunInfo] = useState<RunInfo | null>(null);

  const automationPipeline = useMemo(() => buildAutomationPipeline(pipelineStage), [pipelineStage]);
  const completedPipelineSteps = automationPipeline.filter((step) => step.status === "done").length;
  const pipelineProgress = Math.round((completedPipelineSteps / automationPipeline.length) * 100);

  const canCopyPrompt =
    codexPrompt !== EMPTY_PROMPT_MESSAGE &&
    codexPrompt !== MISSING_PROMPT_MESSAGE;

  const canMarkCodexDone = pipelineStage === "codex_working";
  const canMarkDeployDone = pipelineStage === "deploying";
  const canRefreshApp = pipelineStage === "refresh_ready";

  async function checkBackendStatus() {
    try {
      const response = await fetch(`${API_BASE}/system/status`);

      if (!response.ok) {
        throw new Error("Backend status check failed");
      }

      setBackendStatus("online");
    } catch {
      setBackendStatus("offline");
    }
  }

  async function loadProjects() {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json();
      const items = data.items || [];
      setProjects(items);

      if (items.length > 0 && !items.find((p: ProjectItem) => p.name === selectedProject)) {
        setSelectedProject(items[0].name);
      }
    } catch {
      console.log("Could not load projects");
    }
  }

  async function loadHistory(projectName?: string) {
    try {
      const url = projectName
        ? `${API_BASE}/history?project_name=${encodeURIComponent(projectName)}`
        : `${API_BASE}/history`;

      const response = await fetch(url);
      const data = await response.json();
      setHistory(data.items || []);
    } catch {
      console.log("Could not load history");
    }
  }

  async function loadProjectFiles(projectName: string) {
    try {
      const response = await fetch(`${API_BASE}/project-files?project_name=${encodeURIComponent(projectName)}`);
      const data = await response.json();
      setProjectFiles(data.items || []);
    } catch {
      console.log("Could not load project files");
    }
  }

  async function loadRunInfo(projectName: string) {
    try {
      const response = await fetch(`${API_BASE}/run-info?project_name=${encodeURIComponent(projectName)}`);
      const data = await response.json();
      setRunInfo(data);
    } catch {
      console.log("Could not load run info");
    }
  }

  useEffect(() => {
    checkBackendStatus();
    loadProjects();
    loadHistory(selectedProject);
    loadProjectFiles(selectedProject);
    loadRunInfo(selectedProject);
  }, []);

  useEffect(() => {
    loadHistory(selectedProject);
    loadProjectFiles(selectedProject);
    loadRunInfo(selectedProject);
  }, [selectedProject]);

  function prepareTaskArtifacts() {
    const trimmedInstruction = commandCenterInput.trim();

    if (!trimmedInstruction) {
      setCodexPrompt(MISSING_PROMPT_MESSAGE);
      setPlannerOutput(MISSING_PLANNER_MESSAGE);
      return null;
    }

    const prompt = buildCodexPrompt(trimmedInstruction, selectedProject);
    const planner = buildPlannerPrompt(trimmedInstruction, selectedProject);
    const nextTask = {
      instruction: trimmedInstruction,
      prompt,
      timestamp: formatTaskTimestamp(new Date())
    };

    setCodexPrompt(prompt);
    setPlannerOutput(planner);
    setLastTask(nextTask);
    return nextTask;
  }

  function handleGeneratePlanner() {
    const nextTask = prepareTaskArtifacts();

    if (!nextTask) {
      setExecutionStatus("idle");
      setPipelineStage("idle");
      setPlannerMessage("Add an instruction first.");
      return;
    }

    setExecutionStatus("prepared");
    setPipelineStage("idle");
    setPlannerMessage("Planner prepared.");
    setCommandCenterMessage("");
  }

  function handleGeneratePrompt() {
    const nextTask = prepareTaskArtifacts();

    if (!nextTask) {
      setExecutionStatus("idle");
      setPipelineStage("idle");
      setCommandCenterMessage("Add an instruction first.");
      return;
    }

    setExecutionStatus("prepared");
    setPipelineStage("idle");
    setCommandCenterMessage("Codex prompt prepared.");
    setPlannerMessage("");
  }

  function handleSendToCodex() {
    const nextTask = prepareTaskArtifacts();

    if (!nextTask) {
      setExecutionStatus("idle");
      setPipelineStage("idle");
      setCommandCenterMessage("Add an instruction first.");
      return;
    }

    setExecutionStatus("sent");
    setPipelineStage("codex_working");
    setCommandCenterMessage("Task prepared for Codex.");
    setPlannerMessage("");
  }

  function handleMarkCodexDone() {
    if (!lastTask) {
      return;
    }

    setExecutionStatus("sent");
    setPipelineStage("deploying");
    setCommandCenterMessage("Codex work marked done. Deployment is now active.");
  }

  function handleMarkDeployDone() {
    if (!lastTask) {
      return;
    }

    setExecutionStatus("sent");
    setPipelineStage("refresh_ready");
    setCommandCenterMessage("Deployment marked done. Refresh the app to complete the flow.");
  }

  function handleRefreshApp() {
    if (!lastTask) {
      return;
    }

    setExecutionStatus("completed");
    setPipelineStage("refreshed");
    setCommandCenterMessage("App refresh starting.");

    window.setTimeout(() => {
      window.location.reload();
    }, 350);
  }

  async function handleCopyPrompt() {
    if (!canCopyPrompt) {
      return;
    }

    try {
      await navigator.clipboard.writeText(codexPrompt);
      setCommandCenterMessage("Prompt copied.");
    } catch {
      setCommandCenterMessage("Copy failed. Select the prompt and copy it manually.");
    }
  }

  function handleReviewResult() {
    if (!reviewInput.trim()) {
      setReviewResult(null);
      setReviewMessage("Paste a Codex summary or deploy result first.");
      return;
    }

    setReviewResult(buildReviewSummary(reviewInput, backendStatus));
    setReviewMessage("Review prepared.");
  }

  function handleOpenAppLink() {
    window.open(FRONTEND_APP_URL, "_blank", "noopener,noreferrer");
    setInstallMessage("Opened the live app link.");
  }

  async function handleCopyAppLink() {
    try {
      await navigator.clipboard.writeText(FRONTEND_APP_URL);
      setInstallMessage("App link copied.");
    } catch {
      setInstallMessage("Copy failed. Copy the app link manually from the box below.");
    }
  }

  async function handleCreateProject() {
    if (!newProjectName.trim()) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: newProjectName
        })
      });

      const data = await response.json();

      if (data.ok && data.project) {
        setSelectedProject(data.project.name);
        setNewProjectName("");
        await loadProjects();
        await loadHistory(data.project.name);
        await loadProjectFiles(data.project.name);
        await loadRunInfo(data.project.name);
      }
    } catch {
      console.log("Could not create project");
    }
  }

  async function handleSubmit() {
    if (!request.trim()) {
      setResult("Please enter an instruction.");
      setStatus("error");
      return;
    }

    setResult("Sending request to backend...");
    setStatus("loading");

    try {
      const response = await fetch(`${API_BASE}/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          instruction: request,
          project_name: selectedProject
        })
      });

      const data = await response.json();

      if (!data.ok) {
        setResult(data.message || "Something went wrong.");
        setStatus("error");
        return;
      }

      setStatus(data.status);

      const filesText =
        data.created_files && data.created_files.length > 0
          ? "\n\nCreated Files:\n- " + data.created_files.join("\n- ")
          : "\n\nCreated Files:\n- No files generated for this request.";

      setResult(
        "Message: " + data.message +
        "\n\nProject: " + data.project_name +
        "\nModule Key: " + data.module_key +
        "\nTitle: " + data.title +
        "\nRoute Path: " + data.route_path +
        "\n\nInstruction: " + data.instruction +
        "\n\nPlan:\n- " + data.plan.join("\n- ") +
        filesText
      );

      setRequest("");
      loadHistory(selectedProject);
      loadProjectFiles(selectedProject);
      loadRunInfo(selectedProject);
    } catch {
      setResult("Could not connect to backend.");
      setStatus("error");
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-6 text-black sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-2 text-3xl font-bold sm:text-4xl">Builder Core Dashboard</h1>
        <p className="mb-3 text-gray-600">
          Builder Core v5 with generated app shells, planning help, and deployment tracking.
        </p>
        <p
          className={
            backendStatus === "online"
              ? "mb-6 text-sm font-medium text-green-600"
              : backendStatus === "offline"
                ? "mb-6 text-sm font-medium text-red-600"
                : "mb-6 text-sm font-medium text-gray-500"
          }
        >
          {backendStatus === "checking" && "Backend: Checking..."}
          {backendStatus === "online" && "Backend: Online"}
          {backendStatus === "offline" && "Backend: Offline"}
        </p>

        <div className="mb-6 grid gap-6 lg:grid-cols-[2fr,1fr]">
          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-2 text-xl font-semibold">Command Center</h2>
            <p className="mb-4 text-sm text-gray-600">
              Describe what you want to build, fix, or upgrade, then generate the Codex-ready instruction without leaving the app.
            </p>

            <textarea
              value={commandCenterInput}
              onChange={(e) => setCommandCenterInput(e.target.value)}
              placeholder="Tell Builder Core what to build, fix, or upgrade..."
              className="mb-4 h-36 w-full rounded-xl border p-4"
            />

            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <button
                type="button"
                onClick={handleGeneratePrompt}
                className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
              >
                Generate Codex Prompt
              </button>
              <button
                type="button"
                onClick={handleSendToCodex}
                className="w-full rounded-xl bg-blue-600 px-5 py-3 text-white sm:w-auto"
              >
                Send to Codex
              </button>
              <button
                type="button"
                onClick={handleCopyPrompt}
                disabled={!canCopyPrompt}
                className={
                  canCopyPrompt
                    ? "w-full rounded-xl border border-black px-5 py-3 text-black sm:w-auto"
                    : "w-full rounded-xl border border-gray-200 px-5 py-3 text-gray-400 sm:w-auto"
                }
              >
                Copy Prompt
              </button>
            </div>

            {commandCenterMessage && (
              <p className="mb-3 text-sm text-gray-600">{commandCenterMessage}</p>
            )}

            <p className="mb-2 text-sm font-semibold text-gray-700">Generated Codex Prompt</p>
            <textarea
              value={codexPrompt}
              readOnly
              className="h-72 w-full rounded-xl border bg-gray-50 p-4 text-sm"
            />
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
              <h2 className="mb-3 text-xl font-semibold">Automation Status</h2>
              <div className="mb-4 inline-flex rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700">
                Manual mode active
              </div>
              <p className="mb-3 text-sm text-gray-700">
                Future version will send tasks automatically.
              </p>
              <ul className="list-disc space-y-2 pl-5 text-sm text-gray-600">
                <li>No automatic repo modification without user confirmation.</li>
                <li>Authentication will be required before automation can act.</li>
                <li>Logs and transparent status updates will stay visible in the app.</li>
              </ul>
            </div>

            <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
              <h2 className="mb-3 text-xl font-semibold">Execution Status</h2>
              <p className="text-sm text-gray-700">{getExecutionStatusLabel(executionStatus)}</p>
            </div>

            <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
              <h2 className="mb-3 text-xl font-semibold">Last Task</h2>
              {!lastTask ? (
                <p className="text-sm text-gray-500">No task prepared yet.</p>
              ) : (
                <div className="space-y-3 text-sm text-gray-700">
                  <p><strong>Instruction:</strong> {lastTask.instruction}</p>
                  <p><strong>Timestamp:</strong> {lastTask.timestamp}</p>
                  <div>
                    <p className="mb-2 font-semibold">Generated Prompt</p>
                    <pre className="whitespace-pre-wrap rounded-xl border bg-gray-50 p-4 text-sm">
{lastTask.prompt}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mb-6 grid gap-6 lg:grid-cols-[2fr,1fr]">
          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-2 text-xl font-semibold">ChatGPT Planner</h2>
            <p className="mb-4 text-sm text-gray-600">
              Generate a planning view that breaks the task into steps, calls out risks, and prepares the Codex-ready instruction plus testing plan.
            </p>

            <div className="mb-4 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleGeneratePlanner}
                className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
              >
                Generate Planner
              </button>
            </div>

            {plannerMessage && (
              <p className="mb-3 text-sm text-gray-600">{plannerMessage}</p>
            )}

            <p className="mb-2 text-sm font-semibold text-gray-700">Planner Output</p>
            <textarea
              value={plannerOutput}
              readOnly
              className="h-80 w-full rounded-xl border bg-gray-50 p-4 text-sm"
            />
          </div>

          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-3 text-xl font-semibold">Download / Install</h2>
            <p className="mb-4 text-sm text-gray-600">No App Store needed.</p>

            <div className="mb-4 flex flex-col gap-3">
              <button
                type="button"
                onClick={handleOpenAppLink}
                className="w-full rounded-xl bg-black px-5 py-3 text-white"
              >
                Open App Link
              </button>
              <button
                type="button"
                onClick={handleCopyAppLink}
                className="w-full rounded-xl border border-black px-5 py-3 text-black"
              >
                Copy App Link
              </button>
            </div>

            {installMessage && (
              <p className="mb-3 text-sm text-gray-600">{installMessage}</p>
            )}

            <div className="mb-4 rounded-xl border bg-gray-50 p-4 text-sm text-gray-700">
              {FRONTEND_APP_URL}
            </div>

            <div className="space-y-4 text-sm text-gray-700">
              <div>
                <p className="mb-2 font-semibold">iPhone</p>
                <ul className="list-disc space-y-1 pl-5">
                  <li>Open in Safari.</li>
                  <li>Tap Share.</li>
                  <li>Add to Home Screen.</li>
                </ul>
              </div>
              <div>
                <p className="mb-2 font-semibold">Android</p>
                <ul className="list-disc space-y-1 pl-5">
                  <li>Open in Chrome.</li>
                  <li>Tap the menu icon.</li>
                  <li>Install app.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="mb-2 text-xl font-semibold">Automation Pipeline</h2>
              <p className="text-sm text-gray-600">
                This simulated tracker mirrors the future path from Codex work to deployment and app refresh.
              </p>
              <p className="mt-2 text-sm font-medium text-amber-700">
                This is manual simulation. Future version will automate this.
              </p>
            </div>
            <div className="min-w-32">
              <div className="mb-2 flex items-center justify-between text-xs font-medium text-gray-500">
                <span>Progress</span>
                <span>{pipelineProgress}%</span>
              </div>
              <div className="h-2 rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-blue-600 transition-all"
                  style={{ width: `${pipelineProgress}%` }}
                />
              </div>
            </div>
          </div>

          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <button
              type="button"
              onClick={handleMarkCodexDone}
              disabled={!canMarkCodexDone}
              className={
                canMarkCodexDone
                  ? "w-full rounded-xl border border-black px-5 py-3 text-black sm:w-auto"
                  : "w-full rounded-xl border border-gray-200 px-5 py-3 text-gray-400 sm:w-auto"
              }
            >
              Mark Codex Done
            </button>
            <button
              type="button"
              onClick={handleMarkDeployDone}
              disabled={!canMarkDeployDone}
              className={
                canMarkDeployDone
                  ? "w-full rounded-xl border border-black px-5 py-3 text-black sm:w-auto"
                  : "w-full rounded-xl border border-gray-200 px-5 py-3 text-gray-400 sm:w-auto"
              }
            >
              Mark Deploy Done
            </button>
            <button
              type="button"
              onClick={handleRefreshApp}
              disabled={!canRefreshApp}
              className={
                canRefreshApp
                  ? "w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
                  : "w-full rounded-xl border border-gray-200 px-5 py-3 text-gray-400 sm:w-auto"
              }
            >
              Refresh App
            </button>
          </div>

          <ol className="flex flex-col gap-3 xl:flex-row">
            {automationPipeline.map((step, index) => (
              <li
                key={step.key}
                className={`flex-1 rounded-xl border p-4 ${getPipelineCardClass(step.status)}`}
              >
                <div className="mb-3 flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Step {index + 1}
                  </span>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${getPipelineStatusBadgeClass(step.status)}`}>
                    {step.status === "pending" && "Pending"}
                    {step.status === "active" && "Active"}
                    {step.status === "done" && "Done"}
                  </span>
                </div>

                <div className="mb-2 flex items-center gap-3">
                  <span className={`h-3 w-3 rounded-full ${getPipelineDotClass(step.status)}`} />
                  <p className="font-semibold">{step.label}</p>
                </div>
                <p className="text-sm text-gray-600">{step.description}</p>
              </li>
            ))}
          </ol>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-3 text-xl font-semibold">Codex Result Review</h2>
          <p className="mb-4 text-sm text-gray-600">
            Paste a Codex summary or deploy result, then get a quick review checklist and safe next-step suggestions.
          </p>

          <textarea
            value={reviewInput}
            onChange={(e) => setReviewInput(e.target.value)}
            placeholder="Paste Codex summary or deploy result here..."
            className="mb-4 h-36 w-full rounded-xl border p-4"
          />

          <div className="mb-4 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleReviewResult}
              className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
            >
              Review Result
            </button>
          </div>

          {reviewMessage && (
            <p className="mb-4 text-sm text-gray-600">{reviewMessage}</p>
          )}

          {reviewResult && (
            <div className="space-y-6">
              <div>
                <h3 className="mb-3 text-lg font-semibold">Checklist</h3>
                <div className="space-y-3">
                  {reviewResult.checklist.map((item) => (
                    <div key={item.label} className="rounded-xl border bg-gray-50 p-4">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <p className="font-semibold">{item.label}</p>
                        <span className={`rounded-full px-3 py-1 text-xs font-medium ${getReviewBadgeClass(item.status)}`}>
                          {item.status === "ready" ? "Looks good" : "Check this"}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{item.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-xl border bg-green-50 p-4">
                  <h3 className="mb-3 text-lg font-semibold text-green-800">Do</h3>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-green-900">
                    {reviewResult.doItems.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border bg-amber-50 p-4">
                  <h3 className="mb-3 text-lg font-semibold text-amber-800">Do Not</h3>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-amber-900">
                    {reviewResult.avoidItems.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">Projects</h2>

          <div className="mb-4 flex flex-col gap-3 md:flex-row">
            <input
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="New project name"
              className="flex-1 rounded-xl border px-4 py-3"
            />
            <button
              type="button"
              onClick={handleCreateProject}
              className="w-full rounded-xl bg-black px-5 py-3 text-white md:w-auto"
            >
              Create Project
            </button>
          </div>

          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="w-full rounded-xl border px-4 py-3 md:w-80"
          >
            {projects.length === 0 ? (
              <option>Default Project</option>
            ) : (
              projects.map((project) => (
                <option key={project.id} value={project.name}>
                  {project.name}
                </option>
              ))
            )}
          </select>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">New Request</h2>

          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="Examples:
Create a notes page with add, edit, and delete.
Build a vendor dashboard for comparing supplier quotes.
Add login page with email and password.
Create a dashboard with summary cards."
            className="mb-4 h-48 w-full rounded-xl border p-4"
          />

          <button
            type="button"
            onClick={handleSubmit}
            className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
          >
            Submit Request
          </button>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <div className="mb-3 flex items-center gap-3">
            <h2 className="text-xl font-semibold">Latest Result</h2>
            {status && (
              <span className="rounded-full border px-3 py-1 text-sm">
                {status}
              </span>
            )}
          </div>
          <pre className="whitespace-pre-wrap text-sm">{result}</pre>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">Run Generated App</h2>

          {!runInfo ? (
            <p className="text-gray-500">No run info available.</p>
          ) : (
            <div className="space-y-3">
              <p><strong>Project:</strong> {runInfo.project_name}</p>
              <p><strong>Path:</strong> {runInfo.project_path}</p>
              <p><strong>Run Script:</strong> {runInfo.run_script}</p>
              <p className="text-sm text-gray-600">{runInfo.url_hint}</p>

              <div>
                <p className="mb-2 font-semibold">Commands:</p>
                <pre className="whitespace-pre-wrap rounded-xl border bg-gray-50 p-4 text-sm">
{runInfo.commands.join("\n")}
                </pre>
              </div>
            </div>
          )}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-4 text-xl font-semibold">
              Request History for {selectedProject}
            </h2>

            {history.length === 0 ? (
              <p className="text-gray-500">No requests yet.</p>
            ) : (
              <div className="space-y-4">
                {history.map((item, index) => (
                  <div key={index} className="rounded-xl border p-4">
                    <p className="mb-2 font-semibold">{item.instruction}</p>
                    <p className="mb-1 text-sm">Project: {item.project_name}</p>
                    <p className="mb-2 text-sm">Status: {item.status}</p>

                    <ul className="mb-3 list-disc pl-5 text-sm">
                      {item.plan.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ul>

                    {item.created_files && item.created_files.length > 0 && (
                      <div>
                        <p className="mb-1 text-sm font-semibold">Created Files:</p>
                        <ul className="list-disc pl-5 text-sm">
                          {item.created_files.map((file, fileIndex) => (
                            <li key={fileIndex}>{file}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-4 text-xl font-semibold">
              Project Files for {selectedProject}
            </h2>

            {projectFiles.length === 0 ? (
              <p className="text-gray-500">No files yet.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {projectFiles.map((file, index) => (
                  <li key={index}>{file}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
