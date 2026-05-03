"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const MODE_OPTIONS = [
  "auto",
  "research",
  "coding",
  "market",
  "project",
  "law",
  "exam",
  "creative",
];

type AnyRecord = Record<string, unknown>;

type DomainSearchResult = {
  title?: string;
  domain?: string;
  url?: string;
  snippet?: string;
  score?: number;
  confidence?: string;
  source_type?: string;
};

type CommandResponse = {
  command_id?: string;
  reply?: string;
  selected_agent_role?: string;
  detected_intents?: string[];
  workflow?: string;
  internal_tools_used?: string[];
  progress?: {
    status?: string;
    steps?: string[];
    agent_plan?: {
      steps?: Array<{ tool?: string; action?: string; status?: string; result_summary?: string }>;
    };
  };
  private_search?: {
    used?: boolean;
    results_count?: number;
    top_sources?: string[];
    results?: Array<{ title?: string; preview?: string; source_type?: string; url?: string; score?: number }>;
  };
  research?: AnyRecord;
  market_analysis?: AnyRecord;
  app_plan?: AnyRecord;
  codex_prompt?: string;
  summary?: AnyRecord;
  approvals_needed?: string[];
  security_warnings?: string[];
  security?: AnyRecord;
  knowledge?: AnyRecord;
  domain_search?: {
    action?: string;
    domain?: string;
    query?: string;
    confidence?: string;
    results_count?: number;
    results?: DomainSearchResult[];
    domains?: Array<{ domain?: string; sources_count?: number; titles?: string[]; urls?: string[] }>;
    urls?: DomainSearchResult[];
    missing_knowledge?: string[];
  };
  knowledge_sources_used?: string[];
  confidence?: string;
  missing_knowledge?: string[];
  limitations?: string[];
  storage_used?: string;
  memory_saved?: boolean;
  next_actions?: string[];
  created_at?: string;
};

type ThreadItem = {
  id: string;
  role: "user" | "assistant";
  content: string;
  result?: CommandResponse;
  error?: string;
};

type StatusBundle = {
  system?: AnyRecord;
  os?: AnyRecord;
  platform?: AnyRecord;
  roles?: AnyRecord;
  tasks?: AnyRecord;
  approvals?: AnyRecord;
  account?: AnyRecord;
  connectors?: AnyRecord;
  security?: AnyRecord;
  securityReport?: AnyRecord;
  hardening?: AnyRecord;
  knowledge?: AnyRecord;
  knowledgeSearch?: AnyRecord;
  roadmap?: AnyRecord;
  roadmapNext?: AnyRecord;
  protectedErrors?: Record<string, string>;
  tools?: AnyRecord;
  search?: AnyRecord;
  storage?: AnyRecord;
  model?: AnyRecord;
  memory?: AnyRecord;
  learning?: AnyRecord;
  selfImprovement?: AnyRecord;
};

function createId(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function titleCase(value?: string | null) {
  if (!value) return "Unknown";
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function parseResponse<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function friendlyProtectedMessage(error: unknown) {
  const message = error instanceof Error ? error.message : "Request failed";
  if (message.includes("401") || message.toLowerCase().includes("required")) {
    return "Admin key required for this panel. Add your admin key in Admin Access.";
  }
  if (message.includes("403") || message.toLowerCase().includes("rejected")) {
    return "Admin key rejected. Check ADMIN_API_KEY.";
  }
  return message;
}

async function requestJson<T>(path: string, init?: RequestInit, adminKey?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(adminKey ? { "X-Admin-Key": adminKey } : {}),
      ...(init?.headers ?? {}),
    },
  });
  const data = await parseResponse<T & { detail?: string }>(response);
  if (!response.ok) {
    throw new Error(data?.detail ?? `Request failed with ${response.status}`);
  }
  return (data ?? ({} as T)) as T;
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="min-w-0 rounded-md border border-slate-200 bg-white px-3 py-2">
      <div className="text-[11px] font-semibold uppercase tracking-normal text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-slate-900">{value ?? "Unknown"}</div>
    </div>
  );
}

function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "green" | "amber" | "blue" | "red" }) {
  const tones = {
    neutral: "border-slate-200 bg-slate-50 text-slate-700",
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    amber: "border-amber-200 bg-amber-50 text-amber-800",
    blue: "border-sky-200 bg-sky-50 text-sky-800",
    red: "border-rose-200 bg-rose-50 text-rose-700",
  };
  return <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${tones[tone]}`}>{children}</span>;
}

function ListBlock({ title, items }: { title: string; items?: unknown[] }) {
  const safeItems = (items ?? []).filter(Boolean).slice(0, 8);
  if (!safeItems.length) return null;
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <ul className="space-y-1 text-sm text-slate-700">
        {safeItems.map((item, index) => (
          <li key={`${title}_${index}`} className="rounded-md border border-slate-200 bg-white px-3 py-2">
            {typeof item === "string" ? item : JSON.stringify(item)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function JsonBlock({ value }: { value: unknown }) {
  if (!value || (typeof value === "object" && Object.keys(value as AnyRecord).length === 0)) return null;
  return (
    <pre className="max-h-72 overflow-auto rounded-md border border-slate-200 bg-slate-950 p-3 text-xs leading-5 text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="rounded-md border border-slate-200 bg-slate-50">
      <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-slate-900">{title}</summary>
      <div className="space-y-3 border-t border-slate-200 p-4">{children}</div>
    </details>
  );
}

function MessageResult({ result }: { result: CommandResponse }) {
  const steps = result.progress?.steps ?? result.progress?.agent_plan?.steps?.map((step) => `${step.tool}: ${step.action}`) ?? [];
  const prompt = result.codex_prompt || (typeof result.app_plan?.codex_prompt === "string" ? result.app_plan.codex_prompt : "");
  const domainResults = result.domain_search?.results ?? [];
  const learnedDomains = result.domain_search?.domains ?? [];

  return (
    <div className="mt-4 space-y-4">
      <div className="flex flex-wrap gap-2">
        {result.selected_agent_role && <Pill tone="blue">{titleCase(result.selected_agent_role)}</Pill>}
        {result.workflow && <Pill>{titleCase(result.workflow)}</Pill>}
        {result.storage_used && <Pill tone={result.storage_used === "firestore" ? "green" : "amber"}>{result.storage_used}</Pill>}
        {typeof result.memory_saved === "boolean" && <Pill tone={result.memory_saved ? "green" : "neutral"}>memory {result.memory_saved ? "saved" : "not saved"}</Pill>}
        {result.confidence && <Pill tone="amber">{titleCase(result.confidence)} confidence</Pill>}
      </div>

      <ListBlock title="Plan / Steps" items={steps} />
      <ListBlock title="Tools Used" items={result.internal_tools_used} />
      <ListBlock title="Approvals Needed" items={result.approvals_needed} />
      <ListBlock title="Security Warnings" items={result.security_warnings} />
      <ListBlock title="Knowledge Sources" items={result.knowledge_sources_used ?? result.private_search?.top_sources} />
      <ListBlock title="Missing Knowledge" items={result.missing_knowledge ?? ((result.knowledge?.missing_knowledge as unknown[]) ?? [])} />
      <ListBlock title="Limitations" items={result.limitations} />
      <ListBlock title="Next Actions" items={result.next_actions} />

      {result.domain_search && (
        <div className="space-y-3 rounded-md border border-indigo-200 bg-indigo-50 p-3">
          <h3 className="text-sm font-semibold text-indigo-950">Learned Domain Sources</h3>
          <div className="grid gap-2 sm:grid-cols-3">
            <Field label="Action" value={titleCase(result.domain_search.action ?? "domain_search")} />
            <Field label="Domain" value={result.domain_search.domain || "All learned domains"} />
            <Field label="Results" value={String(result.domain_search.results_count ?? domainResults.length ?? learnedDomains.length)} />
          </div>
          {domainResults.length > 0 && (
            <div className="grid gap-2">
              {domainResults.map((source, index) => (
                <div key={`${source.url ?? source.title ?? "source"}_${index}`} className="rounded-md border border-indigo-100 bg-white px-3 py-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="break-words text-sm font-semibold text-slate-950">{source.title || source.url || source.domain || "Learned source"}</p>
                    {source.domain && <Pill tone="blue">{source.domain}</Pill>}
                    {typeof source.score === "number" && <Pill>{`score ${source.score}`}</Pill>}
                  </div>
                  {source.url && <p className="mt-1 break-words text-xs font-semibold text-indigo-700">{source.url}</p>}
                  {source.snippet && <p className="mt-2 text-sm leading-6 text-slate-700">{source.snippet}</p>}
                </div>
              ))}
            </div>
          )}
          <ListBlock title="Learned Domains" items={learnedDomains.map((item) => `${item.domain ?? "unknown"} (${item.sources_count ?? 0} saved source chunks)`)} />
          <ListBlock title="Missing Knowledge" items={result.domain_search.missing_knowledge} />
        </div>
      )}

      {result.security && (
        <div className="space-y-2 rounded-md border border-emerald-200 bg-emerald-50 p-3">
          <h3 className="text-sm font-semibold text-emerald-950">Security Status</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            <Field label="Monitor" value={String(result.security.monitor_enabled ?? false)} />
            <Field label="Rate Limiter" value={String(result.security.rate_limiter_enabled ?? false)} />
            <Field label="Events" value={String(result.security.events_count ?? 0)} />
            <Field label="Highest" value={String(result.security.highest_severity ?? "low")} />
          </div>
          <ListBlock title="Recent High Severity" items={(result.security.recent_high_severity as unknown[]) ?? []} />
          <ListBlock title="Top Patterns" items={(result.security.top_patterns as unknown[]) ?? []} />
          <ListBlock title="Recommended Defensive Actions" items={(result.security.recommendations as unknown[]) ?? []} />
          <ListBlock title="Hardening Summary" items={Object.entries((result.security.hardening as AnyRecord) ?? {}).flatMap(([key, value]) => [`${titleCase(key)}: ${Array.isArray(value) ? value.slice(0, 2).join("; ") : String(value)}`])} />
          <p className="text-sm font-semibold text-emerald-900">{String(result.security.disclaimer ?? "IP/location data is approximate and does not identify a person.")}</p>
        </div>
      )}

      {result.knowledge && (
        <div className="space-y-2 rounded-md border border-sky-200 bg-sky-50 p-3">
          <h3 className="text-sm font-semibold text-sky-950">Knowledge</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            <Field label="Action" value={String(result.knowledge.action ?? "used")} />
            <Field label="Confidence" value={titleCase(String(result.knowledge.confidence ?? result.confidence ?? "low"))} />
          </div>
          <ListBlock title="Source Titles" items={(result.knowledge.sources_used as unknown[]) ?? result.knowledge_sources_used ?? []} />
          <ListBlock title="Key Points" items={(result.knowledge.key_points as unknown[]) ?? []} />
          <ListBlock title="Missing Knowledge" items={(result.knowledge.missing_knowledge as unknown[]) ?? []} />
          <JsonBlock value={result.knowledge} />
        </div>
      )}

      {prompt && (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Codex Prompt</h3>
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(prompt)}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100"
            >
              Copy
            </button>
          </div>
          <pre className="max-h-80 overflow-auto rounded-md border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-800">
            {prompt}
          </pre>
        </div>
      )}
    </div>
  );
}

function StatusPanel({ title, value, fields }: { title: string; value: unknown; fields?: Array<[string, ReactNode]> }) {
  return (
    <Panel title={title}>
      {fields?.length ? (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {fields.map(([label, fieldValue]) => (
            <Field key={label} label={label} value={fieldValue} />
          ))}
        </div>
      ) : null}
      <JsonBlock value={value} />
    </Panel>
  );
}

export default function Home() {
  const [thread, setThread] = useState<ThreadItem[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Builder Core OS is ready in foundation mode.",
    },
  ]);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("auto");
  const [saveToMemory, setSaveToMemory] = useState(true);
  const [sending, setSending] = useState(false);
  const [statuses, setStatuses] = useState<StatusBundle>({});
  const [statusError, setStatusError] = useState("");
  const [adminKey, setAdminKey] = useState("");
  const [adminDraft, setAdminDraft] = useState("");
  const [adminMessage, setAdminMessage] = useState("");
  const [urlToLearn, setUrlToLearn] = useState("");
  const [crawlUrl, setCrawlUrl] = useState("");
  const [accountQuery, setAccountQuery] = useState("");
  const [knowledgeTitle, setKnowledgeTitle] = useState("");
  const [knowledgeContent, setKnowledgeContent] = useState("");
  const [knowledgeCategory, setKnowledgeCategory] = useState("general");
  const [knowledgeTags, setKnowledgeTags] = useState("");
  const [knowledgeQuery, setKnowledgeQuery] = useState("");

  const latestAssistant = useMemo(() => [...thread].reverse().find((item) => item.role === "assistant" && item.result), [thread]);

  async function protectedJson<T>(path: string, keyOverride?: string): Promise<T | { error: string }> {
    const key = keyOverride ?? adminKey;
    if (!key) return { error: "Admin key required for this panel. Add your admin key in Admin Access." };
    try {
      return await requestJson<T>(path, undefined, key);
    } catch (error) {
      return { error: friendlyProtectedMessage(error) };
    }
  }

  async function refreshStatuses(keyOverride?: string) {
    setStatusError("");
    try {
      const [
        system,
        os,
        platform,
        roles,
        security,
        search,
        storage,
        model,
        knowledge,
        roadmap,
        roadmapNext,
      ] = await Promise.all([
        requestJson<AnyRecord>("/system/status"),
        requestJson<AnyRecord>("/os/status"),
        requestJson<AnyRecord>("/platform/status"),
        requestJson<AnyRecord>("/agents/roles"),
        requestJson<AnyRecord>("/security/status"),
        requestJson<AnyRecord>("/search/status"),
        requestJson<AnyRecord>("/storage/status"),
        requestJson<AnyRecord>("/assistant/model-status"),
        requestJson<AnyRecord>("/knowledge/status"),
        requestJson<AnyRecord>("/roadmap"),
        requestJson<AnyRecord>("/roadmap/next"),
      ]);
      const [
        tasks,
        approvals,
        account,
        connectors,
        securityReport,
        hardening,
        tools,
        memory,
        learning,
        selfImprovement,
      ] = await Promise.all([
        protectedJson<AnyRecord>("/agents/tasks", keyOverride),
        protectedJson<AnyRecord>("/approvals", keyOverride),
        protectedJson<AnyRecord>("/account-agent/status", keyOverride),
        protectedJson<AnyRecord>("/connectors", keyOverride),
        protectedJson<AnyRecord>("/security/report", keyOverride),
        protectedJson<AnyRecord>("/security/hardening", keyOverride),
        protectedJson<AnyRecord>("/tools", keyOverride),
        protectedJson<AnyRecord>("/memory", keyOverride),
        protectedJson<AnyRecord>("/learning", keyOverride),
        protectedJson<AnyRecord>("/self-improvement", keyOverride),
      ]);
      const protectedErrors: Record<string, string> = {};
      Object.entries({ tasks, approvals, account, connectors, securityReport, hardening, tools, memory, learning, selfImprovement }).forEach(([key, value]) => {
        if (typeof value === "object" && value !== null && "error" in value) protectedErrors[key] = String((value as AnyRecord).error);
      });
      setStatuses({ system, os, platform, roles, tasks, approvals, account, connectors, security, securityReport, hardening, tools, search, storage, model, memory, learning, selfImprovement, knowledge, roadmap, roadmapNext, protectedErrors });
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : "Status refresh failed");
    }
  }

  useEffect(() => {
    const stored = window.localStorage.getItem("builder_core_admin_key") ?? "";
    setAdminKey(stored);
    setAdminDraft(stored);
    refreshStatuses(stored);
  }, []);

  function saveAdminKey() {
    const value = adminDraft.trim();
    window.localStorage.setItem("builder_core_admin_key", value);
    setAdminKey(value);
    setAdminMessage(value ? "Admin key saved in this browser only." : "Admin key cleared.");
    refreshStatuses(value);
  }

  function clearAdminKey() {
    window.localStorage.removeItem("builder_core_admin_key");
    setAdminKey("");
    setAdminDraft("");
    setAdminMessage("Admin key cleared.");
    refreshStatuses("");
  }

  async function submitCommand(event: FormEvent) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || sending) return;
    const userItem: ThreadItem = { id: createId("user"), role: "user", content: trimmed };
    setThread((current) => [...current, userItem]);
    setMessage("");
    setSending(true);
    try {
      const result = await requestJson<CommandResponse>("/command", {
        method: "POST",
        body: JSON.stringify({ message: trimmed, mode, save_to_memory: saveToMemory }),
      });
      setThread((current) => [
        ...current,
        { id: createId("assistant"), role: "assistant", content: result.reply ?? "Builder Core OS returned a response.", result },
      ]);
      refreshStatuses();
    } catch (error) {
      setThread((current) => [
        ...current,
        { id: createId("assistant"), role: "assistant", content: "Request failed.", error: error instanceof Error ? error.message : "Unknown error" },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function learnUrl(event: FormEvent) {
    event.preventDefault();
    if (!urlToLearn.trim()) return;
    const result = await requestJson<AnyRecord>("/agent/learn-url", {
      method: "POST",
      body: JSON.stringify({ url: urlToLearn.trim(), topic: "manual frontend learn URL" }),
    });
    setThread((current) => [
      ...current,
      { id: createId("assistant"), role: "assistant", content: `URL learning completed: learned=${String(result.learned)} chunks=${String(result.chunks_created ?? 0)}` },
    ]);
    setUrlToLearn("");
    refreshStatuses();
  }

  async function createCrawlPlan(event: FormEvent) {
    event.preventDefault();
    if (!crawlUrl.trim()) return;
    const result = await requestJson<AnyRecord>("/agent/crawl-plan", {
      method: "POST",
      body: JSON.stringify({ seed_urls: [crawlUrl.trim()], topic: "manual frontend crawl plan", max_pages: 5 }),
    });
    setThread((current) => [
      ...current,
      { id: createId("assistant"), role: "assistant", content: `Crawler plan created: ${String(result.plan_id ?? result.id ?? "planned")}` },
    ]);
    setCrawlUrl("");
    refreshStatuses();
  }

  async function searchAccountAgent(event: FormEvent) {
    event.preventDefault();
    if (!accountQuery.trim()) return;
    if (!adminKey) {
      setStatusError("Admin key required for this panel. Add your admin key in Admin Access.");
      return;
    }
    try {
      const result = await requestJson<AnyRecord>(
        "/account-agent/search",
        {
          method: "POST",
          body: JSON.stringify({ query: accountQuery.trim(), sources: ["firestore_memory", "private_search"], save_to_memory: saveToMemory }),
        },
        adminKey,
      );
      setThread((current) => [
        ...current,
        { id: createId("assistant"), role: "assistant", content: String(result.summary ?? "Account-agent search completed.") },
      ]);
      setAccountQuery("");
      refreshStatuses(adminKey);
    } catch (error) {
      setStatusError(friendlyProtectedMessage(error));
    }
  }

  async function addKnowledge(event: FormEvent) {
    event.preventDefault();
    if (!knowledgeContent.trim()) return;
    const result = await requestJson<AnyRecord>("/knowledge/add", {
      method: "POST",
      body: JSON.stringify({
        title: knowledgeTitle.trim() || "Manual knowledge note",
        content: knowledgeContent.trim(),
        source_type: "manual_note",
        category: knowledgeCategory,
        tags: knowledgeTags.split(",").map((tag) => tag.trim()).filter(Boolean),
      }),
    });
    setThread((current) => [
      ...current,
      { id: createId("assistant"), role: "assistant", content: `Knowledge saved: ${String(result.knowledge_id ?? "saved")} chunks=${String(result.chunks_created ?? 0)}` },
    ]);
    setKnowledgeTitle("");
    setKnowledgeContent("");
    setKnowledgeTags("");
    refreshStatuses();
  }

  async function searchKnowledge(event: FormEvent) {
    event.preventDefault();
    if (!knowledgeQuery.trim()) return;
    const result = await requestJson<AnyRecord>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query: knowledgeQuery.trim(), limit: 8 }),
    });
    setStatuses((current) => ({ ...current, knowledgeSearch: result }));
  }

  async function seedKnowledge() {
    if (!adminKey) {
      setStatusError("Admin key required for this panel. Add your admin key in Admin Access.");
      return;
    }
    try {
      const result = await requestJson<AnyRecord>("/knowledge/seed", { method: "POST", body: JSON.stringify({}) }, adminKey);
      setThread((current) => [
        ...current,
        { id: createId("assistant"), role: "assistant", content: String(result.message ?? "Knowledge seed complete.") },
      ]);
      refreshStatuses(adminKey);
    } catch (error) {
      setStatusError(friendlyProtectedMessage(error));
    }
  }

  async function scanProjectKnowledge() {
    if (!adminKey) {
      setStatusError("Admin key required for this panel. Add your admin key in Admin Access.");
      return;
    }
    try {
      const result = await requestJson<AnyRecord>("/knowledge/scan-project", { method: "POST", body: JSON.stringify({}) }, adminKey);
      setThread((current) => [
        ...current,
        { id: createId("assistant"), role: "assistant", content: `Project scan complete: ${String(result.knowledge_entries_created ?? 0)} entries.` },
      ]);
      refreshStatuses(adminKey);
    } catch (error) {
      setStatusError(friendlyProtectedMessage(error));
    }
  }

  const system = statuses.system ?? {};
  const os = statuses.os ?? {};
  const platform = statuses.platform ?? {};
  const security = statuses.security ?? {};
  const account = statuses.account ?? {};

  return (
    <main className="min-h-screen bg-stone-50 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="border-b border-slate-200 pb-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold text-emerald-700">Foundation</p>
              <h1 className="text-3xl font-bold tracking-normal text-slate-950 sm:text-4xl">Builder Core OS</h1>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <Field label="Storage" value={String(system.storage_mode ?? os.storage ?? "unknown")} />
              <Field label="Brain" value={String(system.active_brain ?? "local_rule_based")} />
              <Field label="Security Events" value={String(security.events_count ?? system.recent_security_event_count ?? 0)} />
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-h-[620px] rounded-md border border-slate-200 bg-white">
            <div className="border-b border-slate-200 px-4 py-3">
              <div className="flex flex-wrap gap-2">
                <Pill tone={os.external_ai_required === false ? "green" : "amber"}>outside AI optional</Pill>
                <Pill tone={os.external_search_api_required === false ? "green" : "amber"}>no search API required</Pill>
                <Pill tone="blue">{titleCase(String(platform.runtime_mode ?? "unknown"))}</Pill>
                <Pill tone="amber">human approval gates</Pill>
              </div>
            </div>

            <div className="h-[520px] space-y-4 overflow-y-auto px-4 py-4">
              {thread.map((item) => (
                <div key={item.id} className={item.role === "user" ? "ml-auto max-w-3xl" : "mr-auto max-w-4xl"}>
                  <div className={`rounded-md border px-4 py-3 ${item.role === "user" ? "border-sky-200 bg-sky-50" : "border-slate-200 bg-slate-50"}`}>
                    <div className="mb-2 text-xs font-semibold uppercase tracking-normal text-slate-500">{item.role}</div>
                    <p className="whitespace-pre-wrap text-sm leading-6 text-slate-900">{item.content}</p>
                    {item.error && <p className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{item.error}</p>}
                    {item.result && <MessageResult result={item.result} />}
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={submitCommand} className="border-t border-slate-200 p-4">
              <div className="grid gap-3 lg:grid-cols-[160px_1fr_auto]">
                <select
                  value={mode}
                  onChange={(event) => setMode(event.target.value)}
                  className="rounded-md border border-slate-300 bg-white px-3 py-3 text-sm font-semibold text-slate-900 outline-none focus:border-sky-500"
                >
                  {MODE_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {titleCase(option)}
                    </option>
                  ))}
                </select>
                <input
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Message Builder Core OS"
                  className="min-w-0 rounded-md border border-slate-300 px-3 py-3 text-sm outline-none focus:border-sky-500"
                />
                <button
                  type="submit"
                  disabled={sending}
                  className="rounded-md bg-slate-950 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {sending ? "Sending" : "Send"}
                </button>
              </div>
              <label className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
                <input type="checkbox" checked={saveToMemory} onChange={(event) => setSaveToMemory(event.target.checked)} />
                Save to memory
              </label>
            </form>
          </div>

          <aside className="space-y-3">
            <div className="rounded-md border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-900">Latest Response</h2>
              <div className="mt-3 space-y-2">
                <Field label="Role" value={titleCase(latestAssistant?.result?.selected_agent_role ?? "none")} />
                <Field label="Workflow" value={titleCase(latestAssistant?.result?.workflow ?? "none")} />
                <Field label="Memory" value={String(latestAssistant?.result?.memory_saved ?? false)} />
              </div>
            </div>

            <Panel title="Admin Access">
              <div className="space-y-3">
                <input
                  value={adminDraft}
                  onChange={(event) => setAdminDraft(event.target.value)}
                  type="password"
                  placeholder="X-Admin-Key"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <div className="flex gap-2">
                  <button type="button" onClick={saveAdminKey} className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">
                    Save key
                  </button>
                  <button type="button" onClick={clearAdminKey} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800">
                    Clear
                  </button>
                </div>
                <p className="text-sm text-slate-600">{adminMessage || (adminKey ? "Admin key is stored only in this browser." : "Admin key required for protected dashboard panels.")}</p>
              </div>
            </Panel>

            <Panel title="Learn URL">
              <form onSubmit={learnUrl} className="flex gap-2">
                <input value={urlToLearn} onChange={(event) => setUrlToLearn(event.target.value)} placeholder="https://example.com" className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
                <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">Learn</button>
              </form>
            </Panel>

            <Panel title="Crawler Plan">
              <form onSubmit={createCrawlPlan} className="flex gap-2">
                <input value={crawlUrl} onChange={(event) => setCrawlUrl(event.target.value)} placeholder="https://example.com" className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
                <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">Plan</button>
              </form>
            </Panel>

            <Panel title="Knowledge Base">
              <div className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-2">
                  <Field label="Entries" value={String(statuses.knowledge?.total_entries ?? 0)} />
                  <Field label="Storage" value={String(statuses.knowledge?.storage_used ?? "unknown")} />
                  <Field label="Search Docs" value={String(statuses.knowledge?.private_search_documents ?? 0)} />
                  <Field label="Search Chunks" value={String(statuses.knowledge?.private_search_chunks ?? 0)} />
                </div>
                <form onSubmit={addKnowledge} className="space-y-2">
                  <input value={knowledgeTitle} onChange={(event) => setKnowledgeTitle(event.target.value)} placeholder="Title" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  <select value={knowledgeCategory} onChange={(event) => setKnowledgeCategory(event.target.value)} className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">
                    {["general", "code", "business", "market", "law", "medical_info", "security", "teaching", "exam", "trucking", "project", "ai_os"].map((category) => (
                      <option key={category} value={category}>{titleCase(category)}</option>
                    ))}
                  </select>
                  <input value={knowledgeTags} onChange={(event) => setKnowledgeTags(event.target.value)} placeholder="tags, comma, separated" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  <textarea value={knowledgeContent} onChange={(event) => setKnowledgeContent(event.target.value)} placeholder="Add a note Builder Core can remember" className="min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">Add note</button>
                </form>
                <form onSubmit={searchKnowledge} className="flex gap-2">
                  <input value={knowledgeQuery} onChange={(event) => setKnowledgeQuery(event.target.value)} placeholder="Search knowledge" className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
                  <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">Search</button>
                </form>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={seedKnowledge} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800">Seed packs</button>
                  <button type="button" onClick={scanProjectKnowledge} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800">Scan project</button>
                </div>
                {!adminKey && <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-800">Admin key required for seed packs and project scan.</p>}
                <ListBlock title="Knowledge Search Results" items={(statuses.knowledgeSearch?.results as unknown[]) ?? []} />
              </div>
            </Panel>

            <Panel title="Account Agent Search">
              <form onSubmit={searchAccountAgent} className="flex gap-2">
                <input value={accountQuery} onChange={(event) => setAccountQuery(event.target.value)} placeholder="Search memory" className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
                <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white">Search</button>
              </form>
              <ListBlock title="Connected Sources" items={(account.connected_sources as unknown[]) ?? []} />
            </Panel>
          </aside>
        </section>

        {statusError && <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{statusError}</div>}
        {Object.values(statuses.protectedErrors ?? {}).length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
            {Object.values(statuses.protectedErrors ?? {})[0]}
          </div>
        )}

        <section className="grid gap-3">
          <StatusPanel title="OS Status" value={statuses.os} fields={[["System", String(os.system ?? "Builder Core OS")], ["Stage", String(os.version_stage ?? "foundation")], ["Storage", String(os.storage ?? "unknown")]]} />
          <StatusPanel title="Platform Status" value={statuses.platform} fields={[["Platform", String(platform.platform ?? "unknown")], ["Runtime", String(platform.runtime_mode ?? "unknown")], ["Python", String(platform.python_version ?? "unknown")]]} />
          <StatusPanel title="Agent Roles" value={statuses.roles} fields={[["Count", String((statuses.roles?.count as number) ?? 0)]]} />
          <StatusPanel title="Agent Tasks" value={statuses.tasks} />
          <StatusPanel title="Pending Approvals" value={statuses.approvals} fields={[["Pending", String(statuses.approvals?.pending_count ?? 0)]]} />
          <StatusPanel title="Account Agent / Connectors" value={{ account: statuses.account, connectors: statuses.connectors }} />
          <StatusPanel title="Security Center" value={{ status: statuses.security, report: statuses.securityReport, hardening: statuses.hardening }} fields={[["Events", String(security.events_count ?? 0)], ["Rate Limiter", String(security.rate_limiter_enabled ?? false)], ["Highest", String(statuses.securityReport?.highest_severity ?? "low")]]} />
          <StatusPanel title="Knowledge Base" value={{ status: statuses.knowledge, search: statuses.knowledgeSearch }} fields={[["Entries", String(statuses.knowledge?.total_entries ?? 0)], ["Storage", String(statuses.knowledge?.storage_used ?? "unknown")], ["Seeded", String((statuses.knowledge?.knowledge_seed_status as AnyRecord | undefined)?.seeded ?? false)]]} />
          <StatusPanel title="Roadmap" value={{ roadmap: statuses.roadmap, next: statuses.roadmapNext }} fields={[["Next", String((statuses.roadmapNext?.item as AnyRecord | undefined)?.title ?? "unknown")], ["Status", String((statuses.roadmapNext?.item as AnyRecord | undefined)?.status ?? "unknown")]]} />
          <StatusPanel title="Tool Registry" value={statuses.tools} />
          <StatusPanel title="Private Search" value={statuses.search} />
          <StatusPanel title="Storage Status" value={statuses.storage} />
          <StatusPanel title="Model Status" value={statuses.model} />
          <StatusPanel title="Memory" value={statuses.memory} />
          <StatusPanel title="Learning" value={statuses.learning} />
          <StatusPanel title="Self-Improvement" value={statuses.selfImprovement} />
        </section>
      </div>
    </main>
  );
}
