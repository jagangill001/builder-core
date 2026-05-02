"use client";

import { type FormEvent, type ReactNode, useEffect, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const LIVE_FRONTEND_URL = "https://builder-core-frontend-599596796788.us-central1.run.app";

const MODE_OPTIONS = [
  { value: "auto", label: "Auto" },
  { value: "coding", label: "Coding" },
  { value: "research", label: "Research" },
  { value: "market", label: "Market" },
  { value: "law", label: "Law" },
  { value: "exam", label: "Exam" },
  { value: "project", label: "Project" },
  { value: "creative", label: "Creative" },
];

const SOURCE_OPTIONS = ["web", "user_notes", "memory"];

type StatusTone = "slate" | "green" | "amber" | "red" | "blue";

type SystemStatus = {
  status?: string;
  service?: string;
  assistant_mode?: string;
  active_brain?: string;
  local_model_provider?: string;
  storage_mode?: string;
  firestore_enabled?: boolean;
  using_firestore?: boolean;
  using_fallback?: boolean;
  firestore_warnings?: string[];
  gcp_project_id?: string;
  memory_count?: number;
  research_task_count?: number;
  private_search_document_count?: number;
  private_search_chunk_count?: number;
  command_router_status?: {
    mode?: string;
    supported_workflows?: string[];
  };
  orchestrator_status?: {
    enabled?: boolean;
    engine?: string;
    uses_private_search?: boolean;
    uses_market_analyzer?: boolean;
    uses_app_planner?: boolean;
  };
  internal_tool_registry_status?: {
    total_tools?: number;
    enabled_tools?: number;
    disabled_tools?: number;
  };
  frontend_url?: string;
  backend_url?: string;
  bridge_status?: {
    ready_for_repo_work?: boolean;
    missing?: string[];
    message?: string;
    repo?: string;
    branch?: string;
  };
  cloud_ready_notes?: string[];
};

type SearchResult = {
  id?: string;
  document_id?: string;
  title?: string;
  preview?: string;
  source_type?: string;
  url?: string | null;
  score?: number;
};

type ResearchResult = {
  summary?: string;
  findings?: string[];
  sources?: Array<{ title?: string; source_type?: string; url?: string | null; score?: number }>;
  limitations?: string[];
  unknowns?: string[];
  confidence?: string;
  next_steps?: string[];
  results_count?: number;
};

type MarketAnalysis = {
  topic?: string;
  market_summary?: string;
  target_users?: string[];
  competitors_to_research?: string[];
  risks?: string[];
  opportunities?: string[];
  missing_data?: string[];
  confidence?: string;
  app_ideas?: string[];
};

type AppPlan = {
  app_name?: string;
  app_concept?: string;
  mvp_features?: string[];
  backend_routes?: string[];
  frontend_screens?: string[];
  storage_collections?: string[];
  storage_plan?: string[];
  next_steps?: string[];
  codex_prompt?: string;
};

type CommandResponse = {
  command_id: string;
  reply: string;
  detected_intents?: string[];
  workflow?: string;
  internal_tools_used?: string[];
  progress?: {
    status?: string;
    steps?: string[];
  };
  private_search?: {
    used?: boolean;
    results_count?: number;
    top_sources?: string[];
    results?: SearchResult[];
  };
  research?: ResearchResult;
  market_analysis?: MarketAnalysis;
  app_plan?: AppPlan;
  codex_prompt?: string;
  summary?: {
    message?: string;
    manual_setup?: string[];
    [key: string]: unknown;
  };
  storage_used?: string;
  memory_saved?: boolean;
  next_actions?: string[];
  limitations?: string[];
  created_at?: string;
};

type ThreadItem = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  result?: CommandResponse;
  error?: string;
};

type ToolItem = {
  tool_id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  input_schema?: string;
  output_schema?: string;
  limitations?: string[];
  safety_notes?: string[];
};

type ToolsResponse = {
  ok?: boolean;
  items?: ToolItem[];
  status?: {
    total_tools?: number;
    enabled_tools?: number;
    disabled_tools?: number;
  };
};

type StorageStatus = {
  storage_mode?: string;
  storage_backend?: string;
  storage_message?: string;
  firestore_enabled?: boolean;
  gcp_project_id?: string;
  gcs_bucket_name?: string;
  using_firestore?: boolean;
  using_fallback?: boolean;
  warnings?: string[];
  collections?: string[];
  project_memory_count?: number;
  assistant_memory_count?: number;
  chat_history_count?: number;
  research_task_count?: number;
  lesson_count?: number;
  self_improvement_count?: number;
  search_document_count?: number;
  search_chunk_count?: number;
  checked_at?: string;
};

type StorageTestResult = {
  ok?: boolean;
  storage_used?: string;
  record_id?: string;
  saved?: boolean;
  read_back?: boolean;
  warnings?: string[];
};

type ModelStatus = {
  assistant_mode?: string;
  active_brain?: string;
  local_model_provider?: string;
  local_model_connected?: boolean;
  openai_configured?: boolean;
  warnings?: string[];
};

type SearchStatus = {
  ok?: boolean;
  document_count?: number;
  chunk_count?: number;
  query_count?: number;
  knowledge_entries?: number;
  status_message?: string;
  checked_at?: string;
};

type SearchQueryResponse = {
  query?: string;
  results_count?: number;
  top_sources?: string[];
  results?: SearchResult[];
};

type MemoryEntry = {
  id?: string;
  type?: string;
  note?: string;
  command?: string;
  project_name?: string;
  created_at?: string;
};

type TaskSummary = {
  task_id?: string;
  message?: string;
  next_recommended_step?: string;
  what_completed?: string[];
  what_still_needs_manual_setup?: string[];
  files_changed?: string[];
  codex_summary?: string;
};

type LatestPrompt = {
  task_id?: string;
  command?: string;
  prompt?: string;
  status?: string;
  workflow?: string;
  created_at?: string;
};

type MemoryResponse = {
  ok?: boolean;
  storage_backend?: string;
  storage_message?: string;
  project_memory?: MemoryEntry[];
  assistant_memory?: MemoryEntry[];
  chat_history?: Array<{
    id?: string;
    role?: string;
    mode?: string;
    message?: string;
    created_at?: string;
  }>;
  research_tasks?: ResearchTask[];
  research_results?: ResearchTask[];
  self_improvement?: SelfImprovementItem[];
  app_plans?: AppPlan[];
  market_analysis?: MarketAnalysis[];
  command_history?: Array<{ command_id?: string; message?: string; workflow?: string; created_at?: string }>;
  latest_summary?: TaskSummary | null;
  latest_prompt?: LatestPrompt | null;
  prompt_history?: LatestPrompt[];
  latest_intelligence_brief?: { title?: string; overview?: string; mode?: string } | null;
  intelligence_history?: Array<{ id?: string; title?: string; mode?: string; created_at?: string }>;
  known_environment_problems?: string[];
  cloud_ready_notes?: string[];
};

type LearningLesson = {
  id?: string;
  command?: string;
  lesson_learned?: string;
  next_recommendation?: string;
  files_changed?: string[];
  error?: string | null;
  created_at?: string;
};

type LearningResponse = {
  ok?: boolean;
  lessons?: LearningLesson[];
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

type SelfImprovementItem = {
  id?: string;
  category?: string;
  user_message?: string;
  assistant_reply?: string;
  what_worked?: string;
  what_failed?: string;
  better_future_instruction?: string;
  repeated_user_preferences?: string[];
  project_lesson?: string;
  next_recommended_improvement?: string;
  created_at?: string;
};

type SelfImprovementResponse = {
  ok?: boolean;
  items?: SelfImprovementItem[];
  next_recommended_upgrade?: string;
  notes?: string[];
};

type ResearchTask = {
  research_id?: string;
  topic?: string;
  goal?: string;
  category?: string;
  sources?: string[];
  status?: string;
  summary?: string;
  findings?: string[];
  limitations?: string[];
  next_steps?: string[];
  created_at?: string;
  updated_at?: string;
};

type ResearchCreateResponse = ResearchTask & {
  research_id: string;
};

type UrlIngestResponse = {
  ok?: boolean;
  document_id?: string | null;
  title?: string;
  text_chars?: number;
  chunks_created?: number;
  warnings?: string[];
};

type CrawlPlanResponse = {
  ok?: boolean;
  plan_id?: string;
  seed_urls?: string[];
  max_pages?: number;
  warnings?: string[];
  limits?: string[];
  plan_steps?: string[];
};

function createId(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function titleCase(value?: string | null) {
  if (!value) {
    return "Unknown";
  }
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatTime(value?: string | null) {
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

async function parseResponse<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const data = await parseResponse<T & { detail?: string; message?: string }>(response);

  if (!response.ok) {
    const detail =
      (data && typeof data === "object" && "detail" in data && typeof data.detail === "string" && data.detail) ||
      (data && typeof data === "object" && "message" in data && typeof data.message === "string" && data.message) ||
      `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return (data ?? ({} as T)) as T;
}

function StatusPill({ tone, children }: { tone: StatusTone; children: ReactNode }) {
  const tones: Record<StatusTone, string> = {
    slate: "border-slate-200 bg-slate-100 text-slate-700",
    green: "border-green-200 bg-green-50 text-green-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
  };

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <details className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <summary className="cursor-pointer list-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-base font-semibold text-slate-900">{title}</p>
            {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
          </div>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-500">
            Expand
          </span>
        </div>
      </summary>
      <div className="mt-5 space-y-4">{children}</div>
    </details>
  );
}

function ListBlock({
  title,
  items,
  emptyText,
}: {
  title: string;
  items?: Array<string | undefined | null>;
  emptyText: string;
}) {
  const filtered = (items ?? []).filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      {filtered.length > 0 ? (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {filtered.map((item, index) => (
            <li key={`${title}_${index}`}>• {item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}

function KeyValue({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <div className="mt-1 text-sm text-slate-800">{value}</div>
    </div>
  );
}

function CodePromptBox({
  prompt,
  onCopy,
  copyLabel,
}: {
  prompt?: string;
  onCopy: () => void;
  copyLabel: string;
}) {
  if (!prompt) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-950 p-4 text-slate-100">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold">Codex Prompt</p>
        <button
          type="button"
          onClick={onCopy}
          className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-100"
        >
          {copyLabel}
        </button>
      </div>
      <textarea
        readOnly
        value={prompt}
        className="mt-3 h-56 w-full resize-y rounded-2xl border border-slate-800 bg-slate-900 p-3 font-mono text-xs text-slate-100 outline-none"
      />
    </div>
  );
}

function ConversationCard({
  item,
  onCopyPrompt,
}: {
  item: ThreadItem;
  onCopyPrompt: (prompt: string) => void;
}) {
  const result = item.result;

  if (item.role === "user") {
    return (
      <div className="ml-auto max-w-3xl rounded-[28px] rounded-br-md bg-slate-950 px-5 py-4 text-white shadow-lg">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-300">You</p>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-7">{item.content}</p>
        <p className="mt-3 text-xs text-slate-300">{formatTime(item.createdAt)}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl rounded-[28px] rounded-bl-md border border-slate-200 bg-white px-5 py-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Builder Core</p>
        {result?.workflow ? <StatusPill tone="blue">{titleCase(result.workflow)}</StatusPill> : null}
        {result?.storage_used ? <StatusPill tone="slate">Storage: {titleCase(result.storage_used)}</StatusPill> : null}
      </div>

      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-800">{item.content}</p>

      {item.error ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {item.error}
        </div>
      ) : null}

      {result ? (
        <div className="mt-5 space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <KeyValue label="Detected Workflow" value={titleCase(result.workflow)} />
            <KeyValue
              label="Private Search"
              value={
                result.private_search?.used
                  ? `${result.private_search.results_count ?? 0} results`
                  : "Not used"
              }
            />
            <KeyValue label="Memory Saved" value={result.memory_saved ? "Yes" : "No"} />
            <KeyValue label="Created" value={formatTime(result.created_at)} />
          </div>

          <ListBlock
            title="Progress Steps"
            items={result.progress?.steps}
            emptyText="No progress steps were returned for this message."
          />

          <ListBlock
            title="Internal Tools Used"
            items={result.internal_tools_used}
            emptyText="No internal tools were listed for this message."
          />

          <ListBlock
            title="Top Private Search Sources"
            items={result.private_search?.top_sources}
            emptyText="No private-search sources were surfaced yet."
          />

          {result.research && Object.keys(result.research).length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Research Result</p>
                <p className="mt-3 text-sm text-slate-700">
                  {result.research.summary || "No research summary returned."}
                </p>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <ListBlock
                    title="Findings"
                    items={result.research.findings}
                    emptyText="No findings returned."
                  />
                  <ListBlock
                    title="Unknowns"
                    items={result.research.unknowns}
                    emptyText="No unknowns were listed."
                  />
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Research Limits</p>
                <ListBlock
                  title="Limitations"
                  items={result.research.limitations}
                  emptyText="No research limitations were returned."
                />
                <ListBlock
                  title="Next Research Steps"
                  items={result.research.next_steps}
                  emptyText="No research next steps were returned."
                />
              </div>
            </div>
          ) : null}

          {result.market_analysis && Object.keys(result.market_analysis).length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">Market Analysis</p>
              <p className="mt-3 text-sm text-slate-700">
                {result.market_analysis.market_summary || "No market summary returned."}
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <ListBlock
                  title="Target Users"
                  items={result.market_analysis.target_users}
                  emptyText="No target users were returned."
                />
                <ListBlock
                  title="Competitors To Research"
                  items={result.market_analysis.competitors_to_research}
                  emptyText="No competitor questions were returned."
                />
                <ListBlock
                  title="Opportunities"
                  items={result.market_analysis.opportunities}
                  emptyText="No opportunities were returned."
                />
                <ListBlock
                  title="Risks"
                  items={result.market_analysis.risks}
                  emptyText="No risks were returned."
                />
              </div>
            </div>
          ) : null}

          {result.app_plan && Object.keys(result.app_plan).length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">App Plan</p>
              <p className="mt-3 text-sm text-slate-700">
                {result.app_plan.app_concept || "No app concept returned."}
              </p>
              <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
                <ListBlock
                  title="MVP Features"
                  items={result.app_plan.mvp_features}
                  emptyText="No MVP features were returned."
                />
                <ListBlock
                  title="Backend Routes"
                  items={result.app_plan.backend_routes}
                  emptyText="No backend routes were returned."
                />
                <ListBlock
                  title="Frontend Screens"
                  items={result.app_plan.frontend_screens}
                  emptyText="No frontend screens were returned."
                />
                <ListBlock
                  title="Storage Collections"
                  items={result.app_plan.storage_collections}
                  emptyText="No storage collections were returned."
                />
              </div>
              <div className="mt-3">
                <ListBlock
                  title="Storage Plan"
                  items={result.app_plan.storage_plan}
                  emptyText="No storage plan was returned."
                />
              </div>
            </div>
          ) : null}

          <CodePromptBox
            prompt={result.codex_prompt}
            onCopy={() => {
              if (result.codex_prompt) {
                onCopyPrompt(result.codex_prompt);
              }
            }}
            copyLabel="Copy Codex Prompt"
          />

          {result.summary && Object.keys(result.summary).length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">Summary</p>
              {typeof result.summary.message === "string" ? (
                <p className="mt-3 text-sm text-slate-700">{result.summary.message}</p>
              ) : null}
              <ListBlock
                title="Manual Setup Still Needed"
                items={Array.isArray(result.summary.manual_setup) ? result.summary.manual_setup : []}
                emptyText="No manual setup items were returned."
              />
            </div>
          ) : null}

          <ListBlock
            title="Limitations"
            items={result.limitations}
            emptyText="No limitations were returned."
          />

          <ListBlock
            title="Next Actions"
            items={result.next_actions}
            emptyText="No next actions were returned."
          />
        </div>
      ) : null}
    </div>
  );
}

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemMessage, setSystemMessage] = useState("");

  const [thread, setThread] = useState<ThreadItem[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Builder Core Command Chat is ready. Send one message and Builder Core will route it through its own internal tools, private search, memory, research engine, market analyzer, app planner, and manual Codex prompt builder when needed.",
      createdAt: new Date().toISOString(),
    },
  ]);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("auto");
  const [saveToMemory, setSaveToMemory] = useState(true);
  const [sending, setSending] = useState(false);
  const [composerMessage, setComposerMessage] = useState("");

  const [memoryData, setMemoryData] = useState<MemoryResponse | null>(null);
  const [learningData, setLearningData] = useState<LearningResponse | null>(null);
  const [selfImprovementData, setSelfImprovementData] = useState<SelfImprovementResponse | null>(null);
  const [toolsData, setToolsData] = useState<ToolsResponse | null>(null);
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  const [storageTestResult, setStorageTestResult] = useState<StorageTestResult | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [searchStatus, setSearchStatus] = useState<SearchStatus | null>(null);
  const [searchResults, setSearchResults] = useState<SearchQueryResponse | null>(null);
  const [latestPrompt, setLatestPrompt] = useState<LatestPrompt | null>(null);
  const [researchTasks, setResearchTasks] = useState<ResearchTask[]>([]);
  const [selectedResearchTask, setSelectedResearchTask] = useState<ResearchTask | null>(null);
  const [memoryError, setMemoryError] = useState("");
  const [learningError, setLearningError] = useState("");
  const [searchMessage, setSearchMessage] = useState("");
  const [storageMessage, setStorageMessage] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [quickDocTitle, setQuickDocTitle] = useState("");
  const [quickDocText, setQuickDocText] = useState("");
  const [quickDocSourceType, setQuickDocSourceType] = useState("manual");

  const [ingestTitle, setIngestTitle] = useState("");
  const [ingestText, setIngestText] = useState("");
  const [ingestSourceType, setIngestSourceType] = useState("project");
  const [ingestTags, setIngestTags] = useState("");
  const [ingestMessage, setIngestMessage] = useState("");

  const [urlInput, setUrlInput] = useState("");
  const [urlNote, setUrlNote] = useState("");
  const [urlMessage, setUrlMessage] = useState("");
  const [urlResult, setUrlResult] = useState<UrlIngestResponse | null>(null);

  const [crawlSeeds, setCrawlSeeds] = useState("");
  const [crawlMaxPages, setCrawlMaxPages] = useState(5);
  const [crawlResult, setCrawlResult] = useState<CrawlPlanResponse | null>(null);
  const [crawlMessage, setCrawlMessage] = useState("");

  const [researchTopic, setResearchTopic] = useState("");
  const [researchGoal, setResearchGoal] = useState("");
  const [researchCategory, setResearchCategory] = useState("market");
  const [researchSources, setResearchSources] = useState<string[]>(["memory"]);
  const [researchMessage, setResearchMessage] = useState("");

  async function copyText(value: string, successLabel: string) {
    try {
      await navigator.clipboard.writeText(value);
      setComposerMessage(successLabel);
    } catch {
      setComposerMessage("Clipboard access failed. Copy the text manually.");
    }
  }

  async function loadSystemStatus() {
    try {
      const data = await requestJson<SystemStatus>("/system/status");
      setSystemStatus(data);
      setBackendStatus(data.status === "ok" ? "online" : "offline");
      setSystemMessage("");
    } catch (error) {
      setBackendStatus("offline");
      setSystemMessage(error instanceof Error ? error.message : "Backend status check failed.");
    }
  }

  async function loadMemory() {
    try {
      const data = await requestJson<MemoryResponse>("/memory");
      setMemoryData(data);
      setMemoryError("");
    } catch (error) {
      setMemoryError(error instanceof Error ? error.message : "Memory endpoint is unavailable.");
      setMemoryData(null);
    }
  }

  async function loadLearning() {
    try {
      const data = await requestJson<LearningResponse>("/learning");
      setLearningData(data);
      setLearningError("");
    } catch (error) {
      setLearningError(error instanceof Error ? error.message : "Learning endpoint is unavailable.");
      setLearningData(null);
    }
  }

  async function loadSelfImprovement() {
    try {
      const data = await requestJson<SelfImprovementResponse>("/self-improvement");
      setSelfImprovementData(data);
    } catch {
      setSelfImprovementData(null);
    }
  }

  async function loadTools() {
    try {
      const data = await requestJson<ToolsResponse>("/tools");
      setToolsData(data);
    } catch {
      setToolsData(null);
    }
  }

  async function loadStorageStatus() {
    try {
      const data = await requestJson<StorageStatus>("/storage/status");
      setStorageStatus(data);
      setStorageMessage("");
    } catch (error) {
      setStorageStatus(null);
      setStorageMessage(error instanceof Error ? error.message : "Storage status endpoint failed.");
    }
  }

  async function loadModelStatus() {
    try {
      const data = await requestJson<ModelStatus>("/assistant/model-status");
      setModelStatus(data);
    } catch {
      setModelStatus(null);
    }
  }

  async function loadSearchStatus() {
    try {
      const data = await requestJson<SearchStatus>("/search/status");
      setSearchStatus(data);
    } catch {
      setSearchStatus(null);
    }
  }

  async function loadLatestPrompt() {
    try {
      const data = await requestJson<{ ok?: boolean; item?: LatestPrompt | null }>("/prompts/latest");
      setLatestPrompt(data.item ?? null);
    } catch {
      setLatestPrompt(null);
    }
  }

  async function loadResearchTasks() {
    try {
      const data = await requestJson<{ items?: ResearchTask[] }>("/research/tasks");
      const items = Array.isArray(data.items) ? data.items : [];
      setResearchTasks(items);
      setSelectedResearchTask((current) => current ?? items[0] ?? null);
    } catch {
      setResearchTasks([]);
      setSelectedResearchTask(null);
    }
  }

  async function refreshSupportData() {
    await Promise.allSettled([
      loadSystemStatus(),
      loadMemory(),
      loadLearning(),
      loadSelfImprovement(),
      loadTools(),
      loadStorageStatus(),
      loadModelStatus(),
      loadSearchStatus(),
      loadLatestPrompt(),
      loadResearchTasks(),
    ]);
  }

  useEffect(() => {
    void refreshSupportData();
  }, []);

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      setComposerMessage("Type a command before sending.");
      return;
    }

    const timestamp = new Date().toISOString();
    setThread((current) => [
      ...current,
      {
        id: createId("user"),
        role: "user",
        content: trimmed,
        createdAt: timestamp,
      },
    ]);
    setMessage("");
    setComposerMessage("");
    setSending(true);

    try {
      const data = await requestJson<CommandResponse>("/command", {
        method: "POST",
        body: JSON.stringify({
          message: trimmed,
          mode,
          save_to_memory: saveToMemory,
        }),
      });

      setThread((current) => [
        ...current,
        {
          id: createId("assistant"),
          role: "assistant",
          content: data.reply,
          createdAt: data.created_at ?? new Date().toISOString(),
          result: data,
        },
      ]);

      if (data.codex_prompt) {
        setLatestPrompt({
          task_id: data.command_id,
          command: trimmed,
          prompt: data.codex_prompt,
          status: "prompt_ready",
          workflow: data.workflow,
          created_at: data.created_at,
        });
      }

      setComposerMessage("Builder Core finished the workflow and refreshed saved context.");
      await refreshSupportData();
    } catch (error) {
      const messageText =
        error instanceof Error ? error.message : "Builder Core could not complete this command right now.";
      setThread((current) => [
        ...current,
        {
          id: createId("assistant"),
          role: "assistant",
          content: "Builder Core hit a problem while handling that message.",
          createdAt: new Date().toISOString(),
          error: messageText,
        },
      ]);
      setComposerMessage(messageText);
    } finally {
      setSending(false);
    }
  }

  async function handleStorageTest() {
    try {
      const data = await requestJson<StorageTestResult>("/storage/test", { method: "POST" });
      setStorageTestResult(data);
      setStorageMessage(data.ok ? `Storage test used ${data.storage_used}.` : "Storage test failed.");
      await loadStorageStatus();
    } catch (error) {
      setStorageMessage(error instanceof Error ? error.message : "Storage test failed.");
      setStorageTestResult(null);
    }
  }

  async function handlePrivateSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query) {
      setSearchMessage("Enter a search query first.");
      return;
    }

    try {
      const data = await requestJson<SearchQueryResponse>("/search/query", {
        method: "POST",
        body: JSON.stringify({ query, limit: 10 }),
      });
      setSearchResults(data);
      setSearchMessage(`Private search returned ${data.results_count ?? 0} results.`);
      await loadSearchStatus();
    } catch (error) {
      setSearchMessage(error instanceof Error ? error.message : "Private search failed.");
      setSearchResults(null);
    }
  }

  async function handleQuickAddDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = quickDocTitle.trim();
    const text = quickDocText.trim();
    if (!title || !text) {
      setSearchMessage("Add both a title and text before saving to the private index.");
      return;
    }

    try {
      await requestJson("/search/add", {
        method: "POST",
        body: JSON.stringify({
          title,
          text,
          source_type: quickDocSourceType,
          metadata: { added_from: "frontend_private_search_panel" },
        }),
      });
      setQuickDocTitle("");
      setQuickDocText("");
      setSearchMessage("Saved directly to the private search index.");
      await Promise.allSettled([loadSearchStatus(), loadMemory()]);
    } catch (error) {
      setSearchMessage(error instanceof Error ? error.message : "Saving to private search failed.");
    }
  }

  async function handleRebuildIndex() {
    try {
      const data = await requestJson<{ documents_added?: number }>("/search/rebuild", { method: "POST" });
      setSearchMessage(`Private search rebuild finished. Documents added: ${data.documents_added ?? 0}.`);
      await loadSearchStatus();
    } catch (error) {
      setSearchMessage(error instanceof Error ? error.message : "Search rebuild failed.");
    }
  }

  async function handleDocumentIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = ingestTitle.trim();
    const text = ingestText.trim();
    if (!title || !text) {
      setIngestMessage("Add both a document title and text before ingesting.");
      return;
    }

    try {
      const data = await requestJson<{ document_id?: string; chunks_created?: number; warnings?: string[] }>(
        "/documents/ingest-text",
        {
          method: "POST",
          body: JSON.stringify({
            title,
            text,
            source_type: ingestSourceType,
            tags: ingestTags
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),
          }),
        },
      );
      setIngestMessage(
        `Document saved with id ${data.document_id ?? "unknown"} and ${data.chunks_created ?? 0} chunks.`,
      );
      setIngestTitle("");
      setIngestText("");
      setIngestTags("");
      await Promise.allSettled([loadSearchStatus(), loadMemory(), loadLearning()]);
    } catch (error) {
      setIngestMessage(error instanceof Error ? error.message : "Document ingest failed.");
    }
  }

  async function handleUrlIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const url = urlInput.trim();
    if (!url) {
      setUrlMessage("Paste a public http or https URL first.");
      return;
    }

    try {
      const data = await requestJson<UrlIngestResponse>("/search/ingest-url", {
        method: "POST",
        body: JSON.stringify({
          url,
          source_note: urlNote.trim() || undefined,
        }),
      });
      setUrlResult(data);
      setUrlMessage(data.ok ? "URL ingest finished safely." : "URL ingest returned a warning.");
      if (data.ok) {
        setUrlInput("");
        setUrlNote("");
      }
      await Promise.allSettled([loadSearchStatus(), loadMemory()]);
    } catch (error) {
      setUrlMessage(error instanceof Error ? error.message : "URL ingest failed.");
      setUrlResult(null);
    }
  }

  async function handleCrawlerPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const seedUrls = crawlSeeds
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

    if (seedUrls.length === 0) {
      setCrawlMessage("Add at least one public seed URL.");
      return;
    }

    try {
      const data = await requestJson<CrawlPlanResponse>("/crawler/plan", {
        method: "POST",
        body: JSON.stringify({
          seed_urls: seedUrls,
          max_pages: Math.max(1, Math.min(crawlMaxPages, 25)),
        }),
      });
      setCrawlResult(data);
      setCrawlMessage("Crawler plan created. It does not start a live crawl.");
      await loadMemory();
    } catch (error) {
      setCrawlMessage(error instanceof Error ? error.message : "Crawler plan failed.");
      setCrawlResult(null);
    }
  }

  async function handleCreateResearchTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const topic = researchTopic.trim();
    const goal = researchGoal.trim();

    if (!topic || !goal) {
      setResearchMessage("Add both a research topic and goal first.");
      return;
    }

    try {
      const data = await requestJson<ResearchCreateResponse>("/research/tasks", {
        method: "POST",
        body: JSON.stringify({
          topic,
          goal,
          category: researchCategory,
          sources: researchSources,
          run_now: true,
        }),
      });
      setResearchMessage(`Research task ${data.research_id} saved with status ${data.status}.`);
      setResearchTopic("");
      setResearchGoal("");
      await Promise.allSettled([loadResearchTasks(), loadMemory(), loadLearning()]);
    } catch (error) {
      setResearchMessage(error instanceof Error ? error.message : "Research task creation failed.");
    }
  }

  function toggleResearchSource(source: string) {
    setResearchSources((current) =>
      current.includes(source) ? current.filter((item) => item !== source) : [...current, source],
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(226,232,240,0.9),_rgba(248,250,252,1)_55%)] text-slate-900">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 md:px-6 lg:px-8">
        <header className="rounded-[32px] border border-slate-200 bg-white/95 p-5 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Builder Core</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
                Builder Core Command Chat
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                One message can route through Builder Core&rsquo;s own internal tools: safety firewall, command router,
                private search, internal research engine, market analyzer, app planner, Codex prompt builder, memory,
                learning, and Firestore-ready storage.
              </p>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[420px]">
              <StatusPill tone={backendStatus === "online" ? "green" : backendStatus === "offline" ? "red" : "amber"}>
                Backend: {backendStatus === "checking" ? "Checking..." : backendStatus === "online" ? "Online" : "Offline"}
              </StatusPill>
              <StatusPill tone={systemStatus?.using_firestore ? "green" : "amber"}>
                Storage: {systemStatus?.using_firestore ? "Firestore" : systemStatus?.storage_mode ?? "Local"}
              </StatusPill>
              <StatusPill tone="blue">
                Brain: {titleCase(systemStatus?.active_brain ?? systemStatus?.assistant_mode ?? "local_rule_based")}
              </StatusPill>
              <StatusPill tone={systemStatus?.bridge_status?.ready_for_repo_work ? "green" : "amber"}>
                Codex Bridge: {systemStatus?.bridge_status?.ready_for_repo_work ? "Configured" : "Manual Prompt Mode"}
              </StatusPill>
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <KeyValue label="GCP Project" value={systemStatus?.gcp_project_id ?? "missing"} />
            <KeyValue label="Memory Count" value={systemStatus?.memory_count ?? 0} />
            <KeyValue label="Research Tasks" value={systemStatus?.research_task_count ?? 0} />
            <KeyValue label="Private Search Docs" value={systemStatus?.private_search_document_count ?? 0} />
          </div>

          <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-600">
            <a href={LIVE_FRONTEND_URL} target="_blank" rel="noreferrer" className="font-medium text-slate-900 underline">
              Open live frontend
            </a>
            <button
              type="button"
              onClick={() => void copyText(LIVE_FRONTEND_URL, "Live frontend link copied.")}
              className="font-medium text-slate-900 underline"
            >
              Copy app link
            </button>
            <span>OpenAI is optional only. Builder Core works in local rule-based mode by default.</span>
          </div>

          {systemMessage ? (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {systemMessage}
            </div>
          ) : null}
        </header>

        <section className="rounded-[32px] border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">Unified command input</p>
              <p className="mt-1 text-sm text-slate-500">
                Builder Core does not automatically edit GitHub yet. It can research from its own saved knowledge,
                build an app plan, and produce a manual Codex prompt inside the same reply.
              </p>
            </div>
            <div className="text-sm text-slate-500">
              Paste a Codex final summary here too. Builder Core can save it to memory and learning when the router detects
              a summary workflow.
            </div>
          </div>

          <form className="mt-4 space-y-4" onSubmit={handleSend}>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Example: Research trucking dispatch market and create an app to analyze it"
              className="h-36 w-full resize-y rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
            />

            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <select
                  value={mode}
                  onChange={(event) => setMode(event.target.value)}
                  className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 outline-none"
                >
                  {MODE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>

                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={saveToMemory}
                    onChange={(event) => setSaveToMemory(event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  Save useful info to memory
                </label>
              </div>

              <button
                type="submit"
                disabled={sending || backendStatus !== "online"}
                className={
                  sending || backendStatus !== "online"
                    ? "rounded-full border border-slate-200 bg-slate-100 px-5 py-3 text-sm font-semibold text-slate-400"
                    : "rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
                }
              >
                {sending ? "Working..." : "Send"}
              </button>
            </div>
          </form>

          {composerMessage ? (
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {composerMessage}
            </div>
          ) : null}
        </section>

        <section className="space-y-4">
          {thread.map((item) => (
            <ConversationCard
              key={item.id}
              item={item}
              onCopyPrompt={(prompt) => {
                void copyText(prompt, "Codex prompt copied.");
              }}
            />
          ))}
        </section>

        <section className="space-y-4">
          <Panel
            title="Internal Tools"
            subtitle="See the built-in modules that power Builder Core without requiring outside AI or search APIs."
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {(toolsData?.items ?? []).map((tool) => (
                <div key={tool.tool_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-slate-900">{tool.name}</p>
                    <StatusPill tone={tool.enabled ? "green" : "amber"}>{tool.enabled ? "Enabled" : "Disabled"}</StatusPill>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{tool.description}</p>
                  <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">{titleCase(tool.category)}</p>
                  <ListBlock
                    title="Limitations"
                    items={tool.limitations}
                    emptyText="No limitations listed."
                  />
                  <ListBlock
                    title="Safety Notes"
                    items={tool.safety_notes}
                    emptyText="No safety notes listed."
                  />
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title="Private Search Engine"
            subtitle="Search Builder Core's own saved knowledge base and rebuild the internal index when you add new notes."
          >
            <div className="grid gap-4 xl:grid-cols-2">
              <form className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={handlePrivateSearch}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Search query</label>
                  <input
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search saved knowledge, notes, or summaries"
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                  />
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                    Search private index
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRebuildIndex()}
                    className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900"
                  >
                    Rebuild index
                  </button>
                </div>
                {searchMessage ? <p className="text-sm text-slate-600">{searchMessage}</p> : null}
                <div className="grid gap-3 sm:grid-cols-2">
                  <KeyValue label="Documents" value={searchStatus?.document_count ?? 0} />
                  <KeyValue label="Chunks" value={searchStatus?.chunk_count ?? 0} />
                </div>
              </form>

              <form className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={handleQuickAddDocument}>
                <p className="text-sm font-semibold text-slate-900">Quick add to private index</p>
                <input
                  value={quickDocTitle}
                  onChange={(event) => setQuickDocTitle(event.target.value)}
                  placeholder="Document title"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                />
                <select
                  value={quickDocSourceType}
                  onChange={(event) => setQuickDocSourceType(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                >
                  {["manual", "project", "research", "market", "code", "note"].map((item) => (
                    <option key={item} value={item}>
                      {titleCase(item)}
                    </option>
                  ))}
                </select>
                <textarea
                  value={quickDocText}
                  onChange={(event) => setQuickDocText(event.target.value)}
                  placeholder="Paste text that should be searchable."
                  className="h-32 w-full resize-y rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                />
                <button type="submit" className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900">
                  Save to private search
                </button>
              </form>
            </div>

            {searchResults ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">
                  Search results ({searchResults.results_count ?? 0})
                </p>
                <div className="mt-3 space-y-3">
                  {(searchResults.results ?? []).map((result, index) => (
                    <div key={`${result.document_id ?? "result"}_${index}`} className="rounded-2xl bg-white p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium text-slate-900">{result.title || "Saved source"}</p>
                        <StatusPill tone="slate">{titleCase(result.source_type ?? "saved")}</StatusPill>
                        <StatusPill tone="blue">Score {result.score ?? 0}</StatusPill>
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{result.preview || "No preview available."}</p>
                      {result.url ? (
                        <a className="mt-2 inline-block text-sm text-slate-900 underline" href={result.url} target="_blank" rel="noreferrer">
                          Open source URL
                        </a>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </Panel>

          <Panel
            title="Document Ingest"
            subtitle="Save plain text into Builder Core memory, learning, and private search without needing outside AI."
          >
            <form className="space-y-4" onSubmit={handleDocumentIngest}>
              <input
                value={ingestTitle}
                onChange={(event) => setIngestTitle(event.target.value)}
                placeholder="Document title"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <select
                value={ingestSourceType}
                onChange={(event) => setIngestSourceType(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              >
                {["note", "law", "market", "exam", "code", "research", "project", "manual"].map((item) => (
                  <option key={item} value={item}>
                    {titleCase(item)}
                  </option>
                ))}
              </select>
              <input
                value={ingestTags}
                onChange={(event) => setIngestTags(event.target.value)}
                placeholder="Tags, separated by commas"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <textarea
                value={ingestText}
                onChange={(event) => setIngestText(event.target.value)}
                placeholder="Paste plain text here."
                className="h-40 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                Ingest document
              </button>
            </form>
            {ingestMessage ? <p className="text-sm text-slate-600">{ingestMessage}</p> : null}
          </Panel>

          <Panel
            title="URL Ingest"
            subtitle="Safely fetch one public URL and add readable text to Builder Core private search."
          >
            <form className="space-y-4" onSubmit={handleUrlIngest}>
              <input
                value={urlInput}
                onChange={(event) => setUrlInput(event.target.value)}
                placeholder="https://example.com/article"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <input
                value={urlNote}
                onChange={(event) => setUrlNote(event.target.value)}
                placeholder="Optional note about why this page matters"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                Ingest safe public URL
              </button>
            </form>
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              URL ingest allows one public page only. It blocks localhost, private/internal IPs, .onion links, file URLs,
              login bypass, and paywall bypass.
            </div>
            {urlMessage ? <p className="text-sm text-slate-600">{urlMessage}</p> : null}
            {urlResult ? (
              <div className="grid gap-3 md:grid-cols-2">
                <KeyValue label="Document ID" value={urlResult.document_id ?? "Not created"} />
                <KeyValue label="Chunks Created" value={urlResult.chunks_created ?? 0} />
                <KeyValue label="Text Characters" value={urlResult.text_chars ?? 0} />
                <KeyValue label="Status" value={urlResult.ok ? "Saved" : "Warning"} />
              </div>
            ) : null}
            <ListBlock title="Warnings" items={urlResult?.warnings} emptyText="No URL warnings returned." />
          </Panel>

          <Panel
            title="Crawler Plan"
            subtitle="Plan a safe crawl only. Builder Core does not start uncontrolled crawling from this panel."
          >
            <form className="space-y-4" onSubmit={handleCrawlerPlan}>
              <textarea
                value={crawlSeeds}
                onChange={(event) => setCrawlSeeds(event.target.value)}
                placeholder={"One public seed URL per line\nhttps://example.com"}
                className="h-28 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <input
                type="number"
                min={1}
                max={25}
                value={crawlMaxPages}
                onChange={(event) => setCrawlMaxPages(Number(event.target.value))}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                Create crawl plan
              </button>
            </form>
            {crawlMessage ? <p className="text-sm text-slate-600">{crawlMessage}</p> : null}
            <ListBlock title="Plan Steps" items={crawlResult?.plan_steps} emptyText="No crawl plan created yet." />
            <ListBlock title="Limits" items={crawlResult?.limits} emptyText="No crawl limits returned yet." />
            <ListBlock title="Warnings" items={crawlResult?.warnings} emptyText="No crawl warnings returned." />
          </Panel>

          <Panel
            title="Cloud Storage Status"
            subtitle="See whether Builder Core is using Firestore or local fallback and run a safe storage test."
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <KeyValue label="Mode" value={titleCase(storageStatus?.storage_mode ?? "local")} />
              <KeyValue label="Backend" value={storageStatus?.storage_backend ?? "local_json"} />
              <KeyValue label="Using Firestore" value={storageStatus?.using_firestore ? "Yes" : "No"} />
              <KeyValue label="Fallback Active" value={storageStatus?.using_fallback ? "Yes" : "No"} />
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <KeyValue label="GCP Project" value={storageStatus?.gcp_project_id ?? "missing"} />
              <KeyValue label="GCS Bucket" value={storageStatus?.gcs_bucket_name ?? "missing"} />
              <KeyValue label="Memory Records" value={storageStatus?.project_memory_count ?? 0} />
              <KeyValue label="Search Chunks" value={storageStatus?.search_chunk_count ?? 0} />
            </div>
            <button
              type="button"
              onClick={() => void handleStorageTest()}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-900"
            >
              Run storage test
            </button>
            {storageMessage ? <p className="text-sm text-slate-600">{storageMessage}</p> : null}
            {storageTestResult ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p>Storage used: {titleCase(storageTestResult.storage_used ?? "unknown")}</p>
                <p>Saved: {storageTestResult.saved ? "Yes" : "No"}</p>
                <p>Read back: {storageTestResult.read_back ? "Yes" : "No"}</p>
                <p>Record ID: {storageTestResult.record_id ?? "unknown"}</p>
              </div>
            ) : null}
            <ListBlock title="Warnings" items={storageStatus?.warnings} emptyText="No storage warnings returned." />
          </Panel>

          <Panel
            title="Model Status"
            subtitle="Builder Core defaults to local rule-based logic. Optional local/OpenAI paths stay secondary."
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <KeyValue label="Assistant Mode" value={titleCase(modelStatus?.assistant_mode ?? "local")} />
              <KeyValue label="Active Brain" value={titleCase(modelStatus?.active_brain ?? "local_rule_based")} />
              <KeyValue label="Local Provider" value={titleCase(modelStatus?.local_model_provider ?? "disabled")} />
              <KeyValue label="OpenAI Configured" value={modelStatus?.openai_configured ? "Yes" : "No"} />
            </div>
            <ListBlock title="Warnings" items={modelStatus?.warnings} emptyText="No model warnings returned." />
          </Panel>

          <Panel
            title="Research History"
            subtitle="Create a safe research task or review saved research results. Live internet-wide research is not connected yet."
          >
            <form className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={handleCreateResearchTask}>
              <input
                value={researchTopic}
                onChange={(event) => setResearchTopic(event.target.value)}
                placeholder="Research topic"
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <input
                value={researchGoal}
                onChange={(event) => setResearchGoal(event.target.value)}
                placeholder="Research goal"
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
              />
              <div className="grid gap-4 md:grid-cols-2">
                <select
                  value={researchCategory}
                  onChange={(event) => setResearchCategory(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
                >
                  {["general", "coding", "law", "market", "exam", "politics", "history", "language", "project"].map(
                    (item) => (
                      <option key={item} value={item}>
                        {titleCase(item)}
                      </option>
                    ),
                  )}
                </select>
                <div className="flex flex-wrap gap-3">
                  {SOURCE_OPTIONS.map((source) => (
                    <label key={source} className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={researchSources.includes(source)}
                        onChange={() => toggleResearchSource(source)}
                        className="h-4 w-4 rounded border-slate-300"
                      />
                      {titleCase(source)}
                    </label>
                  ))}
                </div>
              </div>
              <button type="submit" className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                Create research task
              </button>
              {researchMessage ? <p className="text-sm text-slate-600">{researchMessage}</p> : null}
            </form>

            <div className="grid gap-4 xl:grid-cols-[1.2fr,0.8fr]">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Selected research task</p>
                {selectedResearchTask ? (
                  <div className="mt-3 space-y-3">
                    <p className="font-medium text-slate-900">{selectedResearchTask.topic}</p>
                    <p className="text-sm text-slate-600">{selectedResearchTask.summary}</p>
                    <ListBlock title="Findings" items={selectedResearchTask.findings} emptyText="No findings saved." />
                    <ListBlock title="Limitations" items={selectedResearchTask.limitations} emptyText="No limitations saved." />
                    <ListBlock title="Next Steps" items={selectedResearchTask.next_steps} emptyText="No next steps saved." />
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">No research task selected yet.</p>
                )}
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Recent tasks</p>
                <div className="mt-3 space-y-3">
                  {researchTasks.length > 0 ? (
                    researchTasks.map((task) => (
                      <button
                        key={task.research_id ?? createId("research")}
                        type="button"
                        onClick={() => setSelectedResearchTask(task)}
                        className="w-full rounded-2xl bg-white px-4 py-4 text-left"
                      >
                        <p className="font-medium text-slate-900">{task.topic ?? "Saved research task"}</p>
                        <p className="mt-1 text-sm text-slate-600">{task.summary ?? "No summary saved."}</p>
                        <p className="mt-2 text-xs text-slate-500">
                          {titleCase(task.category)} · {titleCase(task.status)} · {formatTime(task.updated_at)}
                        </p>
                      </button>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500">No research tasks saved yet.</p>
                  )}
                </div>
              </div>
            </div>
          </Panel>

          <Panel
            title="Builder Memory"
            subtitle="Project memory, assistant memory, latest summary, and command history."
          >
            {memoryError ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {memoryError}
              </div>
            ) : null}
            <div className="grid gap-4 xl:grid-cols-2">
              <ListBlock
                title="Project Memory"
                items={(memoryData?.project_memory ?? []).map((item) => item.note || item.command)}
                emptyText="No project memory saved yet."
              />
              <ListBlock
                title="Assistant Memory"
                items={(memoryData?.assistant_memory ?? []).map((item) => item.note || item.command)}
                emptyText="No assistant memory saved yet."
              />
              <ListBlock
                title="Chat History"
                items={(memoryData?.chat_history ?? []).map((item) => `${titleCase(item.role)}: ${item.message}`)}
                emptyText="No chat history saved yet."
              />
              <ListBlock
                title="Cloud Ready Notes"
                items={memoryData?.cloud_ready_notes}
                emptyText="No cloud-ready notes saved yet."
              />
            </div>
            {memoryData?.latest_summary ? (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Latest Saved Summary</p>
                <p className="mt-3 text-sm text-slate-700">
                  {memoryData.latest_summary.message || "No summary message saved."}
                </p>
                <ListBlock
                  title="Completed"
                  items={memoryData.latest_summary.what_completed}
                  emptyText="No completed items saved."
                />
                <ListBlock
                  title="Still Needs Manual Setup"
                  items={memoryData.latest_summary.what_still_needs_manual_setup}
                  emptyText="No manual setup items saved."
                />
              </div>
            ) : null}
          </Panel>

          <Panel
            title="Project Learning"
            subtitle="Lessons, known issues, structure summary, and recommended next steps. This is not AI model training."
          >
            {learningError ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {learningError}
              </div>
            ) : null}
            <div className="grid gap-4 xl:grid-cols-2">
              <ListBlock
                title="Lessons"
                items={(learningData?.lessons ?? []).map(
                  (lesson) => `${lesson.command ?? "Saved task"}: ${lesson.lesson_learned ?? "No lesson text"}`,
                )}
                emptyText="No lessons saved yet."
              />
              <ListBlock
                title="Known Issues"
                items={learningData?.known_issues}
                emptyText="No known issues saved yet."
              />
              <ListBlock
                title="Recommended Next Steps"
                items={learningData?.recommended_next_steps}
                emptyText="No recommended next steps returned."
              />
              <ListBlock
                title="Recent Intelligence Modes"
                items={learningData?.recent_intelligence_modes}
                emptyText="No intelligence modes saved yet."
              />
            </div>
            <ListBlock
              title="Project Structure Sample"
              items={learningData?.project_structure_summary?.sample_tree}
              emptyText="Project structure summary is not available yet."
            />
          </Panel>

          <Panel
            title="Self-Improvement"
            subtitle="Builder Core can remember what worked, what failed, and how future instructions should improve."
          >
            <div className="grid gap-4 xl:grid-cols-2">
              <ListBlock
                title="Recent Notes"
                items={(selfImprovementData?.items ?? []).map(
                  (item) => item.next_recommended_improvement || item.project_lesson || item.what_worked,
                )}
                emptyText="No self-improvement notes saved yet."
              />
              <ListBlock
                title="System Notes"
                items={selfImprovementData?.notes}
                emptyText="No self-improvement notes returned."
              />
            </div>
            <KeyValue
              label="Next Recommended Upgrade"
              value={selfImprovementData?.next_recommended_upgrade ?? "No recommendation returned."}
            />
          </Panel>

          <Panel
            title="Latest Codex Prompt"
            subtitle="See the latest saved manual prompt even when the main chat has moved on."
          >
            {latestPrompt ? (
              <div className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <KeyValue label="Task / Command ID" value={latestPrompt.task_id ?? "unknown"} />
                  <KeyValue label="Workflow" value={titleCase(latestPrompt.workflow ?? latestPrompt.status ?? "prompt_ready")} />
                  <KeyValue label="Created" value={formatTime(latestPrompt.created_at)} />
                  <KeyValue label="Command" value={latestPrompt.command ?? "No command saved."} />
                </div>
                <CodePromptBox
                  prompt={latestPrompt.prompt}
                  onCopy={() => {
                    if (latestPrompt.prompt) {
                      void copyText(latestPrompt.prompt, "Latest Codex prompt copied.");
                    }
                  }}
                  copyLabel="Copy Latest Prompt"
                />
              </div>
            ) : (
              <p className="text-sm text-slate-500">No saved Codex prompt yet.</p>
            )}
          </Panel>
        </section>
      </div>
    </main>
  );
}
