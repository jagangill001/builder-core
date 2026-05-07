"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

const PROD_BACKEND_URL = "https://builder-core-599596796788.us-central1.run.app";
const LOCAL_BACKEND_URL = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 30000;

function configuredApiBase() {
  const configured =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_URL;

  return configured ? configured.replace(/\/$/, "") : "";
}

function isLocalFrontend() {
  if (typeof window === "undefined") return false;
  return window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
}

function isProductionFrontend() {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  return host.includes("run.app") || host.includes("builder-core-frontend");
}

function apiBaseCandidates() {
  const candidates: string[] = [];
  const configured = configuredApiBase();

  if (isLocalFrontend()) candidates.push(LOCAL_BACKEND_URL);
  if (configured) candidates.push(configured);
  if (isProductionFrontend()) candidates.push(PROD_BACKEND_URL);

  candidates.push(PROD_BACKEND_URL, LOCAL_BACKEND_URL);
  return Array.from(new Set(candidates.map((item) => item.replace(/\/$/, ""))));
}

function resolveApiBase() {
  return apiBaseCandidates()[0] ?? LOCAL_BACKEND_URL;
}

const BACKEND_ERROR = "Could not connect to Builder Core backend.";

type ProcessStep = {
  name: string;
  status: string;
  summary: string;
};

type SourceItem = {
  title?: string;
  url?: string;
  snippet?: string;
  summary?: string;
  source_domain?: string;
  opened?: boolean;
  page_excerpt?: string;
};

type EvidenceItem = {
  text?: string;
  classification?: string;
  confidence?: string;
  source_url?: string;
  reason?: string;
  type?: string;
};

type ApprovalRecord = {
  approval_id?: string;
  status?: string;
  action?: string;
  reason?: string;
  risk_level?: string;
};

type FinalResult = {
  type: string;
  summary: string;
  selected_agent: string;
  risk_level: string;
  approval_required: boolean;
  blocked: boolean;
  recommended_next_step: string;
  approval_request?: ApprovalRecord | null;
  sources?: SourceItem[];
  facts?: EvidenceItem[];
  claims?: EvidenceItem[];
  unknowns?: EvidenceItem[];
  confidence?: string | null;
  missing_data?: string[];
  answer?: string | null;
  search_connected?: boolean | null;
  warnings?: string[];
  memory_saved?: boolean | null;
  memory_recalled?: boolean | null;
  recalled_memory_count?: number | null;
  memory_notes?: EvidenceItem[];
  timeline?: Record<string, unknown> | null;
  manipulation_risk?: Record<string, unknown> | null;
  future_scenarios?: unknown[];
};

type TaskStatus = {
  command_id?: string;
  status?: string;
  detected_intent?: string;
  selected_agent?: string;
  approval_required?: boolean;
  approval_id?: string | null;
  blocked?: boolean;
  steps?: Array<{ code?: string; status?: string; summary?: string }>;
};

type CommandResponse = {
  command_id: string;
  needs_clarification: boolean;
  questions: string[];
  process_steps: ProcessStep[];
  final_result: FinalResult;
  task_status?: TaskStatus | null;
};

type SystemStatus = {
  status?: string;
  service?: string;
  phase?: string;
  live_search_connected?: boolean;
  search_provider?: string | null;
  live_search_message?: string | null;
};

type ConnectivityStatus = {
  backend?: string;
  frontend_expected_api_url?: string;
  cloud_storage_configured?: boolean;
  live_search_connected?: boolean;
  search_provider?: string | null;
  live_search_message?: string | null;
  codex_direct_connection?: boolean;
  deployment_executor_connected?: boolean;
  storage_mode?: string;
  warnings?: string[];
};

type StorageStatus = {
  storage_mode?: string;
  cloud_storage_configured?: boolean;
  bucket_name?: string | null;
  local_fallback?: boolean;
  message?: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  recommendedNextStep?: string;
  loading?: boolean;
  response?: CommandResponse;
  taskStatus?: TaskStatus | null;
};

type DetailSection = "sources" | "process" | "facts" | "warnings" | "memory";

async function fetchJsonFromBase<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

async function fetchJsonFromAny<T>(path: string, init?: RequestInit) {
  let lastError: unknown = null;
  for (const baseUrl of apiBaseCandidates()) {
    try {
      const data = await fetchJsonFromBase<T>(baseUrl, path, init);
      return { baseUrl, data };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError ?? new Error("No backend available");
}

function makeId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function answerText(final: FinalResult) {
  if (final.blocked) {
    return `I cannot help with that request because ${final.summary.replace(/^Builder Core cannot help with that action\.\s*/i, "")}`;
  }
  if (final.approval_required) {
    return `This needs approval before any action can happen. ${final.summary}`;
  }
  return final.answer || final.summary;
}

function statusBadge(value: string, connected: boolean | undefined) {
  const styles = connected
    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
    : "border-zinc-200 bg-zinc-100 text-zinc-600";
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${styles}`}>{value}</span>;
}

function DetailButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
        active ? "border-blue-300 bg-blue-50 text-blue-800" : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300"
      }`}
    >
      {children}
    </button>
  );
}

function EmptyDetail({ children }: { children: ReactNode }) {
  return <p className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-600">{children}</p>;
}

function SourcesDetail({ sources }: { sources?: SourceItem[] }) {
  if (!sources?.length) return <EmptyDetail>No sources returned.</EmptyDetail>;

  return (
    <ul className="grid gap-2">
      {sources.map((source, index) => (
        <li key={`${source.url ?? source.title}-${index}`} className="grid gap-2 rounded-lg border border-zinc-200 bg-white p-3 text-sm">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            {source.url ? (
              <a className="font-semibold text-blue-700 underline-offset-2 hover:underline" href={source.url} target="_blank" rel="noreferrer">
                {source.title || source.url}
              </a>
            ) : (
              <span className="font-semibold text-zinc-900">{source.title || "Untitled source"}</span>
            )}
            <span className="text-xs font-medium text-zinc-500">{source.source_domain || "unknown source"}</span>
          </div>
          {source.snippet || source.summary ? <p className="leading-6 text-zinc-700">{source.snippet || source.summary}</p> : null}
          {source.page_excerpt ? <p className="text-xs leading-5 text-zinc-500">Excerpt: {source.page_excerpt}</p> : null}
          <p className="text-xs text-zinc-500">Page opened: {source.opened ? "Yes" : "No"}</p>
        </li>
      ))}
    </ul>
  );
}

function EvidenceDetail({ title, items }: { title: string; items?: EvidenceItem[] }) {
  if (!items?.length) return <EmptyDetail>No {title.toLowerCase()} returned.</EmptyDetail>;

  return (
    <section className="grid gap-2">
      <h4 className="text-xs font-semibold uppercase text-zinc-500">{title}</h4>
      <ul className="grid gap-2">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="grid gap-1 rounded-lg border border-zinc-200 bg-white p-3 text-sm text-zinc-700">
            <p className="leading-6">{item.text ?? JSON.stringify(item)}</p>
            <div className="flex flex-wrap gap-2 text-xs text-zinc-500">
              {item.classification ? <span>{item.classification}</span> : null}
              {item.type ? <span>{item.type}</span> : null}
              {item.confidence ? <span>confidence: {item.confidence}</span> : null}
              {item.source_url ? <a className="text-blue-700 hover:underline" href={item.source_url} target="_blank" rel="noreferrer">source</a> : null}
            </div>
            {item.reason ? <p className="text-xs text-zinc-500">{item.reason}</p> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ProcessDetail({ response, taskStatus }: { response: CommandResponse; taskStatus?: TaskStatus | null }) {
  const steps = response.process_steps ?? [];
  return (
    <div className="grid gap-3">
      {steps.length ? (
        <ol className="grid gap-2">
          {steps.map((step) => (
            <li key={`${response.command_id}-${step.name}`} className="grid gap-1 rounded-lg border border-zinc-200 bg-white p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-zinc-900">{step.name}</span>
                <span className="rounded-full border border-zinc-200 px-2 py-0.5 text-xs text-zinc-500">{step.status}</span>
              </div>
              <p className="text-zinc-600">{step.summary}</p>
            </li>
          ))}
        </ol>
      ) : (
        <EmptyDetail>No process steps returned.</EmptyDetail>
      )}
      {taskStatus?.steps?.length ? (
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-700">
          <p className="font-semibold text-zinc-900">Task status: {taskStatus.status ?? "unknown"}</p>
          <ul className="mt-2 grid gap-1">
            {taskStatus.steps.map((step, index) => (
              <li key={`${step.code}-${index}`}>{step.code}: {step.summary}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function WarningsDetail({ final }: { final: FinalResult }) {
  const warnings = final.warnings ?? [];
  const missing = final.missing_data ?? [];
  if (!warnings.length && !missing.length) return <EmptyDetail>No warnings or missing data returned.</EmptyDetail>;

  return (
    <div className="grid gap-3">
      {warnings.length ? (
        <section className="grid gap-2">
          <h4 className="text-xs font-semibold uppercase text-zinc-500">Warnings</h4>
          {warnings.map((warning) => (
            <p key={warning} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{warning}</p>
          ))}
        </section>
      ) : null}
      {missing.length ? (
        <section className="grid gap-2">
          <h4 className="text-xs font-semibold uppercase text-zinc-500">Missing data</h4>
          {missing.map((item) => (
            <p key={item} className="rounded-lg border border-zinc-200 bg-white p-3 text-sm text-zinc-700">{item}</p>
          ))}
        </section>
      ) : null}
    </div>
  );
}

function MemoryDetail({ final, taskStatus, commandId }: { final: FinalResult; taskStatus?: TaskStatus | null; commandId: string }) {
  return (
    <dl className="grid gap-2 sm:grid-cols-2">
      <Field label="Command ID" value={commandId} />
      <Field label="Memory saved" value={final.memory_saved ? "Yes" : "No"} />
      <Field label="Memory recalled" value={final.memory_recalled ? `Yes (${final.recalled_memory_count ?? 0})` : "No"} />
      <Field label="Audit log" value="Saved by backend" />
      <Field label="Task status" value={taskStatus?.status ?? "unknown"} />
      <Field label="Intent" value={taskStatus?.detected_intent ?? final.type} />
      <Field label="Agent" value={final.selected_agent} />
      <Field label="Approval required" value={final.approval_required ? "Yes" : "No"} />
      <Field label="Risk" value={final.risk_level} />
      {final.memory_notes?.length ? <Field label="Memory notes" value={final.memory_notes.map((item) => item.text).join(" ")} /> : null}
    </dl>
  );
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-3">
      <dt className="text-xs font-semibold uppercase text-zinc-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-zinc-900">{value}</dd>
    </div>
  );
}

function MessageDetails({ message }: { message: ChatMessage }) {
  const [openSections, setOpenSections] = useState<DetailSection[]>([]);
  const response = message.response;
  const final = response?.final_result;
  if (!response || !final) return null;

  function toggle(section: DetailSection) {
    setOpenSections((current) =>
      current.includes(section) ? current.filter((item) => item !== section) : [...current, section],
    );
  }

  return (
    <div className="mt-3 grid gap-3">
      <div className="flex flex-wrap gap-2">
        <DetailButton active={openSections.includes("sources")} onClick={() => toggle("sources")}>Show sources</DetailButton>
        <DetailButton active={openSections.includes("process")} onClick={() => toggle("process")}>Show process</DetailButton>
        <DetailButton active={openSections.includes("facts")} onClick={() => toggle("facts")}>Show facts/claims</DetailButton>
        <DetailButton active={openSections.includes("warnings")} onClick={() => toggle("warnings")}>Show warnings</DetailButton>
        <DetailButton active={openSections.includes("memory")} onClick={() => toggle("memory")}>Show memory/status</DetailButton>
      </div>

      {openSections.includes("sources") ? <SourcesDetail sources={final.sources} /> : null}
      {openSections.includes("process") ? <ProcessDetail response={response} taskStatus={message.taskStatus} /> : null}
      {openSections.includes("facts") ? (
        <div className="grid gap-3">
          <EvidenceDetail title="Facts" items={final.facts} />
          <EvidenceDetail title="Claims" items={final.claims} />
          <EvidenceDetail title="Unknowns" items={final.unknowns} />
        </div>
      ) : null}
      {openSections.includes("warnings") ? <WarningsDetail final={final} /> : null}
      {openSections.includes("memory") ? <MemoryDetail final={final} taskStatus={message.taskStatus} commandId={response.command_id} /> : null}
    </div>
  );
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [connectivity, setConnectivity] = useState<ConnectivityStatus | null>(null);
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  const [activeApiBase, setActiveApiBase] = useState(resolveApiBase());
  const [showSystemDetails, setShowSystemDetails] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadStatus() {
      for (const baseUrl of apiBaseCandidates()) {
        try {
          const [connectivityData, systemData, storageData] = await Promise.all([
            fetchJsonFromBase<ConnectivityStatus>(baseUrl, "/connectivity/status"),
            fetchJsonFromBase<SystemStatus>(baseUrl, "/system/status"),
            fetchJsonFromBase<StorageStatus>(baseUrl, "/storage/status"),
          ]);
          if (cancelled) return;
          setActiveApiBase(baseUrl);
          setConnectivity(connectivityData);
          setSystemStatus(systemData);
          setStorageStatus(storageData);
          return;
        } catch {
          if (cancelled) return;
        }
      }
      if (!cancelled) {
        setConnectivity(null);
        setSystemStatus(null);
        setStorageStatus(null);
      }
    }
    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  const statusSummary = useMemo(() => {
    const backendConnected = connectivity?.backend === "ok" || systemStatus?.status === "ok";
    const searchConnected = Boolean(connectivity?.live_search_connected ?? systemStatus?.live_search_connected);
    const storage = storageStatus?.storage_mode ?? connectivity?.storage_mode ?? "unknown";
    return { backendConnected, searchConnected, storage };
  }, [connectivity, storageStatus, systemStatus]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage || submitting) return;

    const userMessage: ChatMessage = {
      id: makeId("user"),
      role: "user",
      text: cleanMessage,
    };
    const assistantId = makeId("assistant");
    const loadingMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      text: "Searching and preparing answer...",
      loading: true,
    };
    const history = chat
      .filter((item) => !item.loading)
      .slice(-8)
      .map((item) => ({ role: item.role, content: item.text }));

    setChat((current) => [...current, userMessage, loadingMessage]);
    setMessage("");
    setSubmitting(true);

    try {
      const { baseUrl, data } = await fetchJsonFromAny<CommandResponse>("/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: cleanMessage, history }),
      });
      setActiveApiBase(baseUrl);
      let taskStatus = data.task_status ?? null;
      try {
        const taskResponse = await fetchJsonFromBase<TaskStatus>(baseUrl, `/tasks/${data.command_id}`);
        taskStatus = taskResponse;
      } catch {
        taskStatus = data.task_status ?? null;
      }

      const final = data.final_result;
      setChat((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                id: assistantId,
                role: "assistant",
                text: answerText(final),
                recommendedNextStep: final.recommended_next_step,
                response: data,
                taskStatus,
              }
            : item,
        ),
      );
    } catch {
      setChat((current) =>
        current.map((item) =>
          item.id === assistantId
            ? {
                id: assistantId,
                role: "assistant",
                text: BACKEND_ERROR,
              }
            : item,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-5 text-zinc-950 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-4xl flex-col gap-4">
        <header className="grid gap-3 border-b border-zinc-200 pb-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Builder Core</p>
              <h1 className="text-2xl font-semibold tracking-normal">Command Chat</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              {statusBadge(`Backend: ${statusSummary.backendConnected ? "connected" : "unavailable"}`, statusSummary.backendConnected)}
              {statusBadge(`Search: ${statusSummary.searchConnected ? "connected" : "unavailable"}`, statusSummary.searchConnected)}
              {statusBadge(`Storage: ${statusSummary.storage}`, statusSummary.storage !== "unknown")}
            </div>
          </div>

          <div>
            <button
              type="button"
              onClick={() => setShowSystemDetails((value) => !value)}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:border-zinc-300"
            >
              Show system details
            </button>
          </div>

          {showSystemDetails ? (
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <Field label="API URL" value={activeApiBase} />
              <Field label="Backend" value={connectivity?.backend ?? systemStatus?.status ?? "unavailable"} />
              <Field label="Search provider" value={connectivity?.search_provider ?? systemStatus?.search_provider ?? "duckduckgo"} />
              <Field label="Search message" value={connectivity?.live_search_message ?? systemStatus?.live_search_message ?? "unknown"} />
              <Field label="Storage mode" value={storageStatus?.storage_mode ?? connectivity?.storage_mode ?? "unknown"} />
              <Field label="Cloud storage" value={storageStatus?.cloud_storage_configured || connectivity?.cloud_storage_configured ? "configured" : "not configured"} />
            </dl>
          ) : null}
        </header>

        <section className="flex min-h-[22rem] flex-1 flex-col gap-3 overflow-y-auto rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          {chat.length === 0 ? (
            <div className="my-auto grid gap-2 text-center">
              <h2 className="text-lg font-semibold text-zinc-900">Ask Builder Core anything.</h2>
              <p className="text-sm text-zinc-500">Answers appear here as a normal chat. Sources and process details stay tucked away until you ask for them.</p>
            </div>
          ) : null}

          {chat.map((item) => (
            <article key={item.id} className={`flex ${item.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[min(42rem,92%)] rounded-2xl px-4 py-3 shadow-sm ${
                  item.role === "user"
                    ? "rounded-br-md bg-blue-700 text-white"
                    : "rounded-bl-md border border-zinc-200 bg-zinc-50 text-zinc-900"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-6">{item.text}</p>
                {item.loading ? <p className="mt-2 text-xs text-zinc-500">Working...</p> : null}
                {item.recommendedNextStep ? (
                  <p className="mt-2 border-t border-zinc-200 pt-2 text-xs leading-5 text-zinc-500">{item.recommendedNextStep}</p>
                ) : null}
                <MessageDetails message={item} />
              </div>
            </article>
          ))}
        </section>

        <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-zinc-200 bg-white p-3 shadow-sm sm:grid-cols-[1fr,auto]">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask Builder Core anything..."
            className="min-h-20 resize-y rounded-lg border border-zinc-300 bg-white px-3 py-3 text-base outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          />
          <button
            type="submit"
            disabled={submitting || !message.trim()}
            className="h-fit rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-600"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}
