"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

const BACKEND_ERROR = "Could not connect to Builder Core backend. Check NEXT_PUBLIC_API_BASE_URL and backend deployment.";
const LIVE_SEARCH_MISSING = "Live internet/search is not connected yet.";

type ProcessStatus = "pending" | "running" | "completed" | "blocked" | "failed";

type ProcessStep = {
  name: string;
  status: ProcessStatus;
  summary: string;
};

type Timeline = {
  before?: unknown[];
  during?: unknown[];
  after?: unknown[];
  event_count?: number;
};

type ManipulationRisk = {
  level?: string;
  signals?: string[];
  explanation?: string;
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
  sources?: unknown[];
  facts?: unknown[];
  claims?: unknown[];
  timeline?: Timeline | null;
  manipulation_risk?: ManipulationRisk | null;
  future_scenarios?: unknown[];
  confidence?: string | null;
  missing_data?: string[];
};

type TaskStatus = {
  command_id?: string;
  status?: string;
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
  codex_direct_connection?: boolean;
  security_firewall?: boolean;
  audit_log?: boolean;
  approval_workflow?: boolean;
};

type ConnectivityStatus = {
  backend?: string;
  frontend_expected_api_url?: string;
  cloud_storage_configured?: boolean;
  live_search_connected?: boolean;
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

const EMPTY_STEPS: ProcessStep[] = [
  { name: "Understanding request", status: "pending", summary: "Waiting for command" },
  { name: "Checking security", status: "pending", summary: "Waiting for command" },
  { name: "Selecting agent", status: "pending", summary: "Waiting for command" },
  { name: "Preparing result", status: "pending", summary: "Waiting for command" },
  { name: "Saving audit log", status: "pending", summary: "Waiting for command" },
];

function statusClasses(status: ProcessStatus | string | undefined) {
  if (status === "completed") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (status === "blocked" || status === "failed") return "border-red-200 bg-red-50 text-red-800";
  if (status === "running" || status === "waiting_for_approval" || status === "research_not_connected") {
    return "border-blue-200 bg-blue-50 text-blue-800";
  }
  return "border-zinc-200 bg-zinc-100 text-zinc-600";
}

function booleanText(value: boolean | undefined) {
  return value ? "Yes" : "No";
}

function hasItems(items?: unknown[]) {
  return Array.isArray(items) && items.length > 0;
}

function TextList({ title, items, emptyText }: { title: string; items?: unknown[]; emptyText?: string }) {
  if (!hasItems(items)) {
    if (!emptyText) return null;
    return (
      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-zinc-700">{title}</h3>
        <p className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-600">{emptyText}</p>
      </section>
    );
  }

  return (
    <section className="grid gap-2">
      <h3 className="text-sm font-semibold text-zinc-700">{title}</h3>
      <ul className="grid gap-2">
        {items?.map((item, index) => (
          <li key={`${title}-${index}`} className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-700">
            {typeof item === "string" ? item : JSON.stringify(item)}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-lg border border-zinc-200 p-3">
      <dt className="text-xs font-semibold uppercase text-zinc-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium">{value}</dd>
    </div>
  );
}

function TimelineSection({ timeline }: { timeline?: Timeline | null }) {
  if (!timeline) return null;
  return (
    <section className="grid gap-2">
      <h3 className="text-sm font-semibold text-zinc-700">Timeline</h3>
      <div className="grid gap-2 md:grid-cols-3">
        <TextList title="Before" items={timeline.before} emptyText="No verified before-events available." />
        <TextList title="During" items={timeline.during} emptyText="No verified during-events available." />
        <TextList title="After" items={timeline.after} emptyText="No verified after-events available." />
      </div>
      <p className="text-xs text-zinc-500">Verified event count: {timeline.event_count ?? 0}</p>
    </section>
  );
}

function ManipulationSection({ risk }: { risk?: ManipulationRisk | null }) {
  if (!risk) return null;
  return (
    <section className="grid gap-2 rounded-lg border border-zinc-200 bg-zinc-50 p-3">
      <h3 className="text-sm font-semibold text-zinc-700">Manipulation risk</h3>
      <p className="text-sm font-medium text-zinc-900">Level: {risk.level ?? "unknown"}</p>
      <p className="text-sm leading-6 text-zinc-700">{risk.explanation ?? "Not enough evidence."}</p>
      <TextList title="Signals" items={risk.signals} emptyText="No text-only manipulation signals detected." />
    </section>
  );
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [steps, setSteps] = useState<ProcessStep[]>(EMPTY_STEPS);
  const [result, setResult] = useState<CommandResponse | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState("");
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [connectivity, setConnectivity] = useState<ConnectivityStatus | null>(null);
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadStatus() {
      try {
        const [connectivityResponse, systemResponse, storageResponse] = await Promise.all([
          fetch(`${API_BASE}/connectivity/status`),
          fetch(`${API_BASE}/system/status`),
          fetch(`${API_BASE}/storage/status`),
        ]);
        if (cancelled) return;
        setConnectivity(connectivityResponse.ok ? await connectivityResponse.json() : null);
        setSystemStatus(systemResponse.ok ? await systemResponse.json() : null);
        setStorageStatus(storageResponse.ok ? await storageResponse.json() : null);
      } catch {
        if (!cancelled) {
          setConnectivity(null);
          setSystemStatus(null);
          setStorageStatus(null);
          setError(BACKEND_ERROR);
        }
      }
    }
    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  const statusLine = useMemo(() => {
    if (!connectivity && !systemStatus) return "Backend status unavailable";
    const backend = connectivity?.backend ?? systemStatus?.status ?? "unknown";
    const storage = storageStatus?.storage_mode ?? connectivity?.storage_mode ?? "unknown storage";
    const search = connectivity?.live_search_connected ? "live search connected" : "live search not connected";
    const codex = connectivity?.codex_direct_connection ? "Codex connected" : "Codex not directly connected";
    return `${backend} / ${storage} storage / ${search} / ${codex}`;
  }, [connectivity, storageStatus, systemStatus]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage || submitting) return;

    setSubmitting(true);
    setError("");
    setResult(null);
    setTaskStatus(null);
    setSteps([
      { name: "Understanding request", status: "running", summary: "Sending command to backend" },
      ...EMPTY_STEPS.slice(1),
    ]);

    try {
      const response = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: cleanMessage }),
      });

      if (!response.ok) throw new Error("Command request failed");

      const data: CommandResponse = await response.json();
      setResult(data);
      setSteps(data.process_steps);
      setTaskStatus(data.task_status ?? null);
      setMessage("");

      const taskResponse = await fetch(`${API_BASE}/tasks/${data.command_id}`);
      if (taskResponse.ok) setTaskStatus(await taskResponse.json());
    } catch {
      setError(BACKEND_ERROR);
      setSteps([
        { name: "Understanding request", status: "failed", summary: "Backend command endpoint unavailable" },
        { name: "Checking security", status: "pending", summary: "Not run" },
        { name: "Selecting agent", status: "pending", summary: "Not run" },
        { name: "Preparing result", status: "pending", summary: "Not run" },
        { name: "Saving audit log", status: "pending", summary: "Not run" },
      ]);
    } finally {
      setSubmitting(false);
    }
  }

  const final = result?.final_result;
  const liveSearchMissing = Boolean(
    final?.summary?.includes(LIVE_SEARCH_MISSING) ||
      final?.missing_data?.some((item) => item.toLowerCase().includes("live search")) ||
      connectivity?.warnings?.some((item) => item.includes(LIVE_SEARCH_MISSING)),
  );

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-6 text-zinc-950 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-5xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-zinc-200 pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-blue-700">Builder Core</p>
            <h1 className="text-2xl font-semibold tracking-normal">Production Connection Foundation</h1>
          </div>
          <p className="text-sm text-zinc-600">{statusLine}</p>
        </header>

        <section className="grid gap-2 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Backend" value={connectivity?.backend ?? "unavailable"} />
            <Field label="API URL" value={API_BASE} />
            <Field label="Storage" value={`${storageStatus?.storage_mode ?? connectivity?.storage_mode ?? "unknown"}${storageStatus?.local_fallback ? " fallback" : ""}`} />
          </div>
          {storageStatus?.message ? <p className="text-sm text-zinc-600">{storageStatus.message}</p> : null}
          {connectivity?.warnings?.map((warning) => (
            <p key={warning} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
              {warning}
            </p>
          ))}
        </section>

        <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <label htmlFor="builder-command" className="text-sm font-medium text-zinc-700">Command</label>
          <textarea
            id="builder-command"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask Builder Core anything..."
            className="min-h-32 resize-y rounded-lg border border-zinc-300 bg-white px-3 py-3 text-base outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting || !message.trim()}
              className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-600"
            >
              Run
            </button>
          </div>
        </form>

        <section className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Process</h2>
            {result ? <span className="text-xs text-zinc-500">{result.command_id}</span> : null}
          </div>
          <ol className="grid gap-2">
            {steps.map((step) => (
              <li key={step.name} className="grid gap-2 rounded-lg border border-zinc-200 p-3 sm:grid-cols-[12rem,8rem,1fr] sm:items-center">
                <span className="font-medium text-zinc-900">{step.name}</span>
                <span className={`w-fit rounded-md border px-2 py-1 text-xs font-semibold uppercase ${statusClasses(step.status)}`}>
                  {step.status}
                </span>
                <span className="text-sm text-zinc-600">{step.summary}</span>
              </li>
            ))}
          </ol>
          {taskStatus ? (
            <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3">
              <p className="text-sm font-semibold text-zinc-800">Latest task status: {taskStatus.status ?? "unknown"}</p>
              <ul className="mt-2 grid gap-1 text-sm text-zinc-600">
                {taskStatus.steps?.map((step, index) => (
                  <li key={`${step.code}-${index}`}>{step.code}: {step.summary}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold">Final Result</h2>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}

          {final ? (
            <div className="grid gap-4">
              {liveSearchMissing ? (
                <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
                  {LIVE_SEARCH_MISSING}
                </p>
              ) : null}

              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <Field label="Type" value={final.type} />
                <Field label="Selected agent" value={final.selected_agent} />
                <Field label="Risk level" value={final.risk_level} />
                <Field label="Approval required" value={booleanText(final.approval_required)} />
                <Field label="Blocked" value={booleanText(final.blocked)} />
              </dl>

              {final.approval_request ? (
                <section className="grid gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <h3 className="text-sm font-semibold text-amber-950">Approval required</h3>
                  <p className="text-sm text-amber-900">Approval ID: {final.approval_request.approval_id}</p>
                  <p className="text-sm text-amber-900">Action: {final.approval_request.action}</p>
                  <p className="text-sm text-amber-900">Status: {final.approval_request.status}</p>
                  <p className="text-sm text-amber-900">No action has been executed.</p>
                </section>
              ) : null}

              <div className="grid gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-700">Summary</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-700">{final.summary}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-zinc-700">Recommended next step</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-700">{final.recommended_next_step}</p>
                </div>
              </div>

              <TextList title="Sources" items={final.sources} emptyText={final.confidence ? "No verified sources returned." : undefined} />
              <TextList title="Facts" items={final.facts} emptyText={final.confidence ? "No verified facts returned." : undefined} />
              <TextList title="Claims" items={final.claims} emptyText={final.confidence ? "No claims verified from sources." : undefined} />
              <TimelineSection timeline={final.timeline} />
              <ManipulationSection risk={final.manipulation_risk} />
              <TextList title="Missing data" items={final.missing_data} />
              <TextList title="Future scenarios" items={final.future_scenarios} />
              {final.confidence ? <p className="text-sm font-semibold text-zinc-700">Confidence: {final.confidence}</p> : null}
            </div>
          ) : (
            !error && <p className="text-sm text-zinc-500">No result yet.</p>
          )}
        </section>
      </div>
    </main>
  );
}