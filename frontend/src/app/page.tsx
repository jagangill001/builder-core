"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const FRONTEND_APP_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";

const PIPELINE_STEP_DEFINITIONS = [
  {
    key: "task_received",
    label: "Task Received",
    description: "Builder Core accepted the instruction and opened the task."
  },
  {
    key: "planning",
    label: "Planning",
    description: "The planner organized the work, risks, and testing approach."
  },
  {
    key: "codex_ready",
    label: "Codex Ready",
    description: "The Codex-ready task is prepared and waiting to be sent."
  },
  {
    key: "codex_working",
    label: "Codex Working",
    description: "Codex is working through the requested change."
  },
  {
    key: "github_deploying",
    label: "GitHub Deploying",
    description: "GitHub Actions is building and deploying the latest revision."
  },
  {
    key: "cloud_run_live",
    label: "Cloud Run Live",
    description: "The new Cloud Run revision is live."
  },
  {
    key: "app_refreshed",
    label: "App Refreshed",
    description: "The app reloaded and is showing the latest state."
  }
] as const;

type ProjectItem = {
  id: number;
  name: string;
};

type ExecutionStatus = "idle" | "prepared" | "sent" | "completed";

type PipelineStage =
  | "idle"
  | "codex_ready"
  | "codex_working"
  | "github_deploying"
  | "refresh_pending"
  | "refreshed";

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

type CommandTask = {
  instruction: string;
  planner: string;
  prompt: string;
  timestamp: string;
  builderSummary?: string | null;
};

type ChatEntry = {
  id: string;
  role: "user" | "assistant";
  kind: "text" | "planner" | "codex" | "builder" | "review";
  title?: string;
  content?: string;
  review?: ReviewSummary;
  timestamp: string;
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
    "- Do not break working features.",
    "- Commit to main.",
    "- Explain files changed.",
    "- Provide testing steps.",
    "",
    "Legal rules:",
    "- Write original code for this repo.",
    "- Do not blindly copy third-party snippets.",
    "- Licensed frameworks are allowed when used normally.",
    "",
    "Do not break:",
    "- Frontend/backend connection",
    "- Health indicator",
    "- Request submission flow",
    "- PWA install behavior"
  ].join("\n");
}

function buildPlannerOutput(instruction: string, projectName: string) {
  return [
    "ChatGPT Planner",
    `Project: ${projectName}`,
    `Instruction: ${instruction}`,
    "",
    "Step-by-step plan:",
    "1. Inspect the frontend, backend, deployment, and docs that relate to the request.",
    "2. Keep the smallest safe change set that solves the request.",
    "3. Preserve working features before adding or modifying anything.",
    "4. Prepare a Codex-ready implementation task with clear boundaries.",
    "5. Verify the result with focused tests and live checks.",
    "",
    "Risks:",
    "- Breaking the frontend/backend connection or backend health indicator.",
    "- Regressing the request flow or install experience.",
    "- Making broad UI or deploy changes when a smaller change is safer.",
    "",
    "Testing plan:",
    "- Confirm /system/status still reports correctly in the app.",
    "- Confirm the main request submission flow still works.",
    "- Confirm the latest UI works on desktop and phone widths.",
    "- Confirm the live frontend and backend still load after deployment."
  ].join("\n");
}

function formatTimestamp(date: Date) {
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function getExecutionStatusLabel(status: ExecutionStatus) {
  if (status === "prepared") {
    return "Prepared";
  }

  if (status === "sent") {
    return "Sent";
  }

  if (status === "completed") {
    return "Completed";
  }

  return "Idle";
}

function getAutomationStatusLabel(stage: PipelineStage, countdown: number | null) {
  if (stage === "codex_ready") {
    return "Codex Ready";
  }

  if (stage === "codex_working") {
    return "Codex Working";
  }

  if (stage === "github_deploying") {
    return "Deploying";
  }

  if (stage === "refresh_pending") {
    return countdown !== null ? `Refreshing in ${countdown}s` : "Refresh Pending";
  }

  if (stage === "refreshed") {
    return "Refreshed";
  }

  return "Manual";
}

function buildAutomationPipeline(stage: PipelineStage): PipelineStep[] {
  const doneThresholdByStage: Record<PipelineStage, number> = {
    idle: -1,
    codex_ready: 1,
    codex_working: 2,
    github_deploying: 3,
    refresh_pending: 5,
    refreshed: 6
  };

  const activeIndexByStage: Record<PipelineStage, number> = {
    idle: -1,
    codex_ready: 2,
    codex_working: 3,
    github_deploying: 4,
    refresh_pending: 6,
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

function buildBuilderSummary(data: Record<string, unknown>) {
  const createdFiles = Array.isArray(data.created_files) ? data.created_files : [];

  return [
    `Message: ${String(data.message ?? "Builder Core responded.")}`,
    `Project: ${String(data.project_name ?? "Unknown project")}`,
    `Module Key: ${String(data.module_key ?? "n/a")}`,
    `Title: ${String(data.title ?? "n/a")}`,
    `Route Path: ${String(data.route_path ?? "n/a")}`,
    "",
    "Created Files:",
    createdFiles.length > 0 ? "- " + createdFiles.join("\n- ") : "- No files generated for this request."
  ].join("\n");
}

function buildRunSummary(data: Record<string, unknown>) {
  const commands = Array.isArray(data.commands) ? data.commands : [];

  return [
    "Run Instructions",
    `Project: ${String(data.project_name ?? "Unknown project")}`,
    `Path: ${String(data.project_path ?? "n/a")}`,
    `Run Script: ${String(data.run_script ?? "n/a")}`,
    `URL Hint: ${String(data.url_hint ?? "n/a")}`,
    "",
    "Commands:",
    commands.length > 0 ? String(commands.join("\n")) : "No run commands returned."
  ].join("\n");
}

function buildReviewSummary(task: CommandTask | null, backendState: "checking" | "online" | "offline"): ReviewSummary {
  const hasBuilderSummary = Boolean(task?.builderSummary);
  const backendHealthy = backendState === "online";

  const checklist: ReviewChecklistItem[] = [
    {
      label: "Files changed?",
      status: hasBuilderSummary ? "ready" : "attention",
      detail: hasBuilderSummary ? "Builder Core returned a change summary for this task." : "Confirm the exact files changed before approving the rollout."
    },
    {
      label: "Build passed?",
      status: "ready",
      detail: "This manual simulation assumes the build passed before deployment completed."
    },
    {
      label: "GitHub Actions green?",
      status: "ready",
      detail: "This manual simulation treats the deploy step as a successful GitHub Actions run."
    },
    {
      label: "Frontend live?",
      status: "ready",
      detail: "The Cloud Run live step is complete in the current simulation."
    },
    {
      label: "Backend online?",
      status: backendHealthy ? "ready" : "attention",
      detail: backendHealthy ? "The in-app backend health indicator is online." : "Recheck /system/status before calling this task done."
    }
  ];

  return {
    checklist,
    doItems: [
      "Prefer safe improvements and small upgrades after the deploy.",
      "Open the live app and verify the user-visible change immediately.",
      "Capture the files changed and testing notes before starting the next task."
    ],
    avoidItems: [
      "Do not stack risky changes on top of an unverified deploy.",
      "Do not remove working features to make a fix easier.",
      "Do not assume the backend is healthy if the status badge is offline."
    ]
  };
}

function renderTextBubble(entry: ChatEntry) {
  const isUser = entry.role === "user";

  return (
    <div key={entry.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-3xl rounded-3xl bg-black px-5 py-4 text-white shadow-sm"
            : "max-w-3xl rounded-3xl border border-gray-200 bg-white px-5 py-4 text-black shadow-sm"
        }
      >
        {entry.title && (
          <p className={`mb-2 text-xs font-semibold uppercase tracking-wide ${isUser ? "text-white/70" : "text-gray-500"}`}>
            {entry.title}
          </p>
        )}
        <p className="whitespace-pre-wrap text-sm leading-6">{entry.content}</p>
        <p className={`mt-3 text-xs ${isUser ? "text-white/70" : "text-gray-400"}`}>{entry.timestamp}</p>
      </div>
    </div>
  );
}

function renderStructuredBubble(entry: ChatEntry) {
  if (entry.kind === "review" && entry.review) {
    return (
      <div key={entry.id} className="flex justify-start">
        <div className="max-w-4xl rounded-3xl border border-gray-200 bg-white px-5 py-5 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{entry.title}</p>
          <div className="space-y-3">
            {entry.review.checklist.map((item) => (
              <div key={item.label} className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="font-semibold text-gray-900">{item.label}</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${getReviewBadgeClass(item.status)}`}>
                    {item.status === "ready" ? "Looks good" : "Check this"}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{item.detail}</p>
              </div>
            ))}
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-green-200 bg-green-50 p-4">
              <p className="mb-3 font-semibold text-green-900">Suggestions: Do</p>
              <ul className="list-disc space-y-2 pl-5 text-sm text-green-900">
                {entry.review.doItems.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
              <p className="mb-3 font-semibold text-amber-900">Suggestions: Do Not</p>
              <ul className="list-disc space-y-2 pl-5 text-sm text-amber-900">
                {entry.review.avoidItems.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          <p className="mt-4 text-xs text-gray-400">{entry.timestamp}</p>
        </div>
      </div>
    );
  }

  return (
    <div key={entry.id} className="flex justify-start">
      <div className="max-w-4xl rounded-3xl border border-gray-200 bg-white px-5 py-5 shadow-sm">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{entry.title}</p>
        <pre className="whitespace-pre-wrap text-sm leading-6 text-gray-800">{entry.content}</pre>
        <p className="mt-4 text-xs text-gray-400">{entry.timestamp}</p>
      </div>
    </div>
  );
}

export default function Home() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProject, setSelectedProject] = useState("Default Project");
  const [newProjectName, setNewProjectName] = useState("");
  const [commandInput, setCommandInput] = useState("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>("idle");
  const [pipelineStage, setPipelineStage] = useState<PipelineStage>("idle");
  const [refreshCountdown, setRefreshCountdown] = useState<number | null>(null);
  const [installMessage, setInstallMessage] = useState("");
  const [lastTask, setLastTask] = useState<CommandTask | null>(null);
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([
    {
      id: "welcome",
      role: "assistant",
      kind: "text",
      title: "Builder Core",
      content:
        "Ask Builder Core to build, fix, or upgrade anything. I will plan the work, prepare the Codex task, keep the pipeline visible, and show review suggestions inline.",
      timestamp: "Ready"
    }
  ]);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const automationPipeline = useMemo(() => buildAutomationPipeline(pipelineStage), [pipelineStage]);
  const completedPipelineSteps = automationPipeline.filter((step) => step.status === "done").length;
  const pipelineProgress = Math.round((completedPipelineSteps / automationPipeline.length) * 100);

  const canSendToCodex = pipelineStage === "codex_ready";
  const canMarkCodexDone = pipelineStage === "codex_working";
  const canMarkDeployDone = pipelineStage === "github_deploying";
  const canRefreshNow = pipelineStage === "refresh_pending";

  function appendChatEntries(entries: Array<Omit<ChatEntry, "id" | "timestamp">>) {
    const base = Date.now();

    setChatEntries((current) =>
      current.concat(
        entries.map((entry, index) => ({
          ...entry,
          id: `${base}-${index}-${Math.random().toString(16).slice(2)}`,
          timestamp: formatTimestamp(new Date(base + index))
        }))
      )
    );
  }

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

      if (items.length > 0 && !items.find((project: ProjectItem) => project.name === selectedProject)) {
        setSelectedProject(items[0].name);
      }
    } catch {
      console.log("Could not load projects");
    }
  }

  useEffect(() => {
    checkBackendStatus();
    loadProjects();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatEntries, pipelineStage, refreshCountdown]);

  function finishRefresh() {
    setExecutionStatus("completed");
    setPipelineStage("refreshed");
    setRefreshCountdown(null);

    window.setTimeout(() => {
      window.location.reload();
    }, 300);
  }

  useEffect(() => {
    if (pipelineStage !== "refresh_pending" || refreshCountdown === null) {
      return;
    }

    if (refreshCountdown === 0) {
      finishRefresh();
      return;
    }

    const timer = window.setTimeout(() => {
      setRefreshCountdown((current) => (current === null ? null : current - 1));
    }, 1000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [pipelineStage, refreshCountdown]);

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
        appendChatEntries([
          {
            role: "assistant",
            kind: "text",
            title: "Project Ready",
            content: `Created project "${data.project.name}". Future commands will use this project.`
          }
        ]);
      }
    } catch {
      appendChatEntries([
        {
          role: "assistant",
          kind: "text",
          title: "Project Update",
          content: "I could not create the project right now. Please try again."
        }
      ]);
    }
  }

  async function handleCommandSubmit() {
    const instruction = commandInput.trim();

    if (!instruction) {
      return;
    }

    const planner = buildPlannerOutput(instruction, selectedProject);
    const prompt = buildCodexPrompt(instruction, selectedProject);
    const nextTask: CommandTask = {
      instruction,
      planner,
      prompt,
      timestamp: formatTimestamp(new Date())
    };

    setCommandInput("");
    setExecutionStatus("prepared");
    setPipelineStage("codex_ready");
    setRefreshCountdown(null);
    setLastTask(nextTask);

    appendChatEntries([
      {
        role: "user",
        kind: "text",
        content: instruction
      },
      {
        role: "assistant",
        kind: "text",
        title: "System",
        content: "Planning..."
      },
      {
        role: "assistant",
        kind: "planner",
        title: "ChatGPT Planner",
        content: planner
      },
      {
        role: "assistant",
        kind: "text",
        title: "System",
        content: "Preparing Codex task..."
      },
      {
        role: "assistant",
        kind: "codex",
        title: "Codex Task",
        content: prompt
      }
    ]);

    try {
      const response = await fetch(`${API_BASE}/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          instruction,
          project_name: selectedProject
        })
      });

      const data = await response.json();

      if (!data.ok) {
        appendChatEntries([
          {
            role: "assistant",
            kind: "text",
            title: "Builder Core",
            content: data.message || "Builder Core could not complete the request."
          }
        ]);
        return;
      }

      const builderSummary = buildBuilderSummary(data);
      setLastTask((current) => (current ? { ...current, builderSummary } : current));

      appendChatEntries([
        {
          role: "assistant",
          kind: "builder",
          title: "Builder Core Response",
          content: builderSummary
        }
      ]);

      try {
        const runInfoResponse = await fetch(`${API_BASE}/run-info?project_name=${encodeURIComponent(selectedProject)}`);

        if (runInfoResponse.ok) {
          const runInfoData = await runInfoResponse.json();
          appendChatEntries([
            {
              role: "assistant",
              kind: "builder",
              title: "Run Instructions",
              content: buildRunSummary(runInfoData)
            }
          ]);
        }
      } catch {
        console.log("Could not load run info");
      }
    } catch {
      appendChatEntries([
        {
          role: "assistant",
          kind: "text",
          title: "Builder Core",
          content: "The backend request could not complete, but the plan and Codex task are still ready."
        }
      ]);
    }
  }

  function handleSendToCodex() {
    if (!lastTask || pipelineStage !== "codex_ready") {
      return;
    }

    setExecutionStatus("sent");
    setPipelineStage("codex_working");

    appendChatEntries([
      {
        role: "assistant",
        kind: "text",
        title: "Automation",
        content: "Codex task sent. Codex Working is now active."
      }
    ]);
  }

  function handleMarkCodexDone() {
    if (!lastTask || pipelineStage !== "codex_working") {
      return;
    }

    setPipelineStage("github_deploying");

    appendChatEntries([
      {
        role: "assistant",
        kind: "text",
        title: "Automation",
        content: "Codex work marked done. GitHub Deploying is now active."
      }
    ]);
  }

  function handleMarkDeployDone() {
    if (!lastTask || pipelineStage !== "github_deploying") {
      return;
    }

    const review = buildReviewSummary(lastTask, backendStatus);

    setPipelineStage("refresh_pending");
    setRefreshCountdown(5);

    appendChatEntries([
      {
        role: "assistant",
        kind: "text",
        title: "Automation",
        content: "Cloud Run is live. App refresh is queued. Currently simulated. Full automation coming."
      },
      {
        role: "assistant",
        kind: "review",
        title: "Codex Result Review",
        review
      }
    ]);
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
      setInstallMessage("Copy failed. Copy the link manually from the app URL.");
    }
  }

  const automationStatusLabel = getAutomationStatusLabel(pipelineStage, refreshCountdown);

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="flex flex-col gap-4 px-4 py-4 sm:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="text-2xl font-bold sm:text-3xl">Builder Core</h1>
                <p className="text-sm text-slate-600">
                  One unified AI Command Center for planning, Codex tasks, pipeline tracking, deploy review, and cloud-first operation.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <span
                  className={
                    backendStatus === "online"
                      ? "rounded-full border border-green-200 bg-green-100 px-3 py-1 text-sm font-medium text-green-700"
                      : backendStatus === "offline"
                        ? "rounded-full border border-red-200 bg-red-100 px-3 py-1 text-sm font-medium text-red-700"
                        : "rounded-full border border-gray-200 bg-gray-100 px-3 py-1 text-sm font-medium text-gray-600"
                  }
                >
                  {backendStatus === "checking" && "Backend: Checking..."}
                  {backendStatus === "online" && "Backend: Online"}
                  {backendStatus === "offline" && "Backend: Offline"}
                </span>

                <span className="rounded-full border border-amber-200 bg-amber-100 px-3 py-1 text-sm font-medium text-amber-700">
                  Automation: {automationStatusLabel}
                </span>
              </div>
            </div>

            <div className="grid gap-3 rounded-3xl border border-slate-200 bg-slate-50 p-3 sm:p-4 lg:grid-cols-[1fr,1fr,auto,auto]">
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
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

              <input
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Create a new project"
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
              />

              <button
                type="button"
                onClick={handleCreateProject}
                className="w-full rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white lg:w-auto"
              >
                Create Project
              </button>

              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                <p><span className="font-medium text-slate-900">Execution:</span> {getExecutionStatusLabel(executionStatus)}</p>
                {lastTask && (
                  <p className="mt-1"><span className="font-medium text-slate-900">Last task:</span> {lastTask.timestamp}</p>
                )}
              </div>
            </div>
          </div>
        </header>

        <div className="flex-1 px-4 py-4 sm:px-6">
          <section className="rounded-[28px] border border-slate-200 bg-white shadow-sm">
            <div className="min-h-[440px] max-h-[calc(100vh-340px)] overflow-y-auto p-4 sm:p-6">
              <div className="space-y-4">
                {chatEntries.map((entry) =>
                  entry.kind === "text" ? renderTextBubble(entry) : renderStructuredBubble(entry)
                )}
                <div ref={bottomRef} />
              </div>
            </div>

            <div className="border-t border-slate-200 p-4 sm:p-6">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
                <textarea
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  placeholder="Ask Builder Core to build, fix, or upgrade anything..."
                  className="h-32 w-full resize-none rounded-2xl border border-slate-200 bg-white p-4 text-sm"
                />

                <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs text-slate-500">
                    One command now handles planning, Codex task prep, backend request flow, deploy tracking, and inline review.
                  </p>

                  <button
                    type="button"
                    onClick={handleCommandSubmit}
                    className="w-full rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white sm:w-auto"
                  >
                    Run Command
                  </button>
                </div>
              </div>

              <details className="mt-4 rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <summary className="cursor-pointer text-sm font-semibold text-slate-900">
                  Download / Install
                </summary>

                <div className="mt-4 grid gap-4 lg:grid-cols-[1fr,1fr]">
                  <div className="space-y-4 text-sm text-slate-700">
                    <div>
                      <p className="mb-2 font-semibold text-slate-900">iPhone</p>
                      <ul className="list-disc space-y-1 pl-5">
                        <li>Open the app in Safari.</li>
                        <li>Tap Share.</li>
                        <li>Add to Home Screen.</li>
                      </ul>
                    </div>

                    <div>
                      <p className="mb-2 font-semibold text-slate-900">Android</p>
                      <ul className="list-disc space-y-1 pl-5">
                        <li>Open the app in Chrome.</li>
                        <li>Tap the menu icon.</li>
                        <li>Install App.</li>
                      </ul>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                      <p className="mb-2 font-semibold text-slate-900">App Link</p>
                      <p>{FRONTEND_APP_URL}</p>
                      <p className="mt-2 text-xs text-slate-500">No App Store needed.</p>
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row">
                      <button
                        type="button"
                        onClick={handleOpenAppLink}
                        className="w-full rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white sm:w-auto"
                      >
                        Open App Link
                      </button>
                      <button
                        type="button"
                        onClick={handleCopyAppLink}
                        className="w-full rounded-2xl border border-black px-5 py-3 text-sm font-medium text-black sm:w-auto"
                      >
                        Copy Link
                      </button>
                    </div>

                    {installMessage && (
                      <p className="text-sm text-slate-600">{installMessage}</p>
                    )}
                  </div>
                </div>
              </details>
            </div>
          </section>
        </div>

        {lastTask && (
          <div className="fixed bottom-4 left-4 right-4 z-20 lg:left-auto lg:right-6 lg:w-[430px]">
            <div className="rounded-[28px] border border-slate-200 bg-white/95 p-4 shadow-2xl backdrop-blur">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-900">Automation Pipeline</p>
                  <p className="text-xs text-slate-500">Currently simulated. Full automation coming.</p>
                </div>
                <span className="rounded-full border border-amber-200 bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
                  {automationStatusLabel}
                </span>
              </div>

              <div className="mb-3 flex items-center justify-between text-xs font-medium text-slate-500">
                <span>Progress</span>
                <span>{pipelineProgress}%</span>
              </div>
              <div className="mb-4 h-2 rounded-full bg-slate-200">
                <div
                  className="h-2 rounded-full bg-blue-600 transition-all"
                  style={{ width: `${pipelineProgress}%` }}
                />
              </div>

              {refreshCountdown !== null && (
                <p className="mb-4 text-sm text-slate-600">
                  Auto-refresh in {refreshCountdown}s
                </p>
              )}

              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <button
                  type="button"
                  onClick={handleSendToCodex}
                  disabled={!canSendToCodex}
                  className={
                    canSendToCodex
                      ? "w-full rounded-2xl bg-blue-600 px-4 py-3 text-sm font-medium text-white sm:w-auto"
                      : "w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-400 sm:w-auto"
                  }
                >
                  Send to Codex
                </button>
                <button
                  type="button"
                  onClick={handleMarkCodexDone}
                  disabled={!canMarkCodexDone}
                  className={
                    canMarkCodexDone
                      ? "w-full rounded-2xl border border-black px-4 py-3 text-sm font-medium text-black sm:w-auto"
                      : "w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-400 sm:w-auto"
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
                      ? "w-full rounded-2xl border border-black px-4 py-3 text-sm font-medium text-black sm:w-auto"
                      : "w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-400 sm:w-auto"
                  }
                >
                  Mark Deploy Done
                </button>
                <button
                  type="button"
                  onClick={finishRefresh}
                  disabled={!canRefreshNow}
                  className={
                    canRefreshNow
                      ? "w-full rounded-2xl bg-black px-4 py-3 text-sm font-medium text-white sm:w-auto"
                      : "w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-400 sm:w-auto"
                  }
                >
                  Refresh Now
                </button>
              </div>

              <div className="space-y-3">
                {automationPipeline.map((step, index) => (
                  <div key={step.key} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className={`h-3 w-3 rounded-full ${getPipelineDotClass(step.status)}`} />
                        <p className="font-medium text-slate-900">
                          {index + 1}. {step.label}
                        </p>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${getPipelineStatusBadgeClass(step.status)}`}>
                        {step.status === "pending" && "Pending"}
                        {step.status === "active" && "Active"}
                        {step.status === "done" && "Done"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{step.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
