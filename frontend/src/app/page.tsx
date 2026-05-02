"use client";

import { type FormEvent, type ReactNode, useEffect, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const FRONTEND_APP_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";

const ASSISTANT_MODES = [
  { value: "general", label: "General" },
  { value: "coding", label: "Coding" },
  { value: "research", label: "Research" },
  { value: "law", label: "Law" },
  { value: "market", label: "Market" },
  { value: "exam", label: "Exam" },
  { value: "project", label: "Project" },
  { value: "creative", label: "Creative" },
];

const RESEARCH_CATEGORIES = [
  { value: "general", label: "General" },
  { value: "coding", label: "Coding" },
  { value: "law", label: "Law" },
  { value: "market", label: "Market" },
  { value: "exam", label: "Exam" },
  { value: "politics", label: "Politics" },
  { value: "history", label: "History" },
  { value: "language", label: "Language" },
  { value: "project", label: "Project" },
];

type ProjectItem = {
  id: number;
  name: string;
};

type AssistantStatus = {
  mode?: string;
  model?: string | null;
  api_configured?: boolean;
  local_fallback_active?: boolean;
  message?: string;
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

type IntelligenceFirewall = {
  risk_level?: string;
  blocked?: boolean;
  message?: string;
  do?: string[];
  do_not?: string[];
  manual_limits?: string[];
};

type IntelligenceBrief = {
  id?: string;
  command?: string;
  project_name?: string;
  mode?: string;
  title?: string;
  overview?: string;
  status_message?: string;
  safety_firewall?: IntelligenceFirewall;
  research_steps?: string[];
  evidence_checklist?: string[];
  next_questions?: string[];
  codex_focus?: string[];
  output_outline?: string[];
  memory_signals?: string[];
  lesson_signals?: string[];
  recent_summary_note?: string;
  recommended_memory_note?: string;
  created_at?: string;
};

type SystemStatusResponse = {
  status?: string;
  service?: string;
  manual_codex_mode?: boolean;
  intelligence_center_enabled?: boolean;
  assistant_enabled?: boolean;
  assistant_status?: AssistantStatus;
  research_system_enabled?: boolean;
  bridge_status?: BridgeStatus;
  memory_storage_backend?: string;
  memory_storage_message?: string;
  cloud_ready_notes?: string[];
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
  intelligence_mode?: string | null;
  intelligence_brief?: IntelligenceBrief | null;
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

type PromptCreateResponse = {
  task_id: string;
  prompt: string;
  status: string;
  intelligence_brief?: IntelligenceBrief;
};

type LatestPromptResponse = {
  ok?: boolean;
  item?: {
    task_id?: string;
    command?: string;
    project_name?: string;
    status?: string;
    prompt?: string;
    created_at?: string;
  } | null;
};

type MemoryEntry = {
  id: string;
  type?: string;
  note?: string;
  command?: string;
  project_name?: string;
  created_at?: string;
  mode?: string;
  user_message?: string;
};

type ResearchTaskRecord = {
  research_id: string;
  topic: string;
  goal: string;
  category: string;
  sources: string[];
  status: string;
  summary: string;
  findings: string[];
  limitations: string[];
  next_steps: string[];
  web_connected?: boolean;
  created_at?: string;
  updated_at?: string;
};

type MemoryResponse = {
  ok?: boolean;
  storage_backend?: string;
  storage_message?: string;
  project_memory?: MemoryEntry[];
  assistant_memory?: MemoryEntry[];
  chat_history?: AssistantHistoryItem[];
  research_tasks?: ResearchTaskRecord[];
  research_results?: ResearchTaskRecord[];
  self_improvement?: SelfImprovementItem[];
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
  latest_intelligence_brief?: IntelligenceBrief | null;
  intelligence_history?: IntelligenceBrief[];
  latest_bridge_status?: BridgeStatus | null;
  known_environment_problems?: string[];
  cloud_ready_notes?: string[];
};

type Lesson = {
  id: string;
  task_id?: string;
  command?: string;
  lesson_learned?: string;
  next_recommendation?: string;
  files_changed?: string[];
  error?: string | null;
  intelligence_mode?: string;
  created_at?: string;
};

type LearningResponse = {
  ok?: boolean;
  lessons?: Lesson[];
  known_issues?: string[];
  recommended_next_steps?: string[];
  recent_intelligence_modes?: string[];
  project_structure_summary?: {
    root?: string;
    top_level_folders?: string[];
    important_files?: string[];
    sample_tree?: string[];
  } | null;
  notes?: string[];
};

type AssistantHistoryItem = {
  id: string;
  chat_id?: string;
  role?: string;
  mode?: string;
  message?: string;
  suggestions?: string[];
  next_actions?: string[];
  memory_used?: string[];
  created_at?: string;
};

type AssistantChatResponse = {
  chat_id: string;
  reply: string;
  suggestions: string[];
  memory_used: string[];
  saved_to_memory: boolean;
  next_actions: string[];
  created_at: string;
  assistant_status?: AssistantStatus;
};

type AssistantIdea = {
  idea_title: string;
  why_it_is_useful: string;
  difficulty: string;
  possible_next_step: string;
  risk_or_limitation: string;
};

type AssistantIdeaResponse = {
  ideas: AssistantIdea[];
  best_idea: string;
  why: string;
  next_steps: string[];
  created_at: string;
};

type SelfImprovementItem = {
  id: string;
  category?: string;
  user_message?: string;
  assistant_reply?: string;
  what_worked?: string;
  what_failed?: string;
  better_future_instruction?: string;
  repeated_user_preferences?: string[];
  project_mistake?: string;
  project_lesson?: string;
  next_recommended_improvement?: string;
  created_at?: string;
};

type SelfImprovementResponse = {
  ok?: boolean;
  items?: SelfImprovementItem[];
  next_recommended_upgrade?: string;
  notes?: string[];
  storage_backend?: string;
  storage_message?: string;
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

function titleCase(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

  return value
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

function SectionCard({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{eyebrow}</p>
      <h2 className="mt-2 text-lg font-semibold text-slate-950">{title}</h2>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function ListPanel({ title, items }: { title: string; items: string[] | undefined }) {
  const safeItems = items?.filter(Boolean) ?? [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="font-semibold text-slate-900">{title}</p>
      {safeItems.length > 0 ? (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {safeItems.map((item, index) => (
            <li key={`${title}-${index}`} className="rounded-xl bg-white px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">Nothing saved yet.</p>
      )}
    </div>
  );
}

function MemoryList({
  title,
  items,
  emptyText,
}: {
  title: string;
  items: MemoryEntry[] | undefined;
  emptyText: string;
}) {
  const safeItems = items ?? [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="font-semibold text-slate-900">{title}</p>
      {safeItems.length > 0 ? (
        <ul className="mt-3 space-y-3 text-sm text-slate-700">
          {safeItems.map((item) => (
            <li key={item.id} className="rounded-xl bg-white px-3 py-3">
              <p className="font-medium text-slate-900">{item.note ?? item.command ?? item.user_message ?? "Saved entry"}</p>
              <p className="mt-1 text-xs text-slate-500">
                {item.type ? `${titleCase(item.type)} · ` : ""}
                {formatTimestamp(item.created_at)}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}

function TaskSummaryPanel({ summary }: { summary: TaskSummary | null | undefined }) {
  if (!summary) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No latest summary saved yet.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-semibold text-slate-900">
        {summary.final_status ? titleCase(summary.final_status) : "Latest Summary"}
      </p>
      <p className="mt-2 text-sm text-slate-700">{summary.message ?? "Summary saved."}</p>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <ListPanel title="Completed" items={summary.what_completed} />
        <ListPanel title="Manual Setup Remaining" items={summary.what_still_needs_manual_setup} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <ListPanel title="Files Changed" items={summary.files_changed} />
        <ListPanel title="Errors" items={summary.errors} />
      </div>
      {summary.next_recommended_step && (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          Next recommended step: {summary.next_recommended_step}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectName, setProjectName] = useState("Builder Core");

  const [assistantMessage, setAssistantMessage] = useState("");
  const [assistantMode, setAssistantMode] = useState("general");
  const [assistantSaveToMemory, setAssistantSaveToMemory] = useState(true);
  const [assistantSubmitting, setAssistantSubmitting] = useState(false);
  const [assistantResponse, setAssistantResponse] = useState<AssistantChatResponse | null>(null);
  const [assistantHistory, setAssistantHistory] = useState<AssistantHistoryItem[]>([]);
  const [assistantMessageStatus, setAssistantMessageStatus] = useState("");

  const [ideaTopic, setIdeaTopic] = useState("");
  const [ideaGoal, setIdeaGoal] = useState("");
  const [ideaSubmitting, setIdeaSubmitting] = useState(false);
  const [ideaResult, setIdeaResult] = useState<AssistantIdeaResponse | null>(null);
  const [ideaMessage, setIdeaMessage] = useState("");

  const [commandInput, setCommandInput] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [currentTaskId, setCurrentTaskId] = useState("");
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [codexSummaryInput, setCodexSummaryInput] = useState("");
  const [promptSubmitting, setPromptSubmitting] = useState(false);
  const [promptMessage, setPromptMessage] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [savingSummary, setSavingSummary] = useState(false);

  const [researchTopic, setResearchTopic] = useState("");
  const [researchGoal, setResearchGoal] = useState("");
  const [researchCategory, setResearchCategory] = useState("general");
  const [researchSources, setResearchSources] = useState<string[]>(["memory"]);
  const [researchSubmitting, setResearchSubmitting] = useState(false);
  const [researchMessage, setResearchMessage] = useState("");
  const [researchTasks, setResearchTasks] = useState<ResearchTaskRecord[]>([]);
  const [selectedResearchTask, setSelectedResearchTask] = useState<ResearchTaskRecord | null>(null);

  const [memoryData, setMemoryData] = useState<MemoryResponse | null>(null);
  const [learningData, setLearningData] = useState<LearningResponse | null>(null);
  const [selfImprovementData, setSelfImprovementData] = useState<SelfImprovementResponse | null>(null);
  const [manualImprovementNote, setManualImprovementNote] = useState("");
  const [savingImprovement, setSavingImprovement] = useState(false);
  const [improvementMessage, setImprovementMessage] = useState("");
  const [installMessage, setInstallMessage] = useState("");

  const latestIntelligenceBrief =
    currentTask?.intelligence_brief ?? memoryData?.latest_intelligence_brief ?? null;
  const activeBridgeStatus = currentTask?.bridge_status ?? memoryData?.latest_bridge_status ?? systemStatus?.bridge_status ?? null;

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
      setSystemStatus(null);
      setBackendStatus("offline");
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

  async function loadSelfImprovement() {
    try {
      const response = await fetch(`${API_BASE}/self-improvement`);
      const data = await parseJsonSafe<SelfImprovementResponse>(response);
      if (!response.ok || !data) {
        throw new Error("Self-improvement request failed.");
      }
      setSelfImprovementData(data);
    } catch {
      setSelfImprovementData(null);
    }
  }

  async function loadAssistantHistory() {
    try {
      const response = await fetch(`${API_BASE}/assistant/history`);
      const data = (await parseJsonSafe<{ items?: AssistantHistoryItem[] }>(response)) ?? {};
      setAssistantHistory(Array.isArray(data.items) ? data.items : []);
    } catch {
      setAssistantHistory([]);
    }
  }

  async function loadResearchTasks() {
    try {
      const response = await fetch(`${API_BASE}/research/tasks`);
      const data = (await parseJsonSafe<{ items?: ResearchTaskRecord[] }>(response)) ?? {};
      const items = Array.isArray(data.items) ? data.items : [];
      setResearchTasks(items);
      if (!selectedResearchTask && items.length > 0) {
        setSelectedResearchTask(items[0]);
      }
    } catch {
      setResearchTasks([]);
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

  async function refreshSharedPanels() {
    await Promise.all([
      loadSystemStatus(),
      loadMemory(),
      loadLearning(),
      loadSelfImprovement(),
      loadAssistantHistory(),
      loadResearchTasks(),
    ]);
  }

  useEffect(() => {
    void Promise.all([
      loadSystemStatus(),
      loadProjects(),
      loadMemory(),
      loadLearning(),
      loadSelfImprovement(),
      loadAssistantHistory(),
      loadResearchTasks(),
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

  async function handleAssistantSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const message = assistantMessage.trim();
    if (!message) {
      setAssistantMessageStatus("Enter a message first.");
      return;
    }

    setAssistantSubmitting(true);
    setAssistantMessageStatus("");

    try {
      const response = await fetch(`${API_BASE}/assistant/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          mode: assistantMode,
          save_to_memory: assistantSaveToMemory,
        }),
      });
      const data = await parseJsonSafe<AssistantChatResponse>(response);
      if (!response.ok || !data?.chat_id) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Assistant chat failed.";
        throw new Error(errorMessage);
      }

      setAssistantResponse(data);
      setAssistantMessageStatus(
        assistantSaveToMemory
          ? "Assistant reply saved to memory."
          : "Assistant reply ready. You can save important details later.",
      );
      await refreshSharedPanels();
    } catch (error) {
      setAssistantMessageStatus(error instanceof Error ? error.message : "Assistant chat failed.");
    } finally {
      setAssistantSubmitting(false);
    }
  }

  async function handleIdeaGeneration() {
    const topic = ideaTopic.trim() || assistantMessage.trim() || commandInput.trim();
    const goal = ideaGoal.trim() || "Find the next safe and useful improvement.";

    if (!topic) {
      setIdeaMessage("Enter a topic or reuse the assistant message first.");
      return;
    }

    setIdeaSubmitting(true);
    setIdeaMessage("");
    try {
      const response = await fetch(`${API_BASE}/assistant/idea`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic,
          goal,
        }),
      });
      const data = await parseJsonSafe<AssistantIdeaResponse>(response);
      if (!response.ok || !data?.ideas) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Idea generation failed.";
        throw new Error(errorMessage);
      }
      setIdeaResult(data);
      setIdeaMessage("Ideas generated.");
    } catch (error) {
      setIdeaMessage(error instanceof Error ? error.message : "Idea generation failed.");
    } finally {
      setIdeaSubmitting(false);
    }
  }

  function toggleResearchSource(source: string) {
    setResearchSources((previous) => {
      if (previous.includes(source)) {
        const next = previous.filter((item) => item !== source);
        return next.length > 0 ? next : ["memory"];
      }
      return [...previous, source];
    });
  }

  async function createResearchTask(payload: {
    topic: string;
    goal: string;
    category: string;
    sources: string[];
  }) {
    setResearchSubmitting(true);
    setResearchMessage("");
    try {
      const response = await fetch(`${API_BASE}/research/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: payload.topic,
          goal: payload.goal,
          category: payload.category,
          sources: payload.sources,
          run_now: true,
        }),
      });
      const data = await parseJsonSafe<ResearchTaskRecord>(response);
      if (!response.ok || !data?.research_id) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Research task creation failed.";
        throw new Error(errorMessage);
      }
      setSelectedResearchTask(data);
      setResearchMessage(
        "Research task saved. Web research is not connected yet. This research task is saved and can use memory/user notes only.",
      );
      await refreshSharedPanels();
    } catch (error) {
      setResearchMessage(error instanceof Error ? error.message : "Research task creation failed.");
    } finally {
      setResearchSubmitting(false);
    }
  }

  async function handleResearchTaskSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const topic = researchTopic.trim();
    const goal = researchGoal.trim();

    if (!topic || !goal) {
      setResearchMessage("Enter both a topic and a goal.");
      return;
    }

    await createResearchTask({
      topic,
      goal,
      category: researchCategory,
      sources: researchSources,
    });
  }

  async function handleQuickResearchFromAssistant() {
    const topic = assistantMessage.trim();
    if (!topic) {
      setAssistantMessageStatus("Enter or reuse an assistant message before creating a research task.");
      return;
    }

    const categoryMap: Record<string, string> = {
      general: "general",
      coding: "coding",
      research: "general",
      law: "law",
      market: "market",
      exam: "exam",
      project: "project",
      creative: "project",
    };

    setResearchTopic(topic);
    setResearchGoal(`Research this topic safely and summarize what Builder Core can save for later: ${topic}`);
    setResearchCategory(categoryMap[assistantMode] ?? "general");

    await createResearchTask({
      topic,
      goal: `Research this topic safely and summarize what Builder Core can save for later: ${topic}`,
      category: categoryMap[assistantMode] ?? "general",
      sources: ["memory", "user_notes"],
    });
  }

  async function handleGeneratePrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const command = commandInput.trim();
    if (!command) {
      setPromptMessage("Enter a command first.");
      return;
    }

    setPromptSubmitting(true);
    setPromptMessage("");
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
      setPromptMessage(
        "Codex prompt generated. Copy it into Codex, let Codex make the repo changes, then paste Codex's final summary back here.",
      );
      await refreshSharedPanels();
      await loadTask(data.task_id);
    } catch (error) {
      setPromptMessage(error instanceof Error ? error.message : "Prompt generation failed.");
    } finally {
      setPromptSubmitting(false);
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
      setPromptMessage("Generate a prompt first so Builder Core has a task ID.");
      return;
    }

    const codexSummary = codexSummaryInput.trim();
    if (!codexSummary) {
      setPromptMessage("Paste Codex's final summary before saving.");
      return;
    }

    setSavingSummary(true);
    setPromptMessage("");

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

      setPromptMessage("Codex summary saved. Builder Core updated project memory, latest summary, and lessons.");
      await refreshSharedPanels();
      await loadTask(currentTaskId);
    } catch (error) {
      setPromptMessage(error instanceof Error ? error.message : "Saving Codex summary failed.");
    } finally {
      setSavingSummary(false);
    }
  }

  async function handleSaveImprovementNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const note = manualImprovementNote.trim();
    if (!note) {
      setImprovementMessage("Enter a note first.");
      return;
    }

    setSavingImprovement(true);
    setImprovementMessage("");
    try {
      const response = await fetch(`${API_BASE}/self-improvement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          note,
          category: "preference",
        }),
      });
      const data = await parseJsonSafe<{ ok?: boolean }>(response);
      if (!response.ok || !data?.ok) {
        const errorMessage =
          typeof (data as Record<string, unknown> | null)?.["detail"] === "string"
            ? String((data as Record<string, unknown>)["detail"])
            : "Saving self-improvement note failed.";
        throw new Error(errorMessage);
      }
      setManualImprovementNote("");
      setImprovementMessage("Self-improvement note saved.");
      await refreshSharedPanels();
    } catch (error) {
      setImprovementMessage(error instanceof Error ? error.message : "Saving self-improvement note failed.");
    } finally {
      setSavingImprovement(false);
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
              Builder Core Assistant plus a safe manual Codex Prompt Command Center.
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
              Assistant: {systemStatus?.assistant_status?.mode ? titleCase(systemStatus.assistant_status.mode) : "Loading"}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Codex Flow: Manual
            </span>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(320px,1fr)] lg:px-8">
        <div className="space-y-6">
          <SectionCard
            eyebrow="Builder Core Assistant"
            title="Chat naturally with project-aware help"
            description="Builder Core can chat, plan, suggest ideas, create research tasks, save useful memory, and use lessons from previous work. It does not automatically know new internet information unless research is run."
          >
            <form className="space-y-4" onSubmit={handleAssistantSubmit}>
              <div className="grid gap-4 sm:grid-cols-[180px_minmax(0,1fr)]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="assistant-mode">
                    Mode
                  </label>
                  <select
                    id="assistant-mode"
                    value={assistantMode}
                    onChange={(event) => setAssistantMode(event.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  >
                    {ASSISTANT_MODES.map((mode) => (
                      <option key={mode.value} value={mode.value}>
                        {mode.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="assistant-message">
                    Message
                  </label>
                  <textarea
                    id="assistant-message"
                    value={assistantMessage}
                    onChange={(event) => setAssistantMessage(event.target.value)}
                    rows={5}
                    placeholder="Ask Builder Core for planning, coding ideas, research direction, market angles, legal-information structure, exam strategy, or creative ideas..."
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>
              </div>

              <label className="flex items-center gap-3 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={assistantSaveToMemory}
                  onChange={(event) => setAssistantSaveToMemory(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                />
                Save useful info to memory
              </label>

              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled={assistantSubmitting || backendStatus !== "online"}
                  className={
                    assistantSubmitting || backendStatus !== "online"
                      ? "rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                      : "rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                  }
                >
                  {assistantSubmitting ? "Sending..." : "Send to Assistant"}
                </button>

                <button
                  type="button"
                  onClick={handleIdeaGeneration}
                  disabled={ideaSubmitting || backendStatus !== "online"}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
                >
                  {ideaSubmitting ? "Generating ideas..." : "Generate Ideas"}
                </button>

                <button
                  type="button"
                  onClick={handleQuickResearchFromAssistant}
                  disabled={researchSubmitting || backendStatus !== "online"}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
                >
                  Create Research Task
                </button>
              </div>

              {assistantMessageStatus && (
                <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                  {assistantMessageStatus}
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Assistant reply</p>
                {assistantResponse ? (
                  <div className="mt-3 space-y-4">
                    <div className="whitespace-pre-wrap rounded-2xl bg-white px-4 py-4 text-sm leading-6 text-slate-800">
                      {assistantResponse.reply}
                    </div>
                    <div className="grid gap-4 lg:grid-cols-3">
                      <ListPanel title="Suggestions" items={assistantResponse.suggestions} />
                      <ListPanel title="Next actions" items={assistantResponse.next_actions} />
                      <ListPanel title="Memory used" items={assistantResponse.memory_used} />
                    </div>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">
                    Start a chat and Builder Core will answer here. It can research this when you ask, save this to memory, create a research task, use previous memory and lessons, and stay honest about missing internet information.
                  </p>
                )}
              </div>

              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.85fr)]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="idea-topic">
                    Idea topic
                  </label>
                  <input
                    id="idea-topic"
                    value={ideaTopic}
                    onChange={(event) => setIdeaTopic(event.target.value)}
                    placeholder="Builder Core assistant upgrades, business ideas, coding features..."
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="idea-goal">
                    Idea goal
                  </label>
                  <input
                    id="idea-goal"
                    value={ideaGoal}
                    onChange={(event) => setIdeaGoal(event.target.value)}
                    placeholder="Find the next safe and useful improvement"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>
              </div>

              {ideaMessage && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {ideaMessage}
                </div>
              )}

              {ideaResult && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">Idea generator</p>
                  <p className="mt-2 text-sm text-slate-700">
                    Best idea: <span className="font-medium">{ideaResult.best_idea}</span>
                  </p>
                  <p className="mt-1 text-sm text-slate-600">{ideaResult.why}</p>
                  <div className="mt-4 space-y-3">
                    {ideaResult.ideas.map((idea, index) => (
                      <div key={`${idea.idea_title}-${index}`} className="rounded-2xl bg-white px-4 py-4">
                        <p className="font-medium text-slate-900">{idea.idea_title}</p>
                        <p className="mt-1 text-sm text-slate-600">{idea.why_it_is_useful}</p>
                        <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Difficulty: {idea.difficulty}
                        </p>
                        <p className="mt-2 text-sm text-slate-700">Next step: {idea.possible_next_step}</p>
                        <p className="mt-1 text-sm text-amber-700">Risk / limitation: {idea.risk_or_limitation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recent assistant history</p>
                {assistantHistory.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {assistantHistory.slice(-8).map((item) => (
                      <div key={item.id} className="rounded-2xl bg-white px-4 py-4">
                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                          <span className="rounded-full border border-slate-200 px-2 py-1">
                            {titleCase(item.role)}
                          </span>
                          {item.mode && (
                            <span className="rounded-full border border-slate-200 px-2 py-1">
                              {titleCase(item.mode)}
                            </span>
                          )}
                          <span>{formatTimestamp(item.created_at)}</span>
                        </div>
                        <p className="mt-3 whitespace-pre-wrap text-sm text-slate-800">{item.message}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">No assistant chat history saved yet.</p>
                )}
              </div>
            </form>
          </SectionCard>

          <SectionCard
            eyebrow="Codex Prompt Command Center"
            title="Generate a strong prompt, then save Codex's result back"
            description="Builder Core does not automatically edit GitHub yet. Copy this prompt into Codex, let Codex make the changes, then paste Codex's final summary back here."
          >
            <form className="space-y-4" onSubmit={handleGeneratePrompt}>
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="command">
                    Command
                  </label>
                  <textarea
                    id="command"
                    value={commandInput}
                    onChange={(event) => setCommandInput(event.target.value)}
                    rows={6}
                    placeholder="Tell Builder Core what to build, fix, upgrade, research, or plan..."
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
                    disabled={promptSubmitting || backendStatus !== "online"}
                    className={
                      promptSubmitting || backendStatus !== "online"
                        ? "w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                        : "w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                    }
                  >
                    {promptSubmitting ? "Generating..." : "Generate Codex Prompt"}
                  </button>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                    <p className="font-semibold text-slate-900">Current task</p>
                    <p className="mt-2">Task ID: {currentTaskId || "Not generated yet"}</p>
                    <p className="mt-1">
                      Status: {currentTask?.status ? titleCase(currentTask.status) : "Waiting"}
                    </p>
                    <p className="mt-1">
                      Stage: {currentTask?.stage ? titleCase(currentTask.stage) : "Waiting"}
                    </p>
                    <p className="mt-1">Progress: {currentTask?.progress ?? 0}%</p>
                  </div>
                </div>
              </div>

              {promptMessage && (
                <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                  {promptMessage}
                </div>
              )}

              {latestIntelligenceBrief && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">
                    Intelligence mode: {latestIntelligenceBrief.title ?? titleCase(latestIntelligenceBrief.mode)}
                  </p>
                  <p className="mt-2 text-sm text-slate-700">
                    {latestIntelligenceBrief.status_message ?? latestIntelligenceBrief.overview}
                  </p>
                  <div className="mt-4 grid gap-4 lg:grid-cols-3">
                    <ListPanel title="Research steps" items={latestIntelligenceBrief.research_steps} />
                    <ListPanel title="Evidence checklist" items={latestIntelligenceBrief.evidence_checklist} />
                    <ListPanel title="Next questions" items={latestIntelligenceBrief.next_questions} />
                  </div>
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-900">Generated Codex prompt</p>
                    <p className="mt-1 text-sm text-slate-600">
                      Copy this prompt into Codex manually. Builder Core will save the result when you paste the final summary back.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleCopyPrompt}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-800"
                  >
                    Copy Prompt
                  </button>
                </div>
                {copyMessage && <p className="mt-3 text-sm text-slate-600">{copyMessage}</p>}
                <textarea
                  value={generatedPrompt}
                  readOnly
                  rows={18}
                  className="mt-4 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-mono text-xs leading-6 text-slate-800 outline-none"
                />
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Paste Codex final summary</p>
                <p className="mt-1 text-sm text-slate-600">
                  After Codex finishes, paste the summary here so Builder Core can save memory and create a lesson.
                </p>
                <textarea
                  value={codexSummaryInput}
                  onChange={(event) => setCodexSummaryInput(event.target.value)}
                  rows={8}
                  placeholder="Paste Codex's final summary here..."
                  className="mt-4 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <div className="mt-4 flex flex-wrap gap-3">
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
                </div>
              </div>

              {currentTask && (
                <div className="grid gap-4 lg:grid-cols-2">
                  <ListPanel title="Task logs" items={currentTask.logs} />
                  <ListPanel title="Task errors" items={currentTask.errors} />
                </div>
              )}
            </form>
          </SectionCard>

          <SectionCard
            eyebrow="Research Tasks"
            title="Create saved research work without faking web access"
            description="Research tasks are safe, manual, and scheduled-ready. They do not secretly run forever in the background. If web research is not connected, Builder Core will say so clearly."
          >
            <form className="space-y-4" onSubmit={handleResearchTaskSubmit}>
              <div className="grid gap-4 lg:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="research-topic">
                    Topic
                  </label>
                  <input
                    id="research-topic"
                    value={researchTopic}
                    onChange={(event) => setResearchTopic(event.target.value)}
                    placeholder="Example: compare safe market analysis prompts"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="research-goal">
                    Goal
                  </label>
                  <input
                    id="research-goal"
                    value={researchGoal}
                    onChange={(event) => setResearchGoal(event.target.value)}
                    placeholder="Example: save a safe research plan and limitations"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="research-category">
                    Category
                  </label>
                  <select
                    id="research-category"
                    value={researchCategory}
                    onChange={(event) => setResearchCategory(event.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
                  >
                    {RESEARCH_CATEGORIES.map((category) => (
                      <option key={category.value} value={category.value}>
                        {category.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium text-slate-700">Sources</p>
                  <div className="flex flex-wrap gap-3">
                    {["web", "user_notes", "memory"].map((source) => (
                      <label
                        key={source}
                        className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
                      >
                        <input
                          type="checkbox"
                          checked={researchSources.includes(source)}
                          onChange={() => toggleResearchSource(source)}
                          className="h-4 w-4 rounded border-slate-300 text-slate-900"
                        />
                        {titleCase(source)}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={researchSubmitting || backendStatus !== "online"}
                className={
                  researchSubmitting || backendStatus !== "online"
                    ? "rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                    : "rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
                }
              >
                {researchSubmitting ? "Creating task..." : "Create / Run Research Task"}
              </button>

              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                Web research is not connected yet. This research task is saved and can use memory/user notes only.
              </div>

              {researchMessage && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {researchMessage}
                </div>
              )}
            </form>

            <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.9fr)]">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Latest research result</p>
                {selectedResearchTask ? (
                  <div className="mt-3 space-y-4">
                    <div className="rounded-2xl bg-white px-4 py-4">
                      <p className="font-medium text-slate-900">{selectedResearchTask.topic}</p>
                      <p className="mt-1 text-sm text-slate-600">{selectedResearchTask.goal}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        {titleCase(selectedResearchTask.category)} · {titleCase(selectedResearchTask.status)} ·{" "}
                        {formatTimestamp(selectedResearchTask.updated_at)}
                      </p>
                      <p className="mt-3 text-sm text-slate-700">{selectedResearchTask.summary}</p>
                    </div>
                    <div className="grid gap-4 lg:grid-cols-3">
                      <ListPanel title="Findings" items={selectedResearchTask.findings} />
                      <ListPanel title="Limitations" items={selectedResearchTask.limitations} />
                      <ListPanel title="Next steps" items={selectedResearchTask.next_steps} />
                    </div>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">No research task selected yet.</p>
                )}
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recent research tasks</p>
                {researchTasks.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {researchTasks.map((task) => (
                      <button
                        key={task.research_id}
                        type="button"
                        onClick={() => setSelectedResearchTask(task)}
                        className="w-full rounded-2xl bg-white px-4 py-4 text-left"
                      >
                        <p className="font-medium text-slate-900">{task.topic}</p>
                        <p className="mt-1 text-sm text-slate-600">{task.summary}</p>
                        <p className="mt-2 text-xs text-slate-500">
                          {titleCase(task.category)} · {titleCase(task.status)} · {formatTimestamp(task.updated_at)}
                        </p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">No research tasks saved yet.</p>
                )}
              </div>
            </div>
          </SectionCard>
        </div>

        <aside className="space-y-6">
          <SectionCard
            eyebrow="Builder Memory"
            title="Saved context Builder Core can reuse"
            description="This is where saved memory, latest summaries, and storage notes stay visible so the assistant and prompt builder can improve over time."
          >
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">Storage status</p>
                <p className="mt-2">
                  {memoryData?.storage_message ?? systemStatus?.memory_storage_message ?? "Storage status unavailable."}
                </p>
              </div>

              <TaskSummaryPanel summary={memoryData?.latest_summary} />
              <MemoryList
                title="Project memory"
                items={memoryData?.project_memory}
                emptyText="No project memory entries were saved yet."
              />
              <MemoryList
                title="Assistant memory"
                items={memoryData?.assistant_memory}
                emptyText="No assistant memory was saved yet."
              />
              <ListPanel title="Cloud-ready notes" items={memoryData?.cloud_ready_notes ?? systemStatus?.cloud_ready_notes} />
              <ListPanel title="Known environment problems" items={memoryData?.known_environment_problems} />
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Project Learning"
            title="Lessons, issues, and structure summary"
            description="Builder Core learns from saved history and summaries. It does not train a real AI model."
          >
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Recent lessons</p>
                {learningData?.lessons && learningData.lessons.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {learningData.lessons.map((lesson) => (
                      <div key={lesson.id} className="rounded-2xl bg-white px-4 py-4">
                        <p className="font-medium text-slate-900">{lesson.command ?? "Saved lesson"}</p>
                        <p className="mt-1 text-sm text-slate-700">{lesson.lesson_learned}</p>
                        {lesson.next_recommendation && (
                          <p className="mt-2 text-sm text-emerald-700">Next: {lesson.next_recommendation}</p>
                        )}
                        <p className="mt-2 text-xs text-slate-500">{formatTimestamp(lesson.created_at)}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">No lessons saved yet.</p>
                )}
              </div>

              <ListPanel title="Known issues" items={learningData?.known_issues} />
              <ListPanel title="Recommended next steps" items={learningData?.recommended_next_steps} />
              <ListPanel
                title="Project structure sample"
                items={learningData?.project_structure_summary?.sample_tree}
              />
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Self-Improvement Notes"
            title="Memory-based improvement, not AI training"
            description="Builder Core can save what worked, what failed, repeated preferences, and better future instructions so the next reply or prompt can improve."
          >
            <form className="space-y-4" onSubmit={handleSaveImprovementNote}>
              <textarea
                value={manualImprovementNote}
                onChange={(event) => setManualImprovementNote(event.target.value)}
                rows={4}
                placeholder="Save a preference, a lesson, or a note about what should improve next..."
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
              />
              <button
                type="submit"
                disabled={savingImprovement || backendStatus !== "online"}
                className={
                  savingImprovement || backendStatus !== "online"
                    ? "rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-400"
                    : "rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
                }
              >
                {savingImprovement ? "Saving..." : "Save Improvement Note"}
              </button>
              {improvementMessage && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {improvementMessage}
                </div>
              )}
            </form>

            {selfImprovementData?.next_recommended_upgrade && (
              <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                Next recommended upgrade: {selfImprovementData.next_recommended_upgrade}
              </div>
            )}

            <div className="mt-4 space-y-3">
              {selfImprovementData?.items && selfImprovementData.items.length > 0 ? (
                selfImprovementData.items.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="font-medium text-slate-900">{item.user_message ?? "Saved improvement note"}</p>
                    <p className="mt-2 text-sm text-slate-700">{item.project_lesson ?? item.what_worked}</p>
                    {item.next_recommended_improvement && (
                      <p className="mt-2 text-sm text-emerald-700">
                        Next: {item.next_recommended_improvement}
                      </p>
                    )}
                    {item.repeated_user_preferences && item.repeated_user_preferences.length > 0 && (
                      <ListPanel title="Repeated preferences" items={item.repeated_user_preferences} />
                    )}
                    <p className="mt-2 text-xs text-slate-500">{formatTimestamp(item.created_at)}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No self-improvement notes saved yet.</p>
              )}
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Install"
            title="Open Builder Core on phone"
            description="No App Store needed. Use the browser install flow and keep this link handy."
          >
            <div className="space-y-4 text-sm text-slate-700">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">iPhone</p>
                <p className="mt-2">Open in Safari, tap Share, then Add to Home Screen.</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">Android</p>
                <p className="mt-2">Open in Chrome, tap the menu, then Install app or Add to Home screen.</p>
              </div>
              <div className="flex flex-wrap gap-3">
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
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800"
                >
                  Copy App Link
                </button>
              </div>
              {installMessage && <p className="text-sm text-slate-600">{installMessage}</p>}
              {activeBridgeStatus && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="font-semibold text-slate-900">Bridge status</p>
                  <p className="mt-2 text-sm text-slate-700">
                    {activeBridgeStatus.message ?? "Bridge status not available."}
                  </p>
                  <ListPanel title="Missing bridge configuration" items={activeBridgeStatus.missing} />
                </div>
              )}
            </div>
          </SectionCard>
        </aside>
      </div>
    </main>
  );
}
