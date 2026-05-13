"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  API_BASE,
  createTask,
  getConnectors,
  getDeploymentHealth,
  getDeploymentStatus,
  getLessons,
  getProjectSummary,
  getReleaseChecklist,
  getRecommendations,
  getSelfTest,
  getSystemStatus,
  getTask,
  getWorkflow,
} from "@/lib/api";
import type {
  ConnectorStatus,
  DeploymentHealth,
  ProjectSummary,
  ReleaseChecklist,
  SelfTest,
  SystemStatus,
  TaskRecord,
  WorkflowGraph,
} from "@/types";

const STAGES = ["received", "safety_check", "planning", "routing", "executing", "summarizing", "completed"];

function pillClass(value: string) {
  if (["completed", "ready", "connected", "ok"].includes(value)) {
    return "border-emerald-300 bg-emerald-50 text-emerald-800";
  }
  if (["failed", "not_configured", "blocked", "error"].some((term) => value.includes(term))) {
    return "border-rose-300 bg-rose-50 text-rose-800";
  }
  if (value.includes("placeholder") || value.includes("needs")) {
    return "border-amber-300 bg-amber-50 text-amber-900";
  }
  return "border-sky-300 bg-sky-50 text-sky-800";
}

function textValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [adminToken, setAdminToken] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowGraph | null>(null);
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [deployment, setDeployment] = useState<Record<string, unknown> | null>(null);
  const [deploymentHealth, setDeploymentHealth] = useState<DeploymentHealth | null>(null);
  const [selfTest, setSelfTest] = useState<SelfTest | null>(null);
  const [releaseChecklist, setReleaseChecklist] = useState<ReleaseChecklist | null>(null);
  const [lessons, setLessons] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshDashboard();
  }, []);

  useEffect(() => {
    if (!task || ["completed", "failed", "cancelled"].includes(task.status)) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const nextTask = await getTask(task.task_id);
        setTask(nextTask);
        setWorkflow(await getWorkflow(nextTask.task_id));
      } catch (pollError) {
        setError(`Task polling failed: ${(pollError as Error).message}`);
      }
    }, 1200);

    return () => window.clearInterval(interval);
  }, [task]);

  const resultMessage = useMemo(() => {
    if (!task?.result) {
      return "No result yet.";
    }
    return textValue(task.result.message);
  }, [task]);

  async function refreshDashboard() {
    try {
      const [systemData, connectorData, projectData, deploymentData, lessonData, recommendationData] = await Promise.all([
        getSystemStatus(),
        getConnectors(),
        getProjectSummary(),
        getDeploymentStatus(),
        getLessons(),
        getRecommendations(),
      ]);
      const [deploymentHealthData, selfTestData, releaseChecklistData] = await Promise.all([
        getDeploymentHealth(),
        getSelfTest(),
        getReleaseChecklist(),
      ]);
      setSystem(systemData);
      setConnectors(connectorData.items);
      setProject(projectData);
      setDeployment(deploymentData);
      setDeploymentHealth(deploymentHealthData);
      setSelfTest(selfTestData);
      setReleaseChecklist(releaseChecklistData);
      setLessons(lessonData.items);
      setRecommendations(recommendationData.items);
      setError("");
    } catch (dashboardError) {
      setError(`Backend unavailable or returned an error: ${(dashboardError as Error).message}`);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanMessage = message.trim();
    if (!cleanMessage || submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    setWorkflow(null);

    try {
      const created = await createTask(cleanMessage, { adminToken });
      setTask(created);
      setWorkflow(await getWorkflow(created.task_id));
      setMessage("");
      await refreshDashboard();
    } catch (submitError) {
      setError(`Command failed: ${(submitError as Error).message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6f8fb] px-4 py-5 text-slate-950 sm:px-6">
      <div className="mx-auto grid max-w-7xl gap-4">
        <header className="flex flex-col gap-3 border-b border-slate-200 pb-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-sky-700">Builder Core</p>
            <h1 className="text-2xl font-semibold">Command Operating System</h1>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-semibold">
            <span className={`rounded-md border px-2.5 py-1 ${pillClass(system?.backend_online ? "ok" : "error")}`}>
              Backend {system?.backend_online ? "online" : "unavailable"}
            </span>
            <span className={`rounded-md border px-2.5 py-1 ${pillClass(system?.auth_enabled ? "ready" : "not_configured")}`}>
              Admin {system?.auth_enabled ? "configured" : "not configured"}
            </span>
            <span className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-slate-700">{API_BASE}</span>
          </div>
        </header>

        {error ? <div className="rounded-md border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">{error}</div> : null}

        <section className="grid gap-4 lg:grid-cols-[1.2fr,0.8fr]">
          <form onSubmit={handleSubmit} className="grid gap-3 rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Command Center</h2>
              <button
                type="button"
                onClick={refreshDashboard}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Refresh
              </button>
            </div>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="What is Builder Core status?"
              className="min-h-32 resize-y rounded-md border border-slate-300 bg-white px-3 py-3 text-base outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-100"
            />
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <label className="grid gap-1 text-sm text-slate-700 sm:min-w-80">
                Admin token
                <input
                  value={adminToken}
                  onChange={(event) => setAdminToken(event.target.value)}
                  type="password"
                  placeholder="Only stored in browser state"
                  className="rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-100"
                />
              </label>
              <button
                type="submit"
                disabled={submitting || !message.trim()}
                className="rounded-md bg-sky-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
              >
                {submitting ? "Running" : "Run command"}
              </button>
            </div>
          </form>

          <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold">Backend Connection</h2>
            <div className="grid gap-2 text-sm text-slate-700">
              <p>Status: {system ? `${system.status} / ${system.phase}` : "Unavailable"}</p>
              <p>Task engine: {system?.task_engine_ready ? "Ready" : "Not confirmed"}</p>
              <p>Database: {system?.database_connected ? "Connected" : "Fallback or unavailable"}</p>
              <p>DB provider: {system?.database?.provider ?? "unknown"} / fallback {system?.database?.fallback_in_memory ? "yes" : "no"}</p>
              <p>Worker: {system?.worker_enabled ? "External placeholder enabled" : "Immediate processing"}</p>
              <p>Secrets visible: {system?.secrets_visible ? "Unexpected" : "No"}</p>
            </div>
          </section>
        </section>

        <section className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
          <section className="rounded-md border border-slate-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Task Progress</h2>
              <span className="text-xs text-slate-500">{task?.task_id ?? "No task yet"}</span>
            </div>
            <div className="mb-3 h-3 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-sky-600 transition-[width]" style={{ width: `${task?.progress ?? 0}%` }} />
            </div>
            <div className="grid gap-2 text-sm text-slate-700">
              <p>Status: {task?.status ?? "Waiting"}</p>
              <p>Current stage: {task?.current_stage ?? "Not started"}</p>
              <p>Workflow: {task?.workflow ?? "Not selected"}</p>
              <p>Detected intents: {task?.detected_intents.join(", ") || "None"}</p>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Stage Timeline</h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {STAGES.map((stage) => {
                const isDone = workflow?.completed_nodes.includes(stage);
                const isCurrent = workflow?.current_node === stage;
                const isFailed = workflow?.failed_nodes.includes(stage);
                const state = isFailed ? "failed" : isDone ? "completed" : isCurrent ? "running" : "pending";
                return (
                  <div key={stage} className={`rounded-md border p-3 text-sm ${pillClass(state)}`}>
                    <p className="font-semibold">{stage.replace("_", " ")}</p>
                    <p className="mt-1">{state}</p>
                  </div>
                );
              })}
            </div>
          </section>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Logs</h2>
            <div className="grid max-h-80 gap-2 overflow-auto text-sm">
              {task?.logs.length ? (
                task.logs.map((log, index) => (
                  <div key={`${log.timestamp}-${index}`} className="rounded-md border border-slate-200 bg-slate-50 p-2">
                    <p className="font-semibold text-slate-800">{log.stage} / {log.level}</p>
                    <p className="text-slate-700">{log.message}</p>
                    <p className="text-xs text-slate-500">{log.timestamp}</p>
                  </div>
                ))
              ) : (
                <p className="text-slate-500">No backend logs yet.</p>
              )}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Final Result</h2>
            <p className="mb-3 text-sm leading-6 text-slate-700">{resultMessage}</p>
            {task?.summary ? (
              <div className="grid gap-2 text-sm text-slate-700">
                <p>Next step: {task.summary.next_step || "Not provided"}</p>
                <p>Connectors used: {task.summary.tools_connectors_used.join(", ") || "None"}</p>
              </div>
            ) : null}
          </section>
        </section>

        <section className="grid gap-4 xl:grid-cols-3">
          <Panel title="Sources">
            {task?.sources.length ? task.sources.map((source) => (
              <div key={`${source.title}-${source.url}`} className="rounded-md border border-slate-200 p-3 text-sm">
                <p className="font-semibold">{source.title || "Untitled source"}</p>
                <p className="text-slate-600">{source.rank}: {source.reason}</p>
                {source.url ? <a className="text-sky-700 underline" href={source.url}>{source.url}</a> : null}
              </div>
            )) : <p className="text-sm text-slate-500">No sources attached.</p>}
          </Panel>

          <Panel title="Warnings">
            {task?.warnings.length ? task.warnings.map((warning) => (
              <p key={warning} className="rounded-md border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900">{warning}</p>
            )) : <p className="text-sm text-slate-500">No warnings.</p>}
          </Panel>

          <Panel title="Errors">
            {task?.errors.length ? task.errors.map((taskError) => (
              <p key={taskError} className="rounded-md border border-rose-300 bg-rose-50 p-2 text-sm text-rose-900">{taskError}</p>
            )) : <p className="text-sm text-slate-500">No errors.</p>}
          </Panel>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <Panel title="Project Summary">
            <div className="grid gap-2 text-sm text-slate-700">
              <p>{project?.project_name ?? "Builder Core"} / {project?.repo ?? "Repo not loaded"}</p>
              <p>Backend: {project?.backend_folder ?? "backend"} / Frontend: {project?.frontend_folder ?? "frontend"}</p>
              <p>Stack: {project?.current_stack.join(", ") ?? "Not loaded"}</p>
              <List items={project?.pending_work ?? []} empty="No pending work loaded." />
            </div>
          </Panel>

          <Panel title="Integration Status">
            <div className="grid gap-2 sm:grid-cols-2">
              {connectors.map((connector) => (
                <div key={connector.name} className="rounded-md border border-slate-200 p-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold">{connector.name}</p>
                    <span className={`rounded-md border px-2 py-0.5 text-xs ${pillClass(connector.health)}`}>{connector.health}</span>
                  </div>
                  <p className="mt-1 text-slate-600">{connectorExecutionLabel(connector)}</p>
                  <p className="text-xs text-slate-500">Provider: {connector.provider}</p>
                  {connector.admin_required ? <p className="text-xs text-amber-800">Admin required</p> : null}
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-4 xl:grid-cols-3">
          <Panel title="GitHub Status">
            <ConnectorMini connector={connectors.find((item) => item.name === "github")} />
          </Panel>
          <Panel title="Deployment Status">
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap text-xs text-slate-700">{textValue(deployment)}</pre>
          </Panel>
          <Panel title="Deployment Health">
            {deploymentHealth ? (
              <div className="grid gap-3 text-sm text-slate-700">
                <HealthLine label="Backend" value={deploymentHealth.backend} />
                <HealthLine label="Frontend" value={deploymentHealth.frontend} />
                <List items={deploymentHealth.warnings} empty="No deployment warnings." />
              </div>
            ) : <p className="text-sm text-slate-500">Deployment health not loaded.</p>}
          </Panel>
          <Panel title="Admin Mode">
            <p className="text-sm text-slate-700">{adminToken.trim() ? "Admin token entered for outgoing requests." : "Admin token not entered."}</p>
            <p className="mt-2 text-xs text-slate-500">The token stays in browser state and is sent as an Authorization header only when present.</p>
          </Panel>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <Panel title="Self-Test">
            {selfTest ? (
              <div className="grid gap-2 text-sm text-slate-700">
                <p>{selfTest.passed}/{selfTest.total} checks passed</p>
                {selfTest.checks.map((check) => (
                  <div key={check.name} className={`rounded-md border p-2 ${pillClass(check.ok ? "ok" : "warning")}`}>
                    <p className="font-semibold">{check.name}</p>
                    <p className="text-xs">{textValue(check.detail)}</p>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">Self-test not loaded.</p>}
          </Panel>
          <Panel title="Release Checklist">
            {releaseChecklist ? (
              <div className="grid gap-2 text-sm text-slate-700">
                <p>Push ready: {releaseChecklist.push_ready ? "Yes" : "No"}</p>
                <p className="text-xs text-slate-500">{releaseChecklist.reason}</p>
                {releaseChecklist.items.map((item) => (
                  <div key={item.name} className={`rounded-md border p-2 ${pillClass(item.ok ? "ok" : "warning")}`}>
                    <p className="font-semibold">{item.name}</p>
                    <p className="text-xs">{item.detail}</p>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">Release checklist not loaded.</p>}
          </Panel>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <Panel title="Lessons Learned">
            <List items={lessons} empty="No lessons loaded." />
          </Panel>
          <Panel title="Recommended Next Steps">
            <List items={recommendations} empty="No recommendations loaded." />
          </Panel>
        </section>
      </div>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function List({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">{empty}</p>;
  }
  return (
    <ul className="grid gap-2 text-sm text-slate-700">
      {items.map((item) => (
        <li key={item} className="rounded-md border border-slate-200 bg-slate-50 p-2">{item}</li>
      ))}
    </ul>
  );
}

function ConnectorMini({ connector }: { connector?: ConnectorStatus }) {
  if (!connector) {
    return <p className="text-sm text-slate-500">GitHub connector not loaded.</p>;
  }
  return (
    <div className="grid gap-2 text-sm text-slate-700">
      <p>Configured: {connector.configured ? "Yes" : "No"}</p>
      <p>Execution: {connectorExecutionLabel(connector)}</p>
      <p>Health: {connector.health}</p>
      <p>Required env: {connector.required_env_vars.join(", ")}</p>
      <p>{connector.last_error ?? "No connector error reported."}</p>
    </div>
  );
}

function connectorExecutionLabel(connector: ConnectorStatus) {
  if (!connector.configured) {
    return "Not configured";
  }
  if (connector.is_real_execution) {
    return "Real";
  }
  return "Placeholder";
}

function HealthLine({ label, value }: { label: string; value: DeploymentHealth["backend"] }) {
  return (
    <div className="rounded-md border border-slate-200 p-2">
      <p className="font-semibold">{label}: {value.reachable ? "reachable" : "not reachable"}</p>
      <p className="text-xs text-slate-500">
        configured {value.url_configured ? "yes" : "no"} / status {value.status_code ?? "n/a"} / {value.response_time_ms ?? "n/a"} ms
      </p>
      {value.error ? <p className="text-xs text-rose-700">{value.error}</p> : null}
    </div>
  );
}
