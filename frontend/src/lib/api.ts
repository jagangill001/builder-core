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

export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

type ApiOptions = {
  adminToken?: string;
};

function headers(options: ApiOptions = {}) {
  const output: Record<string, string> = { "Content-Type": "application/json" };
  if (options.adminToken?.trim()) {
    output.Authorization = `Bearer ${options.adminToken.trim()}`;
  }
  return output;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      detail = JSON.stringify(await response.json());
    } catch {
      // Keep HTTP status text.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function getSystemStatus() {
  return request<SystemStatus>("/system/status");
}

export function getProjectSummary() {
  return request<ProjectSummary>("/project/summary");
}

export function getConnectors() {
  return request<{ items: ConnectorStatus[] }>("/connectors");
}

export function getDeploymentStatus() {
  return request<Record<string, unknown>>("/deployment/status");
}

export function getDeploymentHealth() {
  return request<DeploymentHealth>("/deployment/health");
}

export function getSelfTest() {
  return request<SelfTest>("/system/self-test");
}

export function getReleaseChecklist() {
  return request<ReleaseChecklist>("/system/release-checklist");
}

export function getLessons() {
  return request<{ items: string[] }>("/project/lessons");
}

export function getRecommendations() {
  return request<{ items: string[] }>("/project/recommendations");
}

export function createTask(message: string, options: ApiOptions = {}) {
  return request<TaskRecord>("/tasks/create", {
    method: "POST",
    headers: headers(options),
    body: JSON.stringify({ message }),
  });
}

export function getTask(taskId: string) {
  return request<TaskRecord>(`/tasks/${taskId}`);
}

export function getWorkflow(taskId: string) {
  return request<WorkflowGraph>(`/tasks/${taskId}/workflow`);
}

export function packageCodexTask(instruction: string, options: ApiOptions = {}) {
  return request<Record<string, unknown>>("/integrations/codex/package-task", {
    method: "POST",
    headers: headers(options),
    body: JSON.stringify({ instruction }),
  });
}

export function createGithubIssue(title: string, body: string, options: ApiOptions = {}) {
  return request<Record<string, unknown>>("/integrations/github/create-issue", {
    method: "POST",
    headers: headers(options),
    body: JSON.stringify({ title, body }),
  });
}
