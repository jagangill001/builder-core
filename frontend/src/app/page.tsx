"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const FRONTEND_APP_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";

type ProjectItem = {
  id: number;
  name: string;
};

type BridgeStatus = {
  ready_for_repo_work?: boolean;
  github_configured?: boolean;
  codex_mode?: string;
  codex_configured?: boolean;
  missing?: string[];
  notes?: string[];
  message?: string;
  repo?: string;
  branch?: string;
  frontend_url?: string;
  backend_url?: string;
  checked_at?: string;
};

type SystemStatusResponse = {
  status?: string;
  service?: string;
  bridge_status?: BridgeStatus;
  task_storage_backend?: string;
  task_storage_message?: string;
  memory_storage_backend?: string;
  memory_storage_message?: string;
  file_storage_backend?: string;
  file_storage_message?: string;
  latest_summary_available?: boolean;
  project_structure_scanned?: boolean;
};

type TaskSummary = {
  task_id?: string;
  original_command?: string;
  final_status?: string;
  stages_completed?: string[];
  files_changed?: string[];
  folder_used?: string;
  backend_logs?: string[];
  errors?: string[];
  what_completed?: string[];
  what_still_needs_manual_setup?: string[];
  next_recommended_step?: string;
  message?: string;
  updated_at?: string;
};

type TaskRecord = {
  id: string;
  command: string;
  project_name?: string;
  status: string;
  stage?: string;
  current_stage?: string;
  progress: number;
  github_commit?: string | null;
  workflow_status?: string | null;
  logs?: string[];
  errors?: string[];
  summary?: TaskSummary | null;
  bridge_status?: BridgeStatus;
  files_changed?: string[];
  stage_history?: {
    stage: string;
    status: string;
    progress: number;
    timestamp: string;
    message?: string;
  }[];
  config_problems?: string[];
  manual_setup?: string[];
  testing_result?: {
    ok?: boolean;
    checks?: string[];
    missing_routes?: string[];
  } | null;
  deploy_result?: {
    summary?: string;
    next_step?: string;
    connected?: boolean;
    deploy_running?: boolean;
    deploy_succeeded?: boolean;
    backend_healthy?: boolean;
    frontend_reachable?: boolean;
  } | null;
  created_at?: string;
  updated_at?: string;
  storage_backend?: string;
  storage_message?: string;
};

type TasksListResponse = {
  items?: TaskRecord[];
  storage_backend?: string;
  storage_message?: string;
};

type TaskCreateResponse = {
  task_id: string;
  status: string;
  stage?: string;
  storage_backend?: string;
  storage_message?: string;
};

type MemoryEntry = {
  id: string;
  type?: string;
  project_name?: string;
  note?: string;
  summary?: unknown;
  task_id?: string;
  command?: string;
  status?: string;
  created_at?: string;
};

type MemoryResponse = {
  ok?: boolean;
  storage_backend?: string;
  storage_message?: string;
  project_memory?: MemoryEntry[];
  latest_summary?: TaskSummary | null;
  latest_bridge_status?: BridgeStatus | null;
  known_environment_problems?: string[];
};

type Lesson = {
  id: string;
  task_id?: string;
  command?: string;
  what_happened?: string[] | string;
  files_changed?: string[];
  error?: string | null;
  lesson_learned?: string;
  next_recommendation?: string;
  status?: string;
  created_at?: string;
};

type LearningResponse = {
  ok?: boolean;
  storage_backend?: string;
  storage_message?: string;
  project_structure_summary?: {
    scanned_at?: string;
    root?: string;
    top_level_folders?: string[];
    important_files?: string[];
    sample_tree?: string[];
    notes?: string[];
  } | null;
  lessons?: Lesson[];
  known_issues?: string[];
  recommended_next_steps?: string[];
  notes?: string[];
};

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function titleCaseStage(stage?: string | null) {
  if (!stage) {
    return "Waiting";
  }

  return stage
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function getProgressBarClass(status: string) {
  if (status === "failed") {
    return "bg-red-500";
  }

  if (status === "completed") {
    return "bg-green-600";
  }

  return "bg-blue-600";
}

function getStatusBadgeClass(status: string) {
  if (status === "completed") {
    return "border border-green-200 bg-green-50 text-green-700";
  }

  if (status === "failed") {
    return "border border-red-200 bg-red-50 text-red-700";
  }

  if (status === "received") {
    return "border border-slate-200 bg-slate-50 text-slate-700";
  }

  return "border border-blue-200 bg-blue-50 text-blue-700";
}

function getBackendBadgeClass(status: "checking" | "online" | "offline") {
  if (status === "online") {
    return "border border-green-200 bg-green-50 text-green-700";
  }

  if (status === "offline") {
    return "border border-red-200 bg-red-50 text-red-700";
  }

  return "border border-slate-200 bg-slate-50 text-slate-600";
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectName, setProjectName] = useState("Default Project");
  const [commandInput, setCommandInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [pollError, setPollError] = useState("");
  const [currentTaskId, setCurrentTaskId] = useState("");
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [recentTasks, setRecentTasks] = useState<TaskRecord[]>([]);
  const [memoryData, setMemoryData] = useState<MemoryResponse | null>(null);
  const [learningData, setLearningData] = useState<LearningResponse | null>(null);
  const [memoryNote, setMemoryNote] = useState("");
  const [memoryMessage, setMemoryMessage] = useState("");
  const [installMessage, setInstallMessage] = useState("");

  const activeStage = currentTask?.stage ?? currentTask?.current_stage ?? "received";
  const activeProgress = currentTask?.progress ?? 0;
  const taskLogs = currentTask?.logs ?? [];
  const taskErrors = currentTask?.errors ?? [];
  const bridgeStatus = currentTask?.bridge_status ?? systemStatus?.bridge_status ?? null;

  const isTaskActive = useMemo(() => {
    if (!currentTask) {
      return false;
    }

    return !["completed", "failed"].includes(currentTask.status);
  }, [currentTask]);

  async function loadSystemStatus(silent = false) {
    try {
      const response = await fetch(`${API_BASE}/system/status`);
      const data = await parseJsonSafe<SystemStatusResponse>(response);
      if (!response.ok || !data) {
        throw new Error("System status request failed.");
      }

      setSystemStatus(data);
      setBackendStatus("online");
      if (!silent) {
        setSubmitError("");
      }
    } catch (error) {
      setBackendStatus("offline");
      if (!silent) {
        setSubmitError(
          error instanceof Error
            ? error.message
            : "Backend is offline right now.",
        );
      }
    }
  }

  async function loadProjects() {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = (await parseJsonSafe<{ items?: ProjectItem[] }>(response)) ?? {};
      const items = Array.isArray(data.items) ? data.items : [];
      setProjects(items);

      if (items.length > 0 && !items.some((item) => item.name === projectName)) {
        setProjectName(items[0].name);
      }
    } catch {
      setProjects([]);
    }
  }

  async function loadRecentTasks() {
    try {
      const response = await fetch(`${API_BASE}/tasks`);
      const data = (await parseJsonSafe<TasksListResponse>(response)) ?? {};
      setRecentTasks(Array.isArray(data.items) ? data.items : []);
    } catch {
      setRecentTasks([]);
    }
  }

  async function loadMemory() {
    try {
      const response = await fetch(`${API_BASE}/memory`);
      const data = await parseJsonSafe<MemoryResponse>(response);
      if (!response.ok || !data) {
        throw new Error("Memory request failed.");
      }

      setMemoryData(data);
    } catch {
      setMemoryData(null);
    }
  }

  async function loadLearning() {
    try {
      const response = await fetch(`${API_BASE}/learning`);
      const data = await parseJsonSafe<LearningResponse>(response);
      if (!response.ok || !data) {
        throw new Error("Learning request failed.");
      }

      setLearningData(data);
    } catch {
      setLearningData(null);
    }
  }

  async function loadTask(taskId: string, silent = false) {
    try {
      const response = await fetch(`${API_BASE}/tasks/${taskId}`);
      const data = await parseJsonSafe<TaskRecord>(response);
      if (!response.ok || !data) {
        throw new Error("Task polling failed.");
      }

      setCurrentTask(data);
      setPollError("");

      if (["completed", "failed"].includes(data.status)) {
        await Promise.all([loadRecentTasks(), loadMemory(), loadLearning(), loadSystemStatus(true)]);
      }
    } catch (error) {
      if (!silent) {
        setPollError(
          error instanceof Error
            ? error.message
            : "Task polling failed.",
        );
      }
    }
  }

  useEffect(() => {
    void Promise.all([loadSystemStatus(), loadProjects(), loadRecentTasks(), loadMemory(), loadLearning()]);
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void loadSystemStatus(true);
    }, 15000);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!currentTaskId) {
      return;
    }

    void loadTask(currentTaskId);

    const interval = window.setInterval(() => {
      void loadTask(currentTaskId, true);
    }, 2500);

    return () => window.clearInterval(interval);
  }, [currentTaskId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const command = commandInput.trim();
    if (!command) {
      setSubmitError("Enter a command before submitting.");
      return;
    }

    setSubmitting(true);
    setSubmitError("");
    setPollError("");
    setCurrentTask(null);

    try {
      const response = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          command,
          project_name: projectName || "Default Project",
        }),
      });
      const data = await parseJsonSafe<TaskCreateResponse>(response);

      if (!response.ok || !data?.task_id) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Task creation failed.";
        throw new Error(errorMessage);
      }

      setCommandInput("");
      setCurrentTaskId(data.task_id);
      await Promise.all([loadTask(data.task_id), loadRecentTasks(), loadMemory(), loadLearning(), loadSystemStatus(true)]);
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : "Backend is online, but the task request failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleManualNext() {
    if (!currentTaskId) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/tasks/${currentTaskId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          manual_advance: true,
        }),
      });
      const data = await parseJsonSafe<TaskRecord>(response);
      if (!response.ok || !data) {
        throw new Error("Manual debug advance failed.");
      }

      setCurrentTask(data);
    } catch (error) {
      setPollError(
        error instanceof Error ? error.message : "Manual debug advance failed.",
      );
    }
  }

  async function handleSaveMemoryNote() {
    const note = memoryNote.trim();
    if (!note) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/memory`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          note,
          category: "manual_note",
          project_name: projectName || "Builder Core",
        }),
      });

      const data = await parseJsonSafe<{ ok?: boolean }>(response);
      if (!response.ok || !data?.ok) {
        throw new Error("Could not save the memory note.");
      }

      setMemoryNote("");
      setMemoryMessage("Memory note saved.");
      await loadMemory();
    } catch (error) {
      setMemoryMessage(
        error instanceof Error ? error.message : "Could not save the memory note.",
      );
    }
  }

  async function handleLearningScan() {
    try {
      const response = await fetch(`${API_BASE}/learning/scan`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Learning scan failed.");
      }

      await loadLearning();
    } catch (error) {
      setMemoryMessage(
        error instanceof Error ? error.message : "Learning scan failed.",
      );
    }
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
    <main className="min-h-screen overflow-x-hidden bg-[#f6f7fb] text-slate-900">
      <div className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <h1 className="text-xl font-semibold text-slate-950 sm:text-2xl">Builder Core</h1>
            <p className="text-sm text-slate-500">
              Real backend task tracking, honest bridge checks, project memory, and learning in one place.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${getBackendBadgeClass(backendStatus)}`}>
              {backendStatus === "checking" && "Backend: Checking..."}
              {backendStatus === "online" && "Backend: Online"}
              {backendStatus === "offline" && "Backend: Offline"}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Task Storage: {systemStatus?.task_storage_backend ?? "loading"}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Memory: {systemStatus?.memory_storage_backend ?? "loading"}
            </span>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] lg:px-8">
        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Command Center</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">Send one real backend task</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Builder Core now creates a real backend task, stores it, runs stage updates in the backend, and returns an honest final summary.
                </p>
              </div>

              {bridgeStatus && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Bridge status</p>
                  <p className="mt-1">{bridgeStatus.message ?? "Bridge status unavailable."}</p>
                </div>
              )}
            </div>

            <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="command">
                    Command
                  </label>
                  <textarea
                    id="command"
                    value={commandInput}
                    onChange={(event) => setCommandInput(event.target.value)}
                    placeholder="Ask Builder Core to build, fix, inspect, or upgrade something..."
                    rows={5}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="project-name">
                      Project
                    </label>
                    <input
                      id="project-name"
                      list="project-options"
                      value={projectName}
                      onChange={(event) => setProjectName(event.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                    />
                    <datalist id="project-options">
                      {projects.map((project) => (
                        <option key={project.id} value={project.name} />
                      ))}
                    </datalist>
                  </div>

                  <button
                    type="submit"
                    disabled={submitting || backendStatus !== "online"}
                    className={
                      submitting || backendStatus !== "online"
                        ? "w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                        : "w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                    }
                  >
                    {submitting ? "Creating task..." : "Submit Task"}
                  </button>

                  <button
                    type="button"
                    onClick={handleManualNext}
                    disabled={!currentTaskId}
                    className={
                      currentTaskId
                        ? "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
                        : "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-400"
                    }
                  >
                    Manual Next (debug fallback)
                  </button>
                </div>
              </div>

              {submitError && (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {submitError}
                </div>
              )}

              {systemStatus?.task_storage_message && (
                <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                  {systemStatus.task_storage_message}
                </div>
              )}
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Live Task</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">Backend-controlled progress</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Progress comes from backend task stages, not frontend-only timers.
                </p>
              </div>

              {currentTask && (
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusBadgeClass(currentTask.status)}`}>
                  {currentTask.status}
                </span>
              )}
            </div>

            {currentTask ? (
              <div className="mt-5 space-y-5">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{currentTask.command}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Task ID: {currentTask.id} · Project: {currentTask.project_name ?? "Default Project"}
                      </p>
                    </div>
                    <div className="text-sm font-medium text-slate-700">
                      {titleCaseStage(activeStage)} · {activeProgress}%
                    </div>
                  </div>

                  <div className="mt-4 h-3 rounded-full bg-slate-200">
                    <div
                      className={`h-3 rounded-full transition-all ${getProgressBarClass(currentTask.status)}`}
                      style={{ width: `${Math.max(0, Math.min(activeProgress, 100))}%` }}
                    />
                  </div>

                  <p className="mt-3 text-sm text-slate-600">
                    {currentTask.status === "failed"
                      ? `${titleCaseStage(activeStage)} stopped. Review the errors and summary below.`
                      : currentTask.status === "completed"
                        ? "Task complete. Review the final summary and learning notes."
                        : `${titleCaseStage(activeStage)} in progress...`}
                  </p>

                  {currentTask.workflow_status && (
                    <p className="mt-2 text-xs text-slate-500">Workflow: {currentTask.workflow_status}</p>
                  )}
                  {currentTask.github_commit && (
                    <p className="mt-1 text-xs text-slate-500">Latest commit: {currentTask.github_commit}</p>
                  )}
                </div>

                {pollError && (
                  <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    {pollError}
                  </div>
                )}

                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-3xl border border-slate-200 p-4">
                    <p className="text-sm font-semibold text-slate-900">Live Logs</p>
                    <div className="mt-3 max-h-72 overflow-y-auto rounded-2xl bg-slate-50 p-3">
                      {taskLogs.length > 0 ? (
                        <ul className="space-y-2 text-sm text-slate-700">
                          {taskLogs.map((log, index) => (
                            <li key={`${log}-${index}`} className="rounded-xl border border-slate-200 bg-white px-3 py-2">
                              {log}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-slate-500">No logs yet.</p>
                      )}
                    </div>
                  </div>

                  <div className="rounded-3xl border border-slate-200 p-4">
                    <p className="text-sm font-semibold text-slate-900">Errors</p>
                    <div className="mt-3 rounded-2xl bg-slate-50 p-3">
                      {taskErrors.length > 0 ? (
                        <ul className="space-y-2 text-sm text-red-700">
                          {taskErrors.map((error, index) => (
                            <li key={`${error}-${index}`} className="rounded-xl border border-red-200 bg-red-50 px-3 py-2">
                              {error}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-slate-500">No errors reported for this task.</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-slate-200 p-4">
                  <p className="text-sm font-semibold text-slate-900">Final Summary</p>
                  {currentTask.summary ? (
                    <div className="mt-3 space-y-4 text-sm text-slate-700">
                      <div className="rounded-2xl bg-slate-50 p-4">
                        <p className="font-semibold text-slate-900">{currentTask.summary.message ?? "Summary ready."}</p>
                        <p className="mt-2 text-xs text-slate-500">
                          Updated: {formatTimestamp(currentTask.summary.updated_at)}
                        </p>
                      </div>

                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-2xl bg-slate-50 p-4">
                          <p className="font-semibold text-slate-900">What completed</p>
                          <ul className="mt-3 space-y-2">
                            {(currentTask.summary.what_completed ?? []).map((item, index) => (
                              <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="rounded-2xl bg-slate-50 p-4">
                          <p className="font-semibold text-slate-900">Manual setup still needed</p>
                          <ul className="mt-3 space-y-2">
                            {(currentTask.summary.what_still_needs_manual_setup ?? []).map((item, index) => (
                              <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <div className="rounded-2xl bg-slate-50 p-4">
                        <p className="font-semibold text-slate-900">Next recommended step</p>
                        <p className="mt-2">{currentTask.summary.next_recommended_step ?? "No next step recorded yet."}</p>
                      </div>

                      <div className="rounded-2xl bg-slate-50 p-4">
                        <p className="font-semibold text-slate-900">Folder used</p>
                        <p className="mt-2 break-all">{currentTask.summary.folder_used ?? "Unknown"}</p>
                      </div>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">The backend summary will appear here when the task reaches the summary stage.</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="mt-5 rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                Submit a command to create a real backend task, then Builder Core will poll its live status here.
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Install</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Use Builder Core from your phone</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">iPhone</p>
                <p className="mt-2">Open the app in Safari, tap Share, then choose Add to Home Screen.</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">Android</p>
                <p className="mt-2">Open the app in Chrome, open the menu, then choose Install App or Add to Home Screen.</p>
              </div>
            </div>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleOpenAppLink}
                className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
              >
                Open App Link
              </button>
              <button
                type="button"
                onClick={handleCopyAppLink}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
              >
                Copy App Link
              </button>
            </div>
            <p className="mt-3 text-sm text-slate-500">No App Store needed.</p>
            {installMessage && <p className="mt-2 text-sm text-slate-700">{installMessage}</p>}
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">System</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Backend and bridge</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Backend connection</p>
                <p className="mt-2">
                  {backendStatus === "online"
                    ? "Backend is online."
                    : backendStatus === "offline"
                      ? "Backend is offline."
                      : "Checking backend status..."}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Bridge message</p>
                <p className="mt-2">{bridgeStatus?.message ?? "Bridge status will appear here."}</p>
                {bridgeStatus?.missing && bridgeStatus.missing.length > 0 && (
                  <ul className="mt-3 space-y-2 text-xs text-slate-600">
                    {bridgeStatus.missing.map((item) => (
                      <li key={item} className="rounded-xl bg-white px-3 py-2">
                        Missing: {item}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Storage</p>
                <ul className="mt-2 space-y-2 text-xs text-slate-600">
                  <li>Tasks: {systemStatus?.task_storage_backend ?? "Unknown"}</li>
                  <li>Memory: {systemStatus?.memory_storage_backend ?? "Unknown"}</li>
                  <li>Files: {systemStatus?.file_storage_backend ?? "Unknown"}</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Memory</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">Builder memory</h2>
              </div>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Latest saved task summary</p>
                {memoryData?.latest_summary ? (
                  <div className="mt-2 text-sm text-slate-700">
                    <p>{memoryData.latest_summary.message ?? "Summary available."}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      Task: {memoryData.latest_summary.task_id ?? "Unknown"} · {formatTimestamp(memoryData.latest_summary.updated_at)}
                    </p>
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No saved summary yet.</p>
                )}
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Add a manual project note</p>
                <textarea
                  value={memoryNote}
                  onChange={(event) => setMemoryNote(event.target.value)}
                  rows={3}
                  placeholder="Write a short project note or reminder..."
                  className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <button
                  type="button"
                  onClick={handleSaveMemoryNote}
                  className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
                >
                  Save Memory Note
                </button>
                {memoryMessage && <p className="mt-2 text-xs text-slate-600">{memoryMessage}</p>}
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recent memory entries</p>
                <ul className="mt-3 space-y-2 text-sm text-slate-700">
                  {(memoryData?.project_memory ?? []).slice(0, 6).map((entry) => (
                    <li key={entry.id} className="rounded-xl bg-white px-3 py-3">
                      <p className="font-medium text-slate-900">{entry.type ?? "memory"}</p>
                      <p className="mt-1">{entry.note ?? entry.command ?? "Saved entry"}</p>
                      <p className="mt-2 text-xs text-slate-500">{formatTimestamp(entry.created_at)}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Learning</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">Project knowledge</h2>
              </div>
              <button
                type="button"
                onClick={handleLearningScan}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700"
              >
                Scan Project
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Known issues</p>
                <ul className="mt-3 space-y-2 text-sm text-slate-700">
                  {(learningData?.known_issues ?? memoryData?.known_environment_problems ?? []).slice(0, 6).map((item, index) => (
                    <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recommended next steps</p>
                <ul className="mt-3 space-y-2 text-sm text-slate-700">
                  {(learningData?.recommended_next_steps ?? []).slice(0, 6).map((item, index) => (
                    <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Latest lessons</p>
                <ul className="mt-3 space-y-3 text-sm text-slate-700">
                  {(learningData?.lessons ?? []).slice(0, 5).map((lesson) => (
                    <li key={lesson.id} className="rounded-xl bg-white px-3 py-3">
                      <p className="font-medium text-slate-900">{lesson.command ?? "Task lesson"}</p>
                      <p className="mt-1">{lesson.lesson_learned ?? "No lesson text recorded yet."}</p>
                      {lesson.next_recommendation && (
                        <p className="mt-2 text-xs text-slate-500">Next: {lesson.next_recommendation}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Project structure summary</p>
                {learningData?.project_structure_summary ? (
                  <div className="mt-3 space-y-3 text-sm text-slate-700">
                    <p>Scanned: {formatTimestamp(learningData.project_structure_summary.scanned_at)}</p>
                    <div>
                      <p className="font-medium text-slate-900">Top folders</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(learningData.project_structure_summary.top_level_folders ?? []).slice(0, 8).map((item) => (
                          <span key={item} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl bg-white p-3 text-xs text-slate-600">
                      <pre className="overflow-x-auto whitespace-pre-wrap">
                        {(learningData.project_structure_summary.sample_tree ?? []).slice(0, 20).join("\n")}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No project scan is saved yet.</p>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Recent Tasks</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Saved task history</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-700">
              {recentTasks.slice(0, 8).map((task) => (
                <li key={task.id} className="rounded-2xl bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-900">{task.command}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {titleCaseStage(task.stage ?? task.current_stage)} · {task.progress}% · {formatTimestamp(task.updated_at)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setCurrentTaskId(task.id);
                        void loadTask(task.id);
                      }}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700"
                    >
                      Open
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </main>
  );
}
