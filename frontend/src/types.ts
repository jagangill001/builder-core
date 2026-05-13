export type TaskLog = {
  timestamp: string;
  stage: string;
  level: string;
  message: string;
};

export type TaskSource = {
  title: string;
  url: string;
  snippet: string;
  rank: string;
  reason: string;
};

export type TaskSummary = {
  what_user_asked: string;
  workflow_used: string;
  tools_connectors_used: string[];
  files_touched: string[];
  result: string;
  errors: string[];
  warnings: string[];
  next_step: string;
};

export type TaskRecord = {
  task_id: string;
  original_message: string;
  normalized_message: string;
  detected_intents: string[];
  workflow: string;
  status: string;
  progress: number;
  current_stage: string;
  logs: TaskLog[];
  result: Record<string, unknown> | null;
  sources: TaskSource[];
  warnings: string[];
  errors: string[];
  created_at: string;
  updated_at: string;
  priority: string;
  timeout_seconds: number;
  queued: boolean;
  summary: TaskSummary | null;
};

export type ConnectorStatus = {
  name: string;
  enabled: boolean;
  configured: boolean;
  provider: string;
  required_env_vars: string[];
  capabilities: string[];
  health: string;
  last_error: string | null;
  admin_required: boolean;
  placeholder: boolean;
  is_real_execution: boolean;
};

export type DatabaseStatus = {
  connected: boolean;
  database_url_configured: boolean;
  provider: string;
  fallback_in_memory: boolean;
  last_error: string | null;
  default_sqlite_url?: string;
  database_path?: string | null;
};

export type SystemStatus = {
  status: string;
  service: string;
  phase: string;
  backend_online: boolean;
  task_engine_ready: boolean;
  project_memory_loaded: boolean;
  configured_connectors: Record<string, boolean>;
  frontend_allowed_origins: string[];
  database_connected: boolean;
  database: DatabaseStatus;
  worker_enabled: boolean;
  auth_enabled: boolean;
  secrets_visible: boolean;
  placeholders: string[];
};

export type WorkflowGraph = {
  nodes: { id: string; label: string }[];
  edges: { from: string; to: string }[];
  current_node: string;
  completed_nodes: string[];
  failed_nodes: string[];
};

export type ProjectSummary = {
  project_name: string;
  repo: string;
  live_frontend_url: string;
  live_backend_url: string;
  backend_folder: string;
  frontend_folder: string;
  current_stack: string[];
  known_problems: string[];
  completed_fixes: string[];
  pending_work: string[];
  next_recommended_steps: string[];
};

export type HealthTarget = {
  url_configured: boolean;
  reachable: boolean;
  status_code: number | null;
  response_time_ms: number | null;
  error: string | null;
};

export type DeploymentHealth = {
  backend: HealthTarget;
  frontend: HealthTarget;
  environment_checklist: { name: string; ok: boolean; details?: Record<string, unknown>; placeholder?: boolean }[];
  warnings: string[];
};

export type SelfTest = {
  ok: boolean;
  passed: number;
  total: number;
  checks: { name: string; ok: boolean; detail: unknown }[];
  database: DatabaseStatus;
};

export type ReleaseChecklist = {
  push_ready: boolean;
  reason: string;
  items: { name: string; ok: boolean; detail: string }[];
};
