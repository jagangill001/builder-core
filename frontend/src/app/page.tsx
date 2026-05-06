"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

type ProcessStatus = "pending" | "running" | "completed" | "blocked" | "failed";

type ProcessStep = {
  name: string;
  status: ProcessStatus;
  summary: string;
};

type FinalResult = {
  type: string;
  summary: string;
  selected_agent: string;
  risk_level: string;
  approval_required: boolean;
  blocked: boolean;
  recommended_next_step: string;
};

type CommandResponse = {
  command_id: string;
  needs_clarification: boolean;
  questions: string[];
  process_steps: ProcessStep[];
  final_result: FinalResult;
};

type SystemStatus = {
  status: string;
  service: string;
  phase: string;
  live_search_connected: boolean;
  codex_direct_connection: boolean;
  security_firewall: boolean;
  audit_log: boolean;
};

const EMPTY_STEPS: ProcessStep[] = [
  { name: "Understanding request", status: "pending", summary: "Waiting for command" },
  { name: "Checking security", status: "pending", summary: "Waiting for command" },
  { name: "Selecting agent", status: "pending", summary: "Waiting for command" },
  { name: "Preparing result", status: "pending", summary: "Waiting for command" },
  { name: "Saving audit log", status: "pending", summary: "Waiting for command" },
];

function statusClasses(status: ProcessStatus) {
  if (status === "completed") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (status === "blocked" || status === "failed") {
    return "border-red-200 bg-red-50 text-red-800";
  }
  if (status === "running") {
    return "border-blue-200 bg-blue-50 text-blue-800";
  }
  return "border-zinc-200 bg-zinc-100 text-zinc-600";
}

function booleanText(value: boolean) {
  return value ? "Yes" : "No";
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [steps, setSteps] = useState<ProcessStep[]>(EMPTY_STEPS);
  const [result, setResult] = useState<CommandResponse | null>(null);
  const [error, setError] = useState("");
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/system/status`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data: SystemStatus | null) => setSystemStatus(data))
      .catch(() => setSystemStatus(null));
  }, []);

  const statusLine = useMemo(() => {
    if (!systemStatus) {
      return "Backend status unavailable";
    }

    const search = systemStatus.live_search_connected ? "live search connected" : "live search not connected";
    const codex = systemStatus.codex_direct_connection ? "Codex connected" : "Codex not directly connected";
    return `${systemStatus.status} / ${search} / ${codex}`;
  }, [systemStatus]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage || submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    setResult(null);
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

      if (!response.ok) {
        throw new Error("Command request failed");
      }

      const data: CommandResponse = await response.json();
      setResult(data);
      setSteps(data.process_steps);
      setMessage("");
    } catch {
      setError("Builder Core could not reach the backend command endpoint.");
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

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-6 text-zinc-950 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-5xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-zinc-200 pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Builder Core</p>
            <h1 className="text-2xl font-semibold tracking-normal">Core Command System</h1>
          </div>
          <p className="text-sm text-zinc-600">{statusLine}</p>
        </header>

        <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <label htmlFor="builder-command" className="text-sm font-medium text-zinc-700">
            Command
          </label>
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
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold">Final Result</h2>
          {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}

          {result ? (
            <div className="grid gap-4">
              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <div className="rounded-lg border border-zinc-200 p-3">
                  <dt className="text-xs font-semibold uppercase text-zinc-500">Type</dt>
                  <dd className="mt-1 text-sm font-medium">{result.final_result.type}</dd>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <dt className="text-xs font-semibold uppercase text-zinc-500">Selected agent</dt>
                  <dd className="mt-1 break-words text-sm font-medium">{result.final_result.selected_agent}</dd>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <dt className="text-xs font-semibold uppercase text-zinc-500">Risk level</dt>
                  <dd className="mt-1 text-sm font-medium">{result.final_result.risk_level}</dd>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <dt className="text-xs font-semibold uppercase text-zinc-500">Approval required</dt>
                  <dd className="mt-1 text-sm font-medium">{booleanText(result.final_result.approval_required)}</dd>
                </div>
                <div className="rounded-lg border border-zinc-200 p-3">
                  <dt className="text-xs font-semibold uppercase text-zinc-500">Blocked</dt>
                  <dd className="mt-1 text-sm font-medium">{booleanText(result.final_result.blocked)}</dd>
                </div>
              </dl>

              <div className="grid gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-700">Summary</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-700">{result.final_result.summary}</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-zinc-700">Recommended next step</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-700">{result.final_result.recommended_next_step}</p>
                </div>
              </div>
            </div>
          ) : (
            !error && <p className="text-sm text-zinc-500">No result yet.</p>
          )}
        </section>
      </div>
    </main>
  );
}

