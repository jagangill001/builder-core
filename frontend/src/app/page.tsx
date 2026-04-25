"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const FRONTEND_APP_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";

const COMMAND_CENTER_TABS = [
  { key: "command", label: "Command" },
  { key: "progress", label: "Progress" },
  { key: "review", label: "Review" },
  { key: "download", label: "Download" },
  { key: "help", label: "Help" }
] as const;

const PIPELINE_STEP_DEFINITIONS = [
  {
    key: "task_received",
    label: "Task Received",
    description: "Builder Core accepted the instruction and opened the task.",
    percent: 15,
    currentText: "Your command was accepted.",
    nextText: "Next: Builder Core will create a safe plan for the task."
  },
  {
    key: "planning",
    label: "Planning",
    description: "The planner organized the work, risks, and testing approach.",
    percent: 30,
    currentText: "Builder Core is creating a safe plan.",
    nextText: "Next: a Codex task will be prepared after the plan is ready."
  },
  {
    key: "codex_ready",
    label: "Codex Ready",
    description: "The Codex-ready task is prepared and waiting to be sent.",
    percent: 45,
    currentText: "A Codex task is ready.",
    nextText: "Next: Codex will start after you send the task."
  },
  {
    key: "codex_working",
    label: "Codex Working",
    description: "Codex is working through the requested change.",
    percent: 60,
    currentText: "Codex is expected to make code changes.",
    nextText: "Next: GitHub deploy will start after Codex finishes."
  },
  {
    key: "github_deploying",
    label: "GitHub Deploying",
    description: "GitHub Actions is building and deploying the latest revision.",
    percent: 75,
    currentText: "GitHub Actions is deploying the update.",
    nextText: "Next: Cloud Run will go live after deployment finishes."
  },
  {
    key: "cloud_run_live",
    label: "Cloud Run Live",
    description: "The new Cloud Run revision is live.",
    percent: 90,
    currentText: "New Cloud Run version is live.",
    nextText: "Next: refresh the app to load the newest version."
  },
  {
    key: "app_refreshed",
    label: "App Refreshed",
    description: "The app reloaded and is showing the latest state.",
    percent: 100,
    currentText: "App is refreshed and ready.",
    nextText: "Next: enter another command when you are ready."
  }
] as const;

type ProjectItem = {
  id: number;
  name: string;
};

type CommandCenterTabKey = "command" | "progress" | "review" | "download" | "help";
type ProgressChecklistKey =
  | "codex_finished"
  | "codex_commit_hash"
  | "codex_summary"
  | "deploy_actions_green"
  | "deploy_cloud_run_finished"
  | "deploy_backend_online"
  | "refresh_deploy_done"
  | "refresh_ready";

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
  percent: number;
  currentText: string;
  nextText: string;
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

type CommandCenterChatResponse = Record<string, unknown> & {
  ok?: boolean;
  message?: string;
  assistant_reply?: string;
  project_name?: string;
  intent?: string;
  plan?: string[];
  risks?: string[];
  testing_plan?: string[];
  next_steps?: string[];
  codex_prompt?: string;
  build_triggered?: boolean;
  run_info?: Record<string, unknown>;
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

function buildPlannerSummary(
  instruction: string,
  projectName: string,
  data: CommandCenterChatResponse,
  fallbackPlanner: string
) {
  const plan = Array.isArray(data.plan) ? data.plan : [];
  const risks = Array.isArray(data.risks) ? data.risks : [];
  const testingPlan = Array.isArray(data.testing_plan) ? data.testing_plan : [];
  const intent = typeof data.intent === "string" && data.intent ? data.intent : "build";
  const resolvedProjectName =
    typeof data.project_name === "string" && data.project_name ? data.project_name : projectName;

  if (plan.length === 0 && risks.length === 0 && testingPlan.length === 0) {
    return fallbackPlanner;
  }

  return [
    "ChatGPT Planner",
    `Project: ${resolvedProjectName}`,
    `Instruction: ${instruction}`,
    `Intent: ${intent}`,
    "",
    "Step-by-step plan:",
    ...(plan.length > 0
      ? plan.map((step, index) => `${index + 1}. ${step}`)
      : ["1. Review the request and choose the next safe step."]),
    "",
    "Risks:",
    ...(risks.length > 0 ? risks.map((risk) => `- ${risk}`) : ["- No risks were returned by the backend."]),
    "",
    "Testing plan:",
    ...(testingPlan.length > 0
      ? testingPlan.map((step) => `- ${step}`)
      : ["- Confirm the request outcome manually after the reply."])
  ].join("\n");
}

function buildNextStepsSummary(nextSteps: unknown) {
  if (!Array.isArray(nextSteps) || nextSteps.length === 0) {
    return "";
  }

  return [
    "Next Steps",
    ...nextSteps.map((step) => `- ${String(step)}`)
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
    refresh_pending: 4,
    refreshed: 6
  };

  const activeIndexByStage: Record<PipelineStage, number> = {
    idle: -1,
    codex_ready: 2,
    codex_working: 3,
    github_deploying: 4,
    refresh_pending: 5,
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

function getCurrentPipelineStep(steps: PipelineStep[], stage: PipelineStage) {
  const activeStep = steps.find((step) => step.status === "active");
  if (activeStep) {
    return activeStep;
  }

  if (stage === "refreshed") {
    return steps[steps.length - 1] ?? null;
  }

  for (let index = steps.length - 1; index >= 0; index -= 1) {
    if (steps[index].status === "done") {
      return steps[index];
    }
  }

  return null;
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

function getPipelineCardClass(status: PipelineStepStatus) {
  if (status === "active") {
    return "rounded-3xl border-2 border-blue-200 bg-blue-50 p-4 shadow-sm";
  }

  if (status === "done") {
    return "rounded-2xl border border-green-200 bg-green-50/80 p-3";
  }

  return "rounded-2xl border border-slate-100 bg-slate-50/80 p-2.5 opacity-65";
}

function getPipelineTitleClass(status: PipelineStepStatus) {
  if (status === "active") {
    return "text-base font-semibold text-slate-900";
  }

  if (status === "done") {
    return "text-sm font-medium text-slate-900";
  }

  return "text-sm font-medium text-slate-500";
}

function getPipelineDescriptionClass(status: PipelineStepStatus) {
  if (status === "active") {
    return "text-sm text-slate-700";
  }

  if (status === "done") {
    return "text-xs text-slate-600";
  }

  return "text-xs text-slate-400";
}

function getTabButtonClass(isActive: boolean) {
  if (isActive) {
    return "rounded-2xl bg-black px-4 py-3 text-sm font-semibold text-white shadow-sm";
  }

  return "rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600";
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

function renderReviewContent(review: ReviewSummary) {
  return (
    <>
      <div className="space-y-3">
        {review.checklist.map((item) => (
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
            {review.doItems.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="mb-3 font-semibold text-amber-900">Suggestions: Do Not</p>
          <ul className="list-disc space-y-2 pl-5 text-sm text-amber-900">
            {review.avoidItems.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
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
          {renderReviewContent(entry.review)}

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
  const [activeTab, setActiveTab] = useState<CommandCenterTabKey>("command");
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
  const [progressChecklist, setProgressChecklist] = useState<Record<ProgressChecklistKey, boolean>>({
    codex_finished: false,
    codex_commit_hash: false,
    codex_summary: false,
    deploy_actions_green: false,
    deploy_cloud_run_finished: false,
    deploy_backend_online: false,
    refresh_deploy_done: false,
    refresh_ready: false
  });

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const sectionRefs = useRef<Partial<Record<CommandCenterTabKey, HTMLElement | null>>>({});

  const automationPipeline = useMemo(() => buildAutomationPipeline(pipelineStage), [pipelineStage]);
  const currentPipelineStep = useMemo(
    () => getCurrentPipelineStep(automationPipeline, pipelineStage),
    [automationPipeline, pipelineStage]
  );
  const latestReview = useMemo(() => buildReviewSummary(lastTask, backendStatus), [lastTask, backendStatus]);
  const pipelineProgress = currentPipelineStep?.percent ?? 0;
  const pipelineProgressText = currentPipelineStep
    ? `${pipelineProgress}% complete — ${currentPipelineStep.currentText}`
    : "0% complete — Waiting for your next task";
  const pipelineCurrentText = currentPipelineStep?.currentText ?? "Waiting for your next command.";
  const pipelineNextStepText =
    currentPipelineStep?.nextText ?? "Next: enter a command to start the automation pipeline.";

  const canSendToCodex = pipelineStage === "codex_ready";
  const canMarkCodexDone = pipelineStage === "codex_working";
  const canMarkDeployDone = pipelineStage === "github_deploying";
  const canRefreshNow = pipelineStage === "refresh_pending";

  function setSectionRef(key: CommandCenterTabKey) {
    return (element: HTMLElement | null) => {
      sectionRefs.current[key] = element;
    };
  }

  function scrollToSection(key: CommandCenterTabKey) {
    setActiveTab(key);
    sectionRefs.current[key]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function toggleProgressChecklistItem(key: ProgressChecklistKey) {
    setProgressChecklist((current) => ({
      ...current,
      [key]: !current[key]
    }));
  }

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
    const sections = Object.entries(sectionRefs.current).filter((entry): entry is [CommandCenterTabKey, HTMLElement] => Boolean(entry[1]));
    if (sections.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntries = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio);

        const activeEntry = visibleEntries[0];
        if (!activeEntry) {
          return;
        }

        const key = activeEntry.target.getAttribute("data-section-key") as CommandCenterTabKey | null;
        if (key) {
          setActiveTab(key);
        }
      },
      {
        rootMargin: "-20% 0px -50% 0px",
        threshold: [0.2, 0.45, 0.7]
      }
    );

    for (const [, element] of sections) {
      observer.observe(element);
    }

    return () => {
      observer.disconnect();
    };
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

    const fallbackPlanner = buildPlannerOutput(instruction, selectedProject);
    const fallbackPrompt = buildCodexPrompt(instruction, selectedProject);

    setCommandInput("");
    setRefreshCountdown(null);

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
      }
    ]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          instruction,
          project_name: selectedProject
        })
      });

      const data = (await response.json()) as CommandCenterChatResponse;

      if (!response.ok || !data.ok) {
        appendChatEntries([
          {
            role: "assistant",
            kind: "text",
            title: "Builder Core",
            content:
              (typeof data.assistant_reply === "string" && data.assistant_reply) ||
              (typeof data.message === "string" && data.message) ||
              "Builder Core could not complete that chat request."
          }
        ]);
        return;
      }

      const planner = buildPlannerSummary(instruction, selectedProject, data, fallbackPlanner);
      const prompt =
        typeof data.codex_prompt === "string" && data.codex_prompt.trim()
          ? data.codex_prompt
          : fallbackPrompt;
      const nextStepsSummary = buildNextStepsSummary(data.next_steps);
      const builderSummary = data.build_triggered ? buildBuilderSummary(data) : null;
      const nextTask: CommandTask = {
        instruction,
        planner,
        prompt,
        timestamp: formatTimestamp(new Date()),
        builderSummary
      };

      setExecutionStatus("prepared");
      setPipelineStage("codex_ready");
      setLastTask(nextTask);

      const responseEntries: Array<Omit<ChatEntry, "id" | "timestamp">> = [
        {
          role: "assistant",
          kind: "text",
          title: "Builder Core",
          content:
            (typeof data.assistant_reply === "string" && data.assistant_reply) ||
            "I planned the request and prepared the next steps."
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
      ];

      if (builderSummary) {
        responseEntries.push({
          role: "assistant",
          kind: "builder",
          title: "Builder Core Response",
          content: builderSummary
        });
      }

      if (nextStepsSummary) {
        responseEntries.push({
          role: "assistant",
          kind: "builder",
          title: "Suggestions / Next Steps",
          content: nextStepsSummary
        });
      }

      if (data.run_info && typeof data.run_info === "object") {
        responseEntries.push({
          role: "assistant",
          kind: "builder",
          title: "Run Instructions",
          content: buildRunSummary(data.run_info)
        });
      }

      appendChatEntries(responseEntries);
    } catch {
      setExecutionStatus("idle");
      setPipelineStage("idle");
      setRefreshCountdown(null);

      appendChatEntries([
        {
          role: "assistant",
          kind: "text",
          title: "Builder Core",
          content: "I could not reach the backend chat service right now. Check the backend status, then try the command again."
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

        <div className="flex-1 px-4 py-4 pb-28 sm:px-6 lg:pb-6">
          <div className="lg:grid lg:grid-cols-[250px,minmax(0,1fr)] lg:gap-6">
            <aside className="mb-6 hidden lg:block">
              <div className="sticky top-28 space-y-4">
                <div className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Navigation</p>
                  <div className="mt-3 space-y-2">
                    {COMMAND_CENTER_TABS.map((tab) => (
                      <button
                        key={tab.key}
                        type="button"
                        onClick={() => scrollToSection(tab.key)}
                        className={`w-full text-left ${getTabButtonClass(activeTab === tab.key)}`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Quick Actions</p>
                  <div className="mt-3 space-y-2">
                    <button
                      type="button"
                      onClick={() => scrollToSection("download")}
                      className="w-full rounded-2xl bg-black px-4 py-3 text-left text-sm font-semibold text-white"
                    >
                      Install on Phone
                    </button>
                    <button
                      type="button"
                      onClick={handleCopyAppLink}
                      className="w-full rounded-2xl border border-black px-4 py-3 text-left text-sm font-semibold text-black"
                    >
                      Copy App Link
                    </button>
                  </div>
                  {installMessage && (
                    <p className="mt-3 text-sm text-slate-600">{installMessage}</p>
                  )}
                </div>
              </div>
            </aside>

            <div className="space-y-6">
              <section
                ref={setSectionRef("command")}
                data-section-key="command"
                className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white shadow-sm"
              >
                <div className="border-b border-slate-200 px-4 py-4 sm:px-6">
                  <p className="text-lg font-semibold text-slate-900">Command</p>
                  <p className="text-sm text-slate-600">
                    Chat with Builder Core, get the backend response, and prepare the next safe task.
                  </p>
                </div>

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
                </div>
              </section>

              <section
                ref={setSectionRef("progress")}
                data-section-key="progress"
                className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
              >
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-lg font-semibold text-slate-900">Progress</p>
                    <p className="text-sm text-slate-600">
                      Watch the automation stages, then use the manual buttons only when the matching checklist is satisfied.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleSendToCodex}
                    disabled={!canSendToCodex}
                    className={
                      canSendToCodex
                        ? "w-full rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white sm:w-auto"
                        : "w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400 sm:w-auto"
                    }
                  >
                    Send to Codex
                  </button>
                </div>

                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <div className="mb-3 flex items-center justify-between text-sm font-semibold text-slate-700">
                    <span>Progress</span>
                    <span>{pipelineProgress}%</span>
                  </div>
                  <div className="mb-3 h-4 rounded-full bg-slate-200">
                    <div
                      className="h-4 rounded-full bg-blue-600 transition-all"
                      style={{ width: `${pipelineProgress}%` }}
                    />
                  </div>
                  <p className="text-sm font-semibold text-slate-900">{pipelineProgressText}</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">What is happening now</p>
                      <p className="mt-2 text-sm font-medium text-slate-900">{pipelineCurrentText}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Next step</p>
                      <p className="mt-2 text-sm font-medium text-slate-900">{pipelineNextStepText}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 xl:grid-cols-3">
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">Mark Codex Done</p>
                        <p className="text-sm text-slate-600">Click this only when the coding pass is clearly complete.</p>
                      </div>
                      <button
                        type="button"
                        onClick={handleMarkCodexDone}
                        disabled={!canMarkCodexDone}
                        className={
                          canMarkCodexDone
                            ? "rounded-xl border border-black px-3 py-2 text-xs font-semibold text-black"
                            : "rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400"
                        }
                      >
                        Mark Codex Done
                      </button>
                    </div>

                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Before Mark Codex Done</p>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.codex_finished}
                          onChange={() => toggleProgressChecklistItem("codex_finished")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Codex finished
                      </label>
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.codex_commit_hash}
                          onChange={() => toggleProgressChecklistItem("codex_commit_hash")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Commit hash received
                      </label>
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.codex_summary}
                          onChange={() => toggleProgressChecklistItem("codex_summary")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Files changed summary received
                      </label>
                    </div>

                    <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
                      <li>Codex says it committed changes.</li>
                      <li>Codex gives a commit hash.</li>
                      <li>Codex summary says files changed.</li>
                      <li>GitHub repo shows the new commit.</li>
                    </ul>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">Mark Deploy Done</p>
                        <p className="text-sm text-slate-600">Use this only after GitHub and Cloud Run both finish cleanly.</p>
                      </div>
                      <button
                        type="button"
                        onClick={handleMarkDeployDone}
                        disabled={!canMarkDeployDone}
                        className={
                          canMarkDeployDone
                            ? "rounded-xl border border-black px-3 py-2 text-xs font-semibold text-black"
                            : "rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400"
                        }
                      >
                        Mark Deploy Done
                      </button>
                    </div>

                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Before Mark Deploy Done</p>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.deploy_actions_green}
                          onChange={() => toggleProgressChecklistItem("deploy_actions_green")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        GitHub Actions green
                      </label>
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.deploy_cloud_run_finished}
                          onChange={() => toggleProgressChecklistItem("deploy_cloud_run_finished")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Cloud Run deploy finished
                      </label>
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.deploy_backend_online || backendStatus === "online"}
                          onChange={() => toggleProgressChecklistItem("deploy_backend_online")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Backend health still online
                      </label>
                    </div>

                    <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
                      <li>GitHub Actions is green.</li>
                      <li>Cloud Run revision finished deploying.</li>
                      <li>Frontend/backend service is live.</li>
                    </ul>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">Refresh App</p>
                        <p className="text-sm text-slate-600">Reload only after the newest version is actually live.</p>
                      </div>
                      <button
                        type="button"
                        onClick={finishRefresh}
                        disabled={!canRefreshNow}
                        className={
                          canRefreshNow
                            ? "rounded-xl bg-black px-3 py-2 text-xs font-semibold text-white"
                            : "rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400"
                        }
                      >
                        Refresh Now
                      </button>
                    </div>

                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Before Refresh</p>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.refresh_deploy_done}
                          onChange={() => toggleProgressChecklistItem("refresh_deploy_done")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Deploy done
                      </label>
                      <label className="flex items-center gap-3 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={progressChecklist.refresh_ready}
                          onChange={() => toggleProgressChecklistItem("refresh_ready")}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        App ready to reload
                      </label>
                    </div>

                    <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
                      <li>Deploy is done.</li>
                      <li>You want to load the newest version.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <section
                ref={setSectionRef("review")}
                data-section-key="review"
                className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
              >
                <div className="mb-4">
                  <p className="text-lg font-semibold text-slate-900">Review</p>
                  <p className="text-sm text-slate-600">
                    Check the latest task result here before you trust the deploy and move on to the next upgrade.
                  </p>
                </div>

                {lastTask ? (
                  <>
                    <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                      <p><span className="font-semibold text-slate-900">Latest task:</span> {lastTask.instruction}</p>
                      <p className="mt-1"><span className="font-semibold text-slate-900">Recorded:</span> {lastTask.timestamp}</p>
                    </div>
                    {renderReviewContent(latestReview)}
                  </>
                ) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    Run a command first. After Builder Core responds and the pipeline advances, review guidance will appear here.
                  </div>
                )}
              </section>

              <section
                ref={setSectionRef("download")}
                data-section-key="download"
                className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
              >
                <div className="mb-4">
                  <p className="text-lg font-semibold text-slate-900">Download</p>
                  <p className="text-sm text-slate-600">
                    Keep the app install steps easy to reach from every area of Builder Core.
                  </p>
                </div>

                <div className="grid gap-4 lg:grid-cols-[1fr,1fr]">
                  <div className="space-y-4 text-sm text-slate-700">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="mb-2 font-semibold text-slate-900">iPhone</p>
                      <ul className="list-disc space-y-1 pl-5">
                        <li>Open the app in Safari.</li>
                        <li>Tap Share.</li>
                        <li>Add to Home Screen.</li>
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="mb-2 font-semibold text-slate-900">Android</p>
                      <ul className="list-disc space-y-1 pl-5">
                        <li>Open the app in Chrome.</li>
                        <li>Tap the menu icon.</li>
                        <li>Install App.</li>
                      </ul>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
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
                        Copy App Link
                      </button>
                    </div>

                    {installMessage && (
                      <p className="text-sm text-slate-600">{installMessage}</p>
                    )}
                  </div>
                </div>
              </section>

              <section
                ref={setSectionRef("help")}
                data-section-key="help"
                className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
              >
                <div className="mb-4">
                  <p className="text-lg font-semibold text-slate-900">Help</p>
                  <p className="text-sm text-slate-600">
                    Use these tab explanations when you want to know where to go next in the app.
                  </p>
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="mb-3 font-semibold text-slate-900">What each tab means</p>
                    <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
                      <li><span className="font-semibold text-slate-900">Command:</span> chat with Builder Core and send the next request.</li>
                      <li><span className="font-semibold text-slate-900">Progress:</span> follow the pipeline and use the manual stage buttons safely.</li>
                      <li><span className="font-semibold text-slate-900">Review:</span> confirm the latest task result before trusting the rollout.</li>
                      <li><span className="font-semibold text-slate-900">Download:</span> install the app on your phone or copy the live link.</li>
                      <li><span className="font-semibold text-slate-900">Help:</span> get quick explanations when you are unsure what to do next.</li>
                    </ul>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="mb-3 font-semibold text-slate-900">When to mark stages done</p>
                    <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
                      <li>Use <span className="font-semibold text-slate-900">Mark Codex Done</span> only after Codex reports completed code work and a commit is visible.</li>
                      <li>Use <span className="font-semibold text-slate-900">Mark Deploy Done</span> only after GitHub Actions is green and Cloud Run is live.</li>
                      <li>Use <span className="font-semibold text-slate-900">Refresh Now</span> only when the newest deployed version is ready to load.</li>
                    </ul>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>

        <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-slate-200 bg-white/95 px-2 py-2 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur lg:hidden">
          <div className="grid grid-cols-5 gap-2">
            {COMMAND_CENTER_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => scrollToSection(tab.key)}
                className={
                  activeTab === tab.key
                    ? "rounded-2xl bg-black px-2 py-2 text-[11px] font-semibold text-white"
                    : "rounded-2xl border border-slate-200 bg-slate-50 px-2 py-2 text-[11px] font-medium text-slate-600"
                }
              >
                {tab.label}
              </button>
            ))}
          </div>
        </nav>

        {lastTask && (
          <div className="fixed bottom-24 left-4 right-4 z-20 lg:bottom-4 lg:left-auto lg:right-6 lg:w-[430px]">
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

              <div className="mb-3 flex items-center justify-between text-sm font-semibold text-slate-700">
                <span>Progress</span>
                <span>{pipelineProgress}%</span>
              </div>
              <div className="mb-3 h-4 rounded-full bg-slate-200">
                <div
                  className="h-4 rounded-full bg-blue-600 transition-all"
                  style={{ width: `${pipelineProgress}%` }}
                />
              </div>

              <p className="mb-4 text-sm font-semibold text-slate-900">
                {pipelineProgressText}
              </p>

              <div className="mb-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    What is happening now
                  </p>
                  <p className="mt-2 text-sm font-medium text-slate-900">
                    {pipelineCurrentText}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Next step
                  </p>
                  <p className="mt-2 text-sm font-medium text-slate-900">
                    {pipelineNextStepText}
                  </p>
                </div>
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
                      ? "w-full rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white sm:w-auto"
                      : "w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400 sm:w-auto"
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
                      ? "w-full rounded-xl border border-black px-3 py-2 text-xs font-semibold text-black sm:w-auto"
                      : "w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400 sm:w-auto"
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
                      ? "w-full rounded-xl border border-black px-3 py-2 text-xs font-semibold text-black sm:w-auto"
                      : "w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400 sm:w-auto"
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
                      ? "w-full rounded-xl bg-black px-3 py-2 text-xs font-semibold text-white sm:w-auto"
                      : "w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-400 sm:w-auto"
                  }
                >
                  Refresh Now
                </button>
              </div>

              <div className="space-y-3">
                {automationPipeline.map((step, index) => (
                  <div key={step.key} className={getPipelineCardClass(step.status)}>
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className={`h-3 w-3 rounded-full ${getPipelineDotClass(step.status)}`} />
                        <div>
                          <p className={getPipelineTitleClass(step.status)}>
                            {index + 1}. {step.label}
                          </p>
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                            {step.percent}%
                          </p>
                        </div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${getPipelineStatusBadgeClass(step.status)}`}>
                        {step.status === "pending" && "Pending"}
                        {step.status === "active" && "Active"}
                        {step.status === "done" && "Done"}
                      </span>
                    </div>
                    <p className={getPipelineDescriptionClass(step.status)}>
                      {step.description}
                    </p>
                    {step.status === "active" && (
                      <p className="mt-2 text-sm font-medium text-blue-700">
                        {step.currentText}
                      </p>
                    )}
                    {step.status === "pending" && (
                      <p className="mt-2 text-[11px] text-slate-400">
                        Waiting for earlier steps to finish.
                      </p>
                    )}
                    {step.status === "done" && (
                      <p className="mt-2 text-[11px] text-green-700">
                        Completed.
                      </p>
                    )}
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
