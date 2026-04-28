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

const TASK_STAGE_DEFINITIONS = [
  {
    key: "planning",
    label: "Planning",
    description: "Builder Core is shaping the safest plan for the request.",
    activeText: "Builder Core is creating a safe plan.",
    completeText: "Planning complete - press Next",
    nextText: "Next: Codex Working will begin after you press Next."
  },
  {
    key: "codex_working",
    label: "Codex Working",
    description: "The simulated Codex stage is working through the requested repo change.",
    activeText: "Codex is expected to work on the code change.",
    completeText: "Codex Working complete - press Next",
    nextText: "Next: GitHub Deploying will begin after you press Next."
  },
  {
    key: "github_deploying",
    label: "GitHub Deploying",
    description: "GitHub Actions is treated as the next deploy checkpoint.",
    activeText: "GitHub Actions is expected to deploy the update.",
    completeText: "GitHub Deploying complete - press Next",
    nextText: "Next: Cloud Run Live will begin after you press Next."
  },
  {
    key: "cloud_run_live",
    label: "Cloud Run Live",
    description: "The live service stage represents the new cloud revision coming online.",
    activeText: "A new Cloud Run version is expected to go live.",
    completeText: "Cloud Run Live complete - press Next",
    nextText: "Next: App Refreshed will begin after you press Next."
  },
  {
    key: "app_refreshed",
    label: "App Refreshed",
    description: "The final stage confirms the app is ready for the next instruction.",
    activeText: "Builder Core is preparing the refreshed app state.",
    completeText: "Done - ready for next task",
    nextText: "Next: start a new task when you are ready."
  }
] as const;

const NEXT_UPGRADE_SUGGESTIONS = [
  "Enable real Codex automation",
  "Add live deploy detection",
  "Store tasks in Firestore",
  "Add multi-project support",
  "Save GitHub status history"
] as const;

type ProjectItem = {
  id: number;
  name: string;
};

type CommandCenterTabKey = "command" | "progress" | "review" | "download" | "help";
type ExecutionStatus = "idle" | "active" | "awaiting_next" | "completed";
type TaskStageKey = (typeof TASK_STAGE_DEFINITIONS)[number]["key"];
type TaskStageStatus = "pending" | "active" | "done";

type TaskStage = {
  key: TaskStageKey;
  label: string;
  description: string;
  activeText: string;
  completeText: string;
  nextText: string;
  status: TaskStageStatus;
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

type GithubWorkflow = {
  name?: string;
  status?: string;
  conclusion?: string | null;
  url?: string;
  event?: string;
  branch?: string;
  sha?: string;
  short_sha?: string;
  updated_at?: string;
};

type GithubCommit = {
  sha?: string;
  short_sha?: string;
  message?: string;
  url?: string;
  author?: string;
  timestamp?: string;
};

type GithubStatusResponse = {
  ok?: boolean;
  connected?: boolean;
  source?: string;
  repo?: string;
  branch?: string;
  configured_with_token?: boolean;
  latest_commit?: GithubCommit | null;
  checks_workflow?: GithubWorkflow | null;
  deploy_workflow?: GithubWorkflow | null;
  summary?: string;
  next_step?: string;
  error?: string;
};

type CommandTask = {
  instruction: string;
  planner: string;
  prompt: string;
  timestamp: string;
  builderSummary?: string | null;
  runSummary?: string | null;
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
  created_files?: string[];
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
    "1. Inspect the current frontend, backend, and deployment context for the request.",
    "2. Choose the smallest safe change that solves the problem.",
    "3. Preserve working features before changing anything else.",
    "4. Prepare a Codex-ready implementation task.",
    "5. Verify the result with focused testing and a live check.",
    "",
    "Risks:",
    "- Breaking the frontend/backend connection.",
    "- Regressing the mobile install or health indicator experience.",
    "- Making a broad UI change when a smaller one is safer.",
    "",
    "Testing plan:",
    "- Confirm /system/status still reports correctly in the app.",
    "- Confirm the main command submission flow still works.",
    "- Confirm the latest UI works on desktop and phone widths.",
    "- Confirm the deployed frontend and backend still load after deployment."
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

  return ["Next Steps", ...nextSteps.map((step) => `- ${String(step)}`)].join("\n");
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

function formatTimestamp(date: Date) {
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function getExecutionStatusLabel(status: ExecutionStatus) {
  if (status === "active") {
    return "Running";
  }

  if (status === "awaiting_next") {
    return "Press Next";
  }

  if (status === "completed") {
    return "Done";
  }

  return "Idle";
}

function buildTaskStages(currentStageIndex: number, executionStatus: ExecutionStatus) {
  return TASK_STAGE_DEFINITIONS.map((stage, index) => {
    let status: TaskStageStatus = "pending";

    if (currentStageIndex < 0) {
      status = "pending";
    } else if (executionStatus === "completed") {
      status = "done";
    } else if (index < currentStageIndex) {
      status = "done";
    } else if (index === currentStageIndex && executionStatus === "active") {
      status = "active";
    } else if (index === currentStageIndex && executionStatus === "awaiting_next") {
      status = "done";
    }

    return {
      ...stage,
      status
    };
  });
}

function getTaskStageCardClass(status: TaskStageStatus) {
  if (status === "active") {
    return "rounded-3xl border-2 border-blue-200 bg-blue-50 p-4 shadow-sm";
  }

  if (status === "done") {
    return "rounded-2xl border border-green-200 bg-green-50/80 p-3";
  }

  return "rounded-2xl border border-slate-100 bg-slate-50/80 p-2.5 opacity-60";
}

function getTaskStageBadgeClass(status: TaskStageStatus) {
  if (status === "active") {
    return "border border-blue-200 bg-blue-100 text-blue-700";
  }

  if (status === "done") {
    return "border border-green-200 bg-green-100 text-green-700";
  }

  return "border border-slate-200 bg-slate-100 text-slate-500";
}

function getTaskStageDotClass(status: TaskStageStatus) {
  if (status === "active") {
    return "bg-blue-600";
  }

  if (status === "done") {
    return "bg-green-600";
  }

  return "bg-slate-300";
}

function getTaskStageTitleClass(status: TaskStageStatus) {
  if (status === "active") {
    return "text-base font-semibold text-slate-900";
  }

  if (status === "done") {
    return "text-sm font-medium text-slate-900";
  }

  return "text-sm font-medium text-slate-500";
}

function getTaskStageDescriptionClass(status: TaskStageStatus) {
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

function getGithubTrackingBadgeClass(state: "checking" | "online" | "offline") {
  if (state === "online") {
    return "border border-green-200 bg-green-100 text-green-700";
  }

  if (state === "offline") {
    return "border border-red-200 bg-red-100 text-red-700";
  }

  return "border border-slate-200 bg-slate-100 text-slate-600";
}

function getGithubWorkflowBadgeClass(workflow: GithubWorkflow | null | undefined) {
  if (!workflow) {
    return "border border-slate-200 bg-slate-100 text-slate-500";
  }

  if (workflow.status !== "completed") {
    return "border border-blue-200 bg-blue-100 text-blue-700";
  }

  if (workflow.conclusion === "success") {
    return "border border-green-200 bg-green-100 text-green-700";
  }

  if (workflow.conclusion === "failure" || workflow.conclusion === "timed_out") {
    return "border border-red-200 bg-red-100 text-red-700";
  }

  return "border border-amber-200 bg-amber-100 text-amber-700";
}

function getGithubWorkflowLabel(workflow: GithubWorkflow | null | undefined) {
  if (!workflow) {
    return "Not found";
  }

  if (workflow.status !== "completed") {
    return workflow.status ? workflow.status.replaceAll("_", " ") : "Running";
  }

  if (workflow.conclusion) {
    return workflow.conclusion.replaceAll("_", " ");
  }

  return "Completed";
}

function workflowPassed(workflow: GithubWorkflow | null | undefined) {
  return workflow?.status === "completed" && workflow?.conclusion === "success";
}

function buildReviewSummary(
  task: CommandTask | null,
  backendState: "checking" | "online" | "offline",
  githubStatus: GithubStatusResponse | null
): ReviewSummary {
  const hasBuilderSummary = Boolean(task?.builderSummary);
  const backendHealthy = backendState === "online";
  const githubChecksPassed = workflowPassed(githubStatus?.checks_workflow);
  const githubDeployPassed = workflowPassed(githubStatus?.deploy_workflow);
  const githubConnected = githubStatus?.connected === true;

  return {
    checklist: [
      {
        label: "Files changed?",
        status: hasBuilderSummary ? "ready" : "attention",
        detail: hasBuilderSummary
          ? "Builder Core returned a change summary for this task."
          : "Confirm the exact files changed before treating the task as complete."
      },
      {
        label: "Build passed?",
        status: "ready",
        detail: "The simplified flow assumes the build was checked before moving forward."
      },
      {
        label: "GitHub Actions green?",
        status: githubChecksPassed ? "ready" : "attention",
        detail: githubChecksPassed
          ? "GitHub tracking shows the latest Repo Checks run completed successfully."
          : githubConnected
            ? "GitHub tracking is connected, but the latest Repo Checks run still needs attention."
            : "GitHub tracking is not available yet, so confirm the Actions run manually."
      },
      {
        label: "Frontend deployed?",
        status: githubDeployPassed ? "ready" : "attention",
        detail: githubDeployPassed
          ? "GitHub tracking shows the latest deploy workflow completed successfully."
          : githubConnected
            ? "GitHub tracking is connected, but the deploy workflow has not reached a successful result yet."
            : "GitHub deploy status is not connected yet, so verify the live frontend manually."
      },
      {
        label: "Backend still online?",
        status: backendHealthy ? "ready" : "attention",
        detail: backendHealthy
          ? "The backend health badge is still online."
          : "Recheck /system/status before closing the task."
      }
    ],
    doItems: [
      "Prefer safe improvements and small upgrades after the task completes.",
      "Verify the live app quickly before starting the next task.",
      "Capture files changed and testing notes while the result is fresh."
    ],
    avoidItems: [
      "Do not pile risky changes onto an unverified result.",
      "Do not delete working features to make a change easier.",
      "Do not assume the backend is healthy if the badge is offline."
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
  const [githubTrackingState, setGithubTrackingState] = useState<"checking" | "online" | "offline">("checking");
  const [githubStatus, setGithubStatus] = useState<GithubStatusResponse | null>(null);
  const [githubCheckedAt, setGithubCheckedAt] = useState("");
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>("idle");
  const [taskStageIndex, setTaskStageIndex] = useState(-1);
  const [taskStageProgress, setTaskStageProgress] = useState(0);
  const [activeTaskInstruction, setActiveTaskInstruction] = useState("");
  const [installMessage, setInstallMessage] = useState("");
  const [lastTask, setLastTask] = useState<CommandTask | null>(null);
  const [completedTaskId, setCompletedTaskId] = useState("");
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([
    {
      id: "welcome",
      role: "assistant",
      kind: "text",
      title: "Builder Core",
      content:
        "Ask Builder Core to build, fix, or upgrade anything. I will plan the work, prepare the Codex task, keep the stage bar visible, and explain what to do next.",
      timestamp: "Ready"
    }
  ]);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const sectionRefs = useRef<Partial<Record<CommandCenterTabKey, HTMLElement | null>>>({});

  const taskStages = useMemo(() => buildTaskStages(taskStageIndex, executionStatus), [taskStageIndex, executionStatus]);
  const currentTaskStage = taskStageIndex >= 0 ? TASK_STAGE_DEFINITIONS[taskStageIndex] : null;
  const latestReview = useMemo(() => buildReviewSummary(lastTask, backendStatus, githubStatus), [lastTask, backendStatus, githubStatus]);

  const taskStageCounter =
    currentTaskStage !== null ? `${taskStageIndex + 1}/${TASK_STAGE_DEFINITIONS.length}` : `0/${TASK_STAGE_DEFINITIONS.length}`;
  const taskBarVisible = currentTaskStage !== null || Boolean(lastTask) || Boolean(activeTaskInstruction);
  const canAdvanceStage =
    executionStatus === "awaiting_next" &&
    taskStageIndex >= 0 &&
    taskStageIndex < TASK_STAGE_DEFINITIONS.length - 1;

  const taskBarTaskName =
    activeTaskInstruction || lastTask?.instruction || "Run a command to start the next task";
  const githubRepoLabel = githubStatus?.repo ?? "jagangill001/builder-core";
  const githubBranchLabel = githubStatus?.branch ?? "main";
  const githubChecksWorkflow = githubStatus?.checks_workflow ?? null;
  const githubDeployWorkflow = githubStatus?.deploy_workflow ?? null;
  const githubStatusSummary =
    githubStatus?.summary ??
    (githubTrackingState === "checking"
      ? "Checking the latest GitHub repo and workflow state..."
      : "GitHub tracking is not available right now.");
  const githubStatusNextStep =
    githubStatus?.next_step ??
    (githubTrackingState === "offline"
      ? "Next: verify the latest GitHub run manually until tracking reconnects."
      : "Next: wait for a tracked workflow update.");

  let taskProgressText = "No task is running yet.";
  let taskStatusText = "Run a command to begin.";
  let taskNextText = "Next: submit a command in the Command tab.";

  if (currentTaskStage) {
    if (executionStatus === "active") {
      taskProgressText = `${taskStageProgress}%`;
      taskStatusText = currentTaskStage.activeText;
      taskNextText = currentTaskStage.nextText;
    } else if (executionStatus === "awaiting_next") {
      taskProgressText = "100%";
      taskStatusText = currentTaskStage.completeText;
      taskNextText =
        taskStageIndex < TASK_STAGE_DEFINITIONS.length - 1
          ? `Next: ${TASK_STAGE_DEFINITIONS[taskStageIndex + 1].label} will begin after you press Next.`
          : "Next: start a new task when you are ready.";
    } else if (executionStatus === "completed") {
      taskProgressText = "100%";
      taskStatusText = "Done - ready for next task";
      taskNextText = "Next: enter another command when you are ready.";
    }
  }

  if (currentTaskStage?.key === "github_deploying" && githubTrackingState === "online") {
    taskStatusText = githubStatusSummary;
    taskNextText = githubStatusNextStep;
  }

  function appendChatEntries(entries: ChatEntry[]) {
    setChatEntries((current) => [...current, ...entries]);
  }

  async function checkBackendStatus() {
    try {
      const response = await fetch(`${API_BASE}/system/status`);

      if (!response.ok) {
        throw new Error("Backend status check failed.");
      }

      setBackendStatus("online");
    } catch {
      setBackendStatus("offline");
    }
  }

  async function loadGithubStatus(silent = false) {
    if (!silent) {
      setGithubTrackingState("checking");
    }

    try {
      const response = await fetch(`${API_BASE}/github/status`);
      const data = (await response.json()) as GithubStatusResponse;

      if (!response.ok) {
        throw new Error(typeof data.error === "string" ? data.error : "GitHub status request failed.");
      }

      setGithubStatus(data);
      setGithubTrackingState(data.connected ? "online" : "offline");
      setGithubCheckedAt(formatTimestamp(new Date()));
    } catch (error) {
      setGithubStatus({
        ok: false,
        connected: false,
        repo: githubRepoLabel,
        branch: githubBranchLabel,
        summary: "GitHub status tracking is not available right now.",
        next_step: "Next: verify the latest GitHub run manually until tracking reconnects.",
        error: error instanceof Error ? error.message : "GitHub status request failed."
      });
      setGithubTrackingState("offline");
      setGithubCheckedAt(formatTimestamp(new Date()));
    }
  }

  async function loadProjects() {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json();
      const items = Array.isArray(data.items) ? data.items : [];
      setProjects(items);

      if (items.length > 0 && !items.some((item: ProjectItem) => item.name === selectedProject)) {
        setSelectedProject(items[0].name);
      }
    } catch {
      setProjects([]);
    }
  }

  useEffect(() => {
    void checkBackendStatus();
    void loadProjects();
    void loadGithubStatus();
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void loadGithubStatus(true);
    }, 60000);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const nodes = Object.entries(sectionRefs.current).filter((entry): entry is [CommandCenterTabKey, HTMLElement] => Boolean(entry[1]));

    if (nodes.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (!visibleEntry) {
          return;
        }

        const key = visibleEntry.target.getAttribute("data-section-key");
        if (key === "command" || key === "progress" || key === "review" || key === "download" || key === "help") {
          setActiveTab(key);
        }
      },
      {
        rootMargin: "-30% 0px -40% 0px",
        threshold: [0.2, 0.4, 0.6]
      }
    );

    nodes.forEach(([, node]) => observer.observe(node));

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatEntries]);

  useEffect(() => {
    if (executionStatus !== "active" || taskStageIndex < 0) {
      return;
    }

    const interval = window.setInterval(() => {
      setTaskStageProgress((current) => Math.min(current + 4, 100));
    }, 180);

    return () => window.clearInterval(interval);
  }, [executionStatus, taskStageIndex]);

  useEffect(() => {
    if (executionStatus !== "active" || taskStageIndex < 0 || taskStageProgress < 100) {
      return;
    }

    if (taskStageIndex === TASK_STAGE_DEFINITIONS.length - 1) {
      setExecutionStatus("completed");
      return;
    }

    setExecutionStatus("awaiting_next");
  }, [executionStatus, taskStageIndex, taskStageProgress]);

  useEffect(() => {
    if (executionStatus !== "completed" || !lastTask) {
      return;
    }

    const completionId = `${lastTask.timestamp}-${lastTask.instruction}`;
    if (completedTaskId === completionId) {
      return;
    }

    appendChatEntries([
      {
        id: `${completionId}-done`,
        role: "assistant",
        kind: "text",
        title: "Task Complete",
        content: "Done - ready for next task. Review the checklist below and pick one safe follow-up when you are ready.",
        timestamp: formatTimestamp(new Date())
      },
      {
        id: `${completionId}-review`,
        role: "assistant",
        kind: "review",
        title: "Result Review",
        review: buildReviewSummary(lastTask, backendStatus, githubStatus),
        timestamp: formatTimestamp(new Date())
      },
      {
        id: `${completionId}-upgrades`,
        role: "assistant",
        kind: "text",
        title: "Next Upgrade Ideas",
        content: NEXT_UPGRADE_SUGGESTIONS.map((item) => `- ${item}`).join("\n"),
        timestamp: formatTimestamp(new Date())
      }
    ]);

    setCompletedTaskId(completionId);
  }, [backendStatus, completedTaskId, executionStatus, githubStatus, lastTask]);

  function setSectionRef(key: CommandCenterTabKey) {
    return (node: HTMLElement | null) => {
      sectionRefs.current[key] = node;
    };
  }

  function scrollToSection(key: CommandCenterTabKey) {
    setActiveTab(key);
    sectionRefs.current[key]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleCreateProject() {
    const name = newProjectName.trim();
    if (!name) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name })
      });

      if (!response.ok) {
        throw new Error("Project create failed.");
      }

      setNewProjectName("");
      setSelectedProject(name);
      await loadProjects();
      appendChatEntries([
        {
          id: `project-${Date.now()}`,
          role: "assistant",
          kind: "text",
          title: "Project Ready",
          content: `Created or confirmed the project "${name}". You can use it for the next Builder Core task.`,
          timestamp: formatTimestamp(new Date())
        }
      ]);
    } catch {
      appendChatEntries([
        {
          id: `project-error-${Date.now()}`,
          role: "assistant",
          kind: "text",
          title: "Project Error",
          content: "I could not create that project right now. Try again after the backend is online.",
          timestamp: formatTimestamp(new Date())
        }
      ]);
    }
  }

  async function handleCommandSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const instruction = commandInput.trim();
    if (!instruction) {
      return;
    }

    const projectName = selectedProject || "Default Project";
    const timestamp = formatTimestamp(new Date());
    const fallbackPlanner = buildPlannerOutput(instruction, projectName);
    const fallbackPrompt = buildCodexPrompt(instruction, projectName);

    setCommandInput("");
    setActiveTaskInstruction(instruction);
    setExecutionStatus("active");
    setTaskStageIndex(0);
    setTaskStageProgress(1);
    setCompletedTaskId("");
    setActiveTab("command");

    appendChatEntries([
      {
        id: `user-${Date.now()}`,
        role: "user",
        kind: "text",
        content: instruction,
        timestamp
      },
      {
        id: `planning-${Date.now()}`,
        role: "assistant",
        kind: "text",
        title: "Builder Core",
        content: "Planning...",
        timestamp
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
          project_name: projectName
        })
      });

      const data = (await response.json()) as CommandCenterChatResponse;

      if (!response.ok || !data.ok) {
        throw new Error(typeof data.message === "string" ? data.message : "Chat request failed.");
      }

      const assistantReply =
        typeof data.assistant_reply === "string" && data.assistant_reply
          ? data.assistant_reply
          : "Builder Core reviewed your request and prepared the next safe move.";
      const plannerSummary = buildPlannerSummary(instruction, projectName, data, fallbackPlanner);
      const codexPrompt =
        typeof data.codex_prompt === "string" && data.codex_prompt ? data.codex_prompt : fallbackPrompt;
      const nextStepsSummary = buildNextStepsSummary(data.next_steps);
      const builderSummary = data.build_triggered ? buildBuilderSummary(data) : null;
      const runSummary =
        data.run_info && typeof data.run_info === "object" ? buildRunSummary(data.run_info as Record<string, unknown>) : null;
      const responseTimestamp = formatTimestamp(new Date());

      setLastTask({
        instruction,
        planner: plannerSummary,
        prompt: codexPrompt,
        timestamp: responseTimestamp,
        builderSummary,
        runSummary
      });
      void loadGithubStatus(true);

      appendChatEntries([
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          kind: "text",
          title: "Builder Core",
          content: assistantReply,
          timestamp: responseTimestamp
        },
        {
          id: `planner-${Date.now()}`,
          role: "assistant",
          kind: "planner",
          title: "Planner Output",
          content: plannerSummary,
          timestamp: responseTimestamp
        },
        {
          id: `codex-${Date.now()}`,
          role: "assistant",
          kind: "codex",
          title: "Codex Task",
          content: codexPrompt,
          timestamp: responseTimestamp
        },
        ...(builderSummary
          ? [
              {
                id: `builder-${Date.now()}`,
                role: "assistant" as const,
                kind: "builder" as const,
                title: "Builder Output",
                content: builderSummary,
                timestamp: responseTimestamp
              }
            ]
          : []),
        ...(runSummary
          ? [
              {
                id: `run-${Date.now()}`,
                role: "assistant" as const,
                kind: "builder" as const,
                title: "Run Info",
                content: runSummary,
                timestamp: responseTimestamp
              }
            ]
          : []),
        ...(nextStepsSummary
          ? [
              {
                id: `next-${Date.now()}`,
                role: "assistant" as const,
                kind: "text" as const,
                title: "Next Steps",
                content: nextStepsSummary,
                timestamp: responseTimestamp
              }
            ]
          : [])
      ]);
    } catch (error) {
      setExecutionStatus("idle");
      setTaskStageIndex(-1);
      setTaskStageProgress(0);
      setActiveTaskInstruction("");

      appendChatEntries([
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          kind: "text",
          title: "Backend Error",
          content:
            error instanceof Error
              ? `I could not complete that request: ${error.message}`
              : "I could not complete that request because the backend did not respond.",
          timestamp: formatTimestamp(new Date())
        }
      ]);
    }
  }

  function handleNextStage() {
    if (!canAdvanceStage || !currentTaskStage) {
      return;
    }

    const nextIndex = taskStageIndex + 1;
    const nextStage = TASK_STAGE_DEFINITIONS[nextIndex];

    appendChatEntries([
      {
        id: `stage-${Date.now()}`,
        role: "assistant",
        kind: "text",
        title: "Automation Progress",
        content: `${currentTaskStage.label} is complete. ${nextStage.label} has started.`,
        timestamp: formatTimestamp(new Date())
      }
    ]);

    setTaskStageIndex(nextIndex);
    setTaskStageProgress(1);
    setExecutionStatus("active");
  }

  function handleOpenAppLink() {
    window.open(FRONTEND_APP_URL, "_blank", "noopener,noreferrer");
  }

  async function handleCopyAppLink() {
    try {
      await navigator.clipboard.writeText(FRONTEND_APP_URL);
      setInstallMessage("App link copied.");
    } catch {
      setInstallMessage(`Copy this link manually: ${FRONTEND_APP_URL}`);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f7f4] text-slate-900">
      <div className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <p className="text-xl font-semibold text-slate-950">Builder Core</p>
            <p className="text-sm text-slate-500">Cloud-first command center for Builder Core tasks.</p>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <span
              className={
                backendStatus === "online"
                  ? "rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-semibold text-green-700"
                  : backendStatus === "offline"
                    ? "rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-semibold text-red-700"
                    : "rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600"
              }
            >
              {backendStatus === "checking" && "Backend: Checking..."}
              {backendStatus === "online" && "Backend: Online"}
              {backendStatus === "offline" && "Backend: Offline"}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Automation: {getExecutionStatusLabel(executionStatus)}
            </span>
          </div>
        </div>
      </div>

      {taskBarVisible && (
        <div className="fixed inset-x-0 bottom-20 z-30 px-3 sm:px-6 lg:bottom-6 lg:left-72 lg:right-8 lg:px-0">
          <div className="mx-auto max-w-5xl rounded-[28px] border border-slate-200 bg-white/95 px-4 py-4 shadow-2xl backdrop-blur sm:px-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Stage {taskStageCounter}
                  </span>
                  <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-blue-700">
                    {currentTaskStage ? currentTaskStage.label : "Idle"}
                  </span>
                </div>

                <p className="truncate text-sm font-semibold text-slate-900 sm:text-base">{taskBarTaskName}</p>
                <p className="mt-1 text-sm text-slate-600">{taskStatusText}</p>

                <div className="mt-3 flex items-center justify-between gap-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <span>Stage Progress</span>
                  <span>{taskProgressText}</span>
                </div>
                <div className="mt-2 h-3 rounded-full bg-slate-200">
                  <div
                    className="h-3 rounded-full bg-slate-900 transition-all"
                    style={{ width: `${Math.max(taskStageProgress, 0)}%` }}
                  />
                </div>

                <p className="mt-3 text-xs text-slate-500">Automation permission granted by user.</p>
                <p className="mt-1 text-xs text-slate-500">Future: Codex will run automatically after approval.</p>
                <p className="mt-2 text-xs text-slate-500">{taskNextText}</p>
              </div>

              <div className="flex items-center gap-3 lg:w-auto">
                <button
                  type="button"
                  onClick={handleNextStage}
                  disabled={!canAdvanceStage}
                  className={
                    canAdvanceStage
                      ? "w-full rounded-2xl bg-black px-5 py-3 text-sm font-semibold text-white lg:w-auto"
                      : "w-full rounded-2xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-400 lg:w-auto"
                  }
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto flex max-w-7xl gap-6 px-4 pb-28 pt-6 sm:px-6 lg:px-8">
        <aside className="sticky top-6 hidden h-fit w-64 shrink-0 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm lg:block">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Navigation</p>
          <div className="space-y-2">
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

          <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Quick Actions</p>
            <div className="mt-3 flex flex-col gap-2">
              <button
                type="button"
                onClick={() => scrollToSection("download")}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700"
              >
                Install on Phone
              </button>
              <button
                type="button"
                onClick={handleCopyAppLink}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700"
              >
                Copy App Link
              </button>
            </div>
            {installMessage && <p className="mt-3 text-xs text-slate-500">{installMessage}</p>}
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <div className="grid gap-6">
            <section
              ref={setSectionRef("command")}
              data-section-key="command"
              className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
            >
              <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-lg font-semibold text-slate-900">Command Center</p>
                  <p className="text-sm text-slate-600">
                    Use one command box to chat with Builder Core, generate the plan, and start the next tracked task.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr),auto,auto]">
                  <select
                    value={selectedProject}
                    onChange={(event) => setSelectedProject(event.target.value)}
                    className="min-w-0 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
                  >
                    {projects.length === 0 && <option value="Default Project">Default Project</option>}
                    {projects.map((project) => (
                      <option key={project.id} value={project.name}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(event) => setNewProjectName(event.target.value)}
                    placeholder="New project name"
                    className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700"
                  />
                  <button
                    type="button"
                    onClick={handleCreateProject}
                    className="rounded-2xl border border-black px-4 py-3 text-sm font-semibold text-black"
                  >
                    Create Project
                  </button>
                </div>
              </div>

              <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-3 sm:p-4">
                <div className="space-y-4">
                  {chatEntries.map((entry) => {
                    if (entry.kind === "text") {
                      return renderTextBubble(entry);
                    }

                    return renderStructuredBubble(entry);
                  })}
                  <div ref={bottomRef} />
                </div>
              </div>

              <form onSubmit={handleCommandSubmit} className="mt-5">
                <label htmlFor="command-input" className="mb-3 block text-sm font-semibold text-slate-900">
                  Ask Builder Core to build, fix, or upgrade anything...
                </label>
                <textarea
                  id="command-input"
                  value={commandInput}
                  onChange={(event) => setCommandInput(event.target.value)}
                  placeholder="Ask Builder Core to build, fix, or upgrade anything..."
                  className="min-h-[140px] w-full rounded-[28px] border border-slate-200 px-4 py-4 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                />

                <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-slate-500">
                    Builder Core will call the backend chat route, prepare the Codex task, and open the simplified stage bar.
                  </p>
                  <button
                    type="submit"
                    className="rounded-2xl bg-black px-5 py-3 text-sm font-semibold text-white"
                  >
                    Run Command
                  </button>
                </div>
              </form>
            </section>

            <section
              ref={setSectionRef("progress")}
              data-section-key="progress"
              className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
            >
              <div className="mb-4">
                <p className="text-lg font-semibold text-slate-900">Progress</p>
                <p className="text-sm text-slate-600">
                  One compact task bar controls the stage flow. Each stage progresses from 1% to 100%, then waits for one Next click.
                </p>
              </div>

              <div className="mb-5 grid gap-4 lg:grid-cols-[1.4fr,1fr]">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">Current Task</p>
                      <p className="text-xs text-slate-500">{taskBarTaskName}</p>
                    </div>
                    <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                      {getExecutionStatusLabel(executionStatus)}
                    </span>
                  </div>

                  <div className="mb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <span>{currentTaskStage ? currentTaskStage.label : "No stage yet"}</span>
                    <span>{taskProgressText}</span>
                  </div>
                  <div className="h-3 rounded-full bg-slate-200">
                    <div
                      className="h-3 rounded-full bg-slate-900 transition-all"
                      style={{ width: `${Math.max(taskStageProgress, 0)}%` }}
                    />
                  </div>

                  <p className="mt-3 text-sm font-medium text-slate-900">{taskStatusText}</p>
                  <p className="mt-2 text-sm text-slate-600">{taskNextText}</p>
                </div>

                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">Permission Model</p>
                  <p className="mt-3 text-sm text-slate-700">Automation permission granted by user.</p>
                  <p className="mt-2 text-sm text-slate-600">
                    Future: Codex will run automatically after approval, with cloud tracking instead of laptop-only state.
                  </p>
                  <button
                    type="button"
                    onClick={handleNextStage}
                    disabled={!canAdvanceStage}
                    className={
                      canAdvanceStage
                        ? "mt-4 rounded-2xl bg-black px-4 py-3 text-sm font-semibold text-white"
                        : "mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-400"
                    }
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="mb-5 rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <div className="mb-3 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">GitHub Tracking</p>
                    <p className="mt-1 text-sm text-slate-600">
                      Builder Core now reads the repo and workflow state so the GitHub stage is tied to real GitHub status.
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${getGithubTrackingBadgeClass(githubTrackingState)}`}>
                    {githubTrackingState === "checking" && "Checking"}
                    {githubTrackingState === "online" && "Connected"}
                    {githubTrackingState === "offline" && "Unavailable"}
                  </span>
                </div>

                <div className="grid gap-4 xl:grid-cols-[1.3fr,1fr]">
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <div className="mb-3 flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <span>{githubRepoLabel}</span>
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
                        Branch {githubBranchLabel}
                      </span>
                    </div>

                    <p className="text-sm font-medium text-slate-900">{githubStatusSummary}</p>
                    <p className="mt-2 text-sm text-slate-600">{githubStatusNextStep}</p>

                    <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Latest Commit</p>
                      <p className="mt-2 text-sm font-medium text-slate-900">
                        {githubStatus?.latest_commit?.short_sha
                          ? `${githubStatus.latest_commit.short_sha} - ${githubStatus.latest_commit.message ?? "No commit message"}`
                          : "No commit details available yet."}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        {githubStatus?.latest_commit?.author && githubStatus?.latest_commit?.timestamp
                          ? `${githubStatus.latest_commit.author} - ${githubStatus.latest_commit.timestamp}`
                          : "Builder Core will show commit details when the GitHub API responds."}
                      </p>
                      {githubStatus?.latest_commit?.url && (
                        <a
                          href={githubStatus.latest_commit.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-block text-xs font-semibold text-blue-700"
                        >
                          Open commit
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-900">Repo Checks</p>
                        <span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${getGithubWorkflowBadgeClass(githubChecksWorkflow)}`}>
                          {getGithubWorkflowLabel(githubChecksWorkflow)}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">
                        {githubChecksWorkflow?.updated_at
                          ? `Updated at ${githubChecksWorkflow.updated_at}`
                          : "Waiting for a tracked Repo Checks workflow run."}
                      </p>
                      {githubChecksWorkflow?.url && (
                        <a
                          href={githubChecksWorkflow.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-block text-xs font-semibold text-blue-700"
                        >
                          Open workflow run
                        </a>
                      )}
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-4">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-900">Deploy Workflow</p>
                        <span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${getGithubWorkflowBadgeClass(githubDeployWorkflow)}`}>
                          {getGithubWorkflowLabel(githubDeployWorkflow)}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">
                        {githubDeployWorkflow?.updated_at
                          ? `Updated at ${githubDeployWorkflow.updated_at}`
                          : "Waiting for a tracked Deploy Cloud Run workflow run."}
                      </p>
                      {githubDeployWorkflow?.url && (
                        <a
                          href={githubDeployWorkflow.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-block text-xs font-semibold text-blue-700"
                        >
                          Open deploy run
                        </a>
                      )}
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Status Refresh</p>
                      <p className="mt-2 text-sm text-slate-700">
                        {githubCheckedAt ? `Last checked ${githubCheckedAt}` : "Builder Core will record the next GitHub status refresh here."}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Auto-refresh runs every minute. Add `GITHUB_STATUS_TOKEN` later if you want higher GitHub API limits.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                {taskStages.map((stage, index) => (
                  <div key={stage.key} className={getTaskStageCardClass(stage.status)}>
                    <div className="mb-2 flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <span className={`mt-1 h-3 w-3 rounded-full ${getTaskStageDotClass(stage.status)}`} />
                        <div>
                          <p className={getTaskStageTitleClass(stage.status)}>
                            {index + 1}. {stage.label}
                          </p>
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                            {stage.status === "active" ? `${taskStageProgress}%` : stage.status === "done" ? "100%" : "Pending"}
                          </p>
                        </div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${getTaskStageBadgeClass(stage.status)}`}>
                        {stage.status === "active" && "Active"}
                        {stage.status === "done" && "Done"}
                        {stage.status === "pending" && "Pending"}
                      </span>
                    </div>
                    <p className={getTaskStageDescriptionClass(stage.status)}>{stage.description}</p>
                    {stage.status === "active" && <p className="mt-2 text-sm font-medium text-blue-700">{stage.activeText}</p>}
                    {stage.status === "done" && index === taskStageIndex && executionStatus !== "completed" && (
                      <p className="mt-2 text-sm font-medium text-green-700">{stage.completeText}</p>
                    )}
                    {stage.status === "done" && executionStatus === "completed" && index === taskStages.length - 1 && (
                      <p className="mt-2 text-sm font-medium text-green-700">Done - ready for next task</p>
                    )}
                  </div>
                ))}
              </div>

              {executionStatus === "completed" && (
                <div className="mt-5 rounded-3xl border border-blue-200 bg-blue-50 p-4">
                  <p className="text-sm font-semibold text-blue-900">Next upgrade ideas</p>
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-blue-900">
                    {NEXT_UPGRADE_SUGGESTIONS.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            <section
              ref={setSectionRef("review")}
              data-section-key="review"
              className="scroll-mt-32 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
            >
              <div className="mb-4">
                <p className="text-lg font-semibold text-slate-900">Review</p>
                <p className="text-sm text-slate-600">
                  Use this section after a task completes so you can decide whether the result is safe to keep moving with.
                </p>
              </div>

              {lastTask ? (
                <>
                  <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                    <p>
                      <span className="font-semibold text-slate-900">Latest task:</span> {lastTask.instruction}
                    </p>
                    <p className="mt-1">
                      <span className="font-semibold text-slate-900">Recorded:</span> {lastTask.timestamp}
                    </p>
                  </div>
                  {renderReviewContent(latestReview)}
                </>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  Run a command first. Review guidance will appear here after Builder Core responds.
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
                  Keep the install steps close by so Builder Core is easy to open on your phone any time.
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

                  {installMessage && <p className="text-sm text-slate-600">{installMessage}</p>}
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
                  Builder Core now uses one compact task system: let each stage finish, then press Next to move forward.
                </p>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="mb-3 font-semibold text-slate-900">What each tab means</p>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
                    <li>
                      <span className="font-semibold text-slate-900">Command:</span> chat with Builder Core and send the next request.
                    </li>
                    <li>
                      <span className="font-semibold text-slate-900">Progress:</span> follow the stage bar, review live GitHub tracking, and use the single Next button.
                    </li>
                    <li>
                      <span className="font-semibold text-slate-900">Review:</span> confirm the latest task result before trusting the rollout.
                    </li>
                    <li>
                      <span className="font-semibold text-slate-900">Download:</span> install the app on your phone or copy the live link.
                    </li>
                    <li>
                      <span className="font-semibold text-slate-900">Help:</span> get quick guidance when you are unsure what to do next.
                    </li>
                  </ul>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="mb-3 font-semibold text-slate-900">How the stage flow works</p>
                  <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
                    <li>Each stage automatically progresses from 1% to 100%.</li>
                    <li>When a stage reaches 100%, Builder Core pauses and tells you to press Next.</li>
                    <li>The only manual control is the Next button in the compact task bar.</li>
                    <li>The final stage ends with Done - ready for next task.</li>
                  </ul>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-20 border-t border-slate-200 bg-white/95 px-2 py-2 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur lg:hidden">
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
    </main>
  );
}
