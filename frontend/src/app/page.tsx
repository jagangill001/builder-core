"use client";

import { type FormEvent, useEffect, useState } from "react";

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
};

type SystemStatusResponse = {
  status?: string;
  service?: string;
  manual_codex_mode?: boolean;
  bridge_status?: BridgeStatus;
  task_storage_backend?: string;
  task_storage_message?: string;
  memory_storage_backend?: string;
  memory_storage_message?: string;
  latest_summary_available?: boolean;
  latest_prompt_available?: boolean;
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
  codex_summary?: string;
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
  generated_prompt?: string | null;
  codex_summary?: string | null;
  logs?: string[];
  errors?: string[];
  summary?: TaskSummary | null;
  bridge_status?: BridgeStatus;
  files_changed?: string[];
  known_issues?: string[];
  what_completed?: string[];
  what_remains?: string[];
  next_recommended_step?: string | null;
  created_at?: string;
  updated_at?: string;
};

type LatestPromptResponse = {
  ok?: boolean;
  message?: string;
  item?: {
    task_id?: string;
    command?: string;
    project_name?: string;
    status?: string;
    prompt?: string;
    created_at?: string;
  } | null;
};

type PromptCreateResponse = {
  task_id: string;
  prompt: string;
  status: string;
};

type MemoryEntry = {
  id: string;
  type?: string;
  note?: string;
  command?: string;
  project_name?: string;
  created_at?: string;
};

type MemoryResponse = {
  ok?: boolean;
  storage_backend?: string;
  storage_message?: string;
  project_memory?: MemoryEntry[];
  latest_summary?: TaskSummary | null;
  latest_prompt?: {
    task_id?: string;
    command?: string;
    prompt?: string;
    status?: string;
    created_at?: string;
  } | null;
  prompt_history?: {
    task_id?: string;
    command?: string;
    prompt?: string;
    status?: string;
    created_at?: string;
  }[];
  latest_bridge_status?: BridgeStatus | null;
  known_environment_problems?: string[];
};

type Lesson = {
  id: string;
  task_id?: string;
  command?: string;
  lesson_learned?: string;
  next_recommendation?: string;
  files_changed?: string[];
  error?: string | null;
  created_at?: string;
};

type LearningResponse = {
  ok?: boolean;
  lessons?: Lesson[];
  known_issues?: string[];
  recommended_next_steps?: string[];
  project_structure_summary?: {
    root?: string;
    top_level_folders?: string[];
    important_files?: string[];
    sample_tree?: string[];
  } | null;
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
  const [projectName, setProjectName] = useState("Builder Core");
  const [commandInput, setCommandInput] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [currentTaskId, setCurrentTaskId] = useState("");
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [codexSummaryInput, setCodexSummaryInput] = useState("");
  const [recentTasks, setRecentTasks] = useState<TaskRecord[]>([]);
  const [memoryData, setMemoryData] = useState<MemoryResponse | null>(null);
  const [learningData, setLearningData] = useState<LearningResponse | null>(null);
  const [submitMessage, setSubmitMessage] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [installMessage, setInstallMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [savingSummary, setSavingSummary] = useState(false);

  const activeBridgeStatus = currentTask?.bridge_status ?? systemStatus?.bridge_status ?? null;

  async function loadSystemStatus() {
    try {
      const response = await fetch(`${API_BASE}/system/status`);
      const data = await parseJsonSafe<SystemStatusResponse>(response);
      if (!response.ok || !data) {
        throw new Error("System status request failed.");
      }

      setSystemStatus(data);
      setBackendStatus("online");
    } catch {
      setBackendStatus("offline");
      setSystemStatus(null);
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
      const data = (await parseJsonSafe<{ items?: TaskRecord[] }>(response)) ?? {};
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

  async function loadLatestPrompt() {
    try {
      const response = await fetch(`${API_BASE}/prompts/latest`);
      const data = await parseJsonSafe<LatestPromptResponse>(response);
      if (!response.ok || !data?.ok || !data.item) {
        return;
      }

      setGeneratedPrompt(data.item.prompt ?? "");
      if (data.item.task_id) {
        setCurrentTaskId(data.item.task_id);
      }
      if (data.item.command) {
        setCommandInput(data.item.command);
      }
    } catch {
      return;
    }
  }

  async function loadTask(taskId: string) {
    try {
      const response = await fetch(`${API_BASE}/tasks/${taskId}`);
      const data = await parseJsonSafe<TaskRecord>(response);
      if (!response.ok || !data) {
        throw new Error("Task request failed.");
      }

      setCurrentTask(data);
      if (data.generated_prompt) {
        setGeneratedPrompt(data.generated_prompt);
      }
    } catch {
      setCurrentTask(null);
    }
  }

  useEffect(() => {
    void Promise.all([
      loadSystemStatus(),
      loadProjects(),
      loadRecentTasks(),
      loadMemory(),
      loadLearning(),
      loadLatestPrompt(),
    ]);
  }, []);

  useEffect(() => {
    if (!currentTaskId) {
      return;
    }

    void loadTask(currentTaskId);
    const interval = window.setInterval(() => {
      void loadTask(currentTaskId);
    }, 5000);

    return () => window.clearInterval(interval);
  }, [currentTaskId]);

  async function handleGeneratePrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const command = commandInput.trim();
    if (!command) {
      setSubmitMessage("Enter a command first.");
      return;
    }

    setSubmitting(true);
    setSubmitMessage("");
    setCopyMessage("");

    try {
      const response = await fetch(`${API_BASE}/prompts/codex`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          command,
          project_name: projectName || "Builder Core",
        }),
      });
      const data = await parseJsonSafe<PromptCreateResponse>(response);
      if (!response.ok || !data?.task_id || !data.prompt) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Prompt generation failed.";
        throw new Error(errorMessage);
      }

      setCurrentTaskId(data.task_id);
      setGeneratedPrompt(data.prompt);
      setCodexSummaryInput("");
      setSubmitMessage("Codex prompt generated. Copy it into Codex, let Codex do the repo work, then paste Codex’s final summary back here.");
      await Promise.all([loadTask(data.task_id), loadMemory(), loadLearning(), loadRecentTasks(), loadSystemStatus()]);
    } catch (error) {
      setSubmitMessage(
        error instanceof Error ? error.message : "Prompt generation failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCopyPrompt() {
    if (!generatedPrompt) {
      return;
    }

    try {
      await navigator.clipboard.writeText(generatedPrompt);
      setCopyMessage("Prompt copied.");
    } catch {
      setCopyMessage("Copy failed. Select the prompt manually.");
    }
  }

  async function handleSaveCodexSummary() {
    if (!currentTaskId) {
      setSubmitMessage("Generate a prompt first so Builder Core has a task ID.");
      return;
    }

    const codexSummary = codexSummaryInput.trim();
    if (!codexSummary) {
      setSubmitMessage("Paste Codex’s final summary before saving.");
      return;
    }

    setSavingSummary(true);
    setSubmitMessage("");

    try {
      const response = await fetch(`${API_BASE}/tasks/${currentTaskId}/codex-summary`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          codex_summary: codexSummary,
        }),
      });
      const data = await parseJsonSafe<{ ok?: boolean; message?: string }>(response);
      if (!response.ok || !data?.ok) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : data?.message ?? "Saving Codex summary failed.";
        throw new Error(errorMessage);
      }

      setSubmitMessage("Codex summary saved. Builder Core updated project memory and learning.");
      await Promise.all([loadTask(currentTaskId), loadMemory(), loadLearning(), loadRecentTasks(), loadSystemStatus()]);
    } catch (error) {
      setSubmitMessage(
        error instanceof Error ? error.message : "Saving Codex summary failed.",
      );
    } finally {
      setSavingSummary(false);
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
              Codex Prompt Command Center for manual repo changes with saved memory and lessons.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
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
              Mode: Manual Codex
            </span>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] lg:px-8">
        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Main Workflow</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Generate a Codex prompt</h2>
            <p className="mt-2 text-sm text-slate-600">
              Builder Core does not automatically edit GitHub yet. Copy this prompt into Codex, let Codex make the changes, then paste Codex’s final summary back here.
            </p>

            <form className="mt-5 space-y-4" onSubmit={handleGeneratePrompt}>
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="command">
                    Command
                  </label>
                  <textarea
                    id="command"
                    value={commandInput}
                    onChange={(event) => setCommandInput(event.target.value)}
                    placeholder="Tell Builder Core what to build, fix, or upgrade..."
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
                    {submitting ? "Generating..." : "Generate Codex Prompt"}
                  </button>
                </div>
              </div>

              {submitMessage && (
                <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                  {submitMessage}
                </div>
              )}
            </form>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Generated Prompt</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-950">Copy this into Codex</h2>
              </div>

              <button
                type="button"
                onClick={handleCopyPrompt}
                disabled={!generatedPrompt}
                className={
                  generatedPrompt
                    ? "rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
                    : "rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-400"
                }
              >
                Copy Prompt
              </button>
            </div>

            <div className="mt-4 rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span>Task ID: {currentTaskId || "Not created yet"}</span>
                <span>·</span>
                <span>Status: {currentTask?.status ?? "waiting"}</span>
                <span>·</span>
                <span>Stage: {titleCaseStage(currentTask?.stage ?? currentTask?.current_stage)}</span>
              </div>

              <textarea
                value={generatedPrompt}
                readOnly
                rows={18}
                className="mt-4 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                placeholder="Your generated Codex prompt will appear here."
              />
              {copyMessage && <p className="mt-2 text-xs text-slate-600">{copyMessage}</p>}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Codex Result</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Paste Codex final summary back into Builder Core</h2>
            <textarea
              value={codexSummaryInput}
              onChange={(event) => setCodexSummaryInput(event.target.value)}
              rows={10}
              placeholder="Paste Codex’s final summary or implementation report here..."
              className="mt-4 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
            />
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleSaveCodexSummary}
                disabled={savingSummary || !currentTaskId}
                className={
                  savingSummary || !currentTaskId
                    ? "rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                    : "rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                }
              >
                {savingSummary ? "Saving..." : "Save Codex Summary"}
              </button>
              <p className="text-sm text-slate-500">
                Saving the summary updates task history, project memory, latest summary, and learning lessons.
              </p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Task Status</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Tracked backend task</h2>
            {currentTask ? (
              <div className="mt-4 space-y-4">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-sm font-semibold text-slate-900">{currentTask.command}</p>
                    <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                      {currentTask.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    {titleCaseStage(currentTask.stage ?? currentTask.current_stage)} · {currentTask.progress}%
                  </p>
                  <div className="mt-3 h-3 rounded-full bg-slate-200">
                    <div
                      className={
                        currentTask.status === "failed"
                          ? "h-3 rounded-full bg-red-500"
                          : currentTask.status.startsWith("completed")
                            ? "h-3 rounded-full bg-green-600"
                            : "h-3 rounded-full bg-blue-600"
                      }
                      style={{ width: `${Math.max(0, Math.min(currentTask.progress, 100))}%` }}
                    />
                  </div>
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="font-semibold text-slate-900">Logs</p>
                    <ul className="mt-3 space-y-2 text-sm text-slate-700">
                      {(currentTask.logs ?? []).map((log, index) => (
                        <li key={`${log}-${index}`} className="rounded-xl bg-white px-3 py-2">
                          {log}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="font-semibold text-slate-900">Errors / Known Issues</p>
                    <ul className="mt-3 space-y-2 text-sm text-slate-700">
                      {[...(currentTask.errors ?? []), ...(currentTask.known_issues ?? [])].map((item, index) => (
                        <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">Latest saved summary</p>
                  {currentTask.summary ? (
                    <div className="mt-3 space-y-3 text-sm text-slate-700">
                      <p>{currentTask.summary.message}</p>
                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-xl bg-white p-3">
                          <p className="font-medium text-slate-900">What completed</p>
                          <ul className="mt-2 space-y-2">
                            {(currentTask.summary.what_completed ?? []).map((item, index) => (
                              <li key={`${item}-${index}`}>{item}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="rounded-xl bg-white p-3">
                          <p className="font-medium text-slate-900">Still needs manual setup</p>
                          <ul className="mt-2 space-y-2">
                            {(currentTask.summary.what_still_needs_manual_setup ?? []).map((item, index) => (
                              <li key={`${item}-${index}`}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">
                        Updated: {formatTimestamp(currentTask.summary.updated_at)}
                      </p>
                    </div>
                  ) : (
                    <p className="mt-2 text-sm text-slate-500">No summary has been saved for this task yet.</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500">Generate a prompt to create a tracked task.</p>
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
            {installMessage && <p className="mt-3 text-sm text-slate-600">{installMessage}</p>}
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Bridge Status</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Manual-Codex safety mode</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Backend message</p>
                <p className="mt-2">{activeBridgeStatus?.message ?? "Bridge status not loaded yet."}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Why this mode is safer</p>
                <ul className="mt-2 space-y-2">
                  <li>Builder Core tracks the task and context.</li>
                  <li>You review and paste the prompt into Codex manually.</li>
                  <li>No fake GitHub or Codex automation is claimed.</li>
                  <li>Project memory and lessons still improve after each task.</li>
                </ul>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Still disabled</p>
                <p className="mt-2">Real GitHub automatic execution remains disabled in the main workflow.</p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Latest Summary</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Most recent saved outcome</h2>
            {memoryData?.latest_summary ? (
              <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">{memoryData.latest_summary.message}</p>
                <p className="mt-2">Task: {memoryData.latest_summary.task_id ?? "Unknown"}</p>
                <p className="mt-2 text-xs text-slate-500">
                  Updated: {formatTimestamp(memoryData.latest_summary.updated_at)}
                </p>
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-500">No saved summary yet.</p>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Memory</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Project memory</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-700">
              {(memoryData?.project_memory ?? []).slice(0, 6).map((entry) => (
                <li key={entry.id} className="rounded-2xl bg-slate-50 p-4">
                  <p className="font-medium text-slate-900">{entry.type ?? "memory"}</p>
                  <p className="mt-1">{entry.note ?? entry.command ?? "Saved memory entry"}</p>
                  <p className="mt-2 text-xs text-slate-500">{formatTimestamp(entry.created_at)}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Learning</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Lessons and next steps</h2>
            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Known issues</p>
                <ul className="mt-2 space-y-2 text-sm text-slate-700">
                  {(learningData?.known_issues ?? []).slice(0, 6).map((issue, index) => (
                    <li key={`${issue}-${index}`} className="rounded-xl bg-white px-3 py-2">
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recommended next steps</p>
                <ul className="mt-2 space-y-2 text-sm text-slate-700">
                  {(learningData?.recommended_next_steps ?? []).slice(0, 6).map((item, index) => (
                    <li key={`${item}-${index}`} className="rounded-xl bg-white px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Latest lessons</p>
                <ul className="mt-2 space-y-3 text-sm text-slate-700">
                  {(learningData?.lessons ?? []).slice(0, 5).map((lesson) => (
                    <li key={lesson.id} className="rounded-xl bg-white px-3 py-3">
                      <p className="font-medium text-slate-900">{lesson.command ?? "Task lesson"}</p>
                      <p className="mt-1">{lesson.lesson_learned ?? "No lesson saved yet."}</p>
                      {lesson.next_recommendation && (
                        <p className="mt-2 text-xs text-slate-500">Next: {lesson.next_recommendation}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Recent Tasks</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-950">Prompt history</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-700">
              {recentTasks.slice(0, 8).map((task) => (
                <li key={task.id} className="rounded-2xl bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-slate-900">{task.command}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {task.id} · {task.status} · {formatTimestamp(task.updated_at)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setCurrentTaskId(task.id);
                        void loadTask(task.id);
                        setGeneratedPrompt(task.generated_prompt ?? "");
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
