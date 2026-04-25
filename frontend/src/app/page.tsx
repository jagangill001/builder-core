"use client";

import { useEffect, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

const EMPTY_PROMPT_MESSAGE = "Generated Codex prompt will appear here.";

type HistoryItem = {
  instruction: string;
  status: string;
  project_name: string;
  plan: string[];
  created_files?: string[];
};

type ProjectItem = {
  id: number;
  name: string;
};

type RunInfo = {
  project_name: string;
  project_path: string;
  run_script: string;
  commands: string[];
  url_hint: string;
};

function buildCodexPrompt(instruction: string, projectName: string) {
  return [
    "Repo: jagangill001/builder-core",
    `Selected project: ${projectName}`,
    "",
    "Goal:",
    instruction,
    "",
    "Safety rules:",
    "- Inspect the repo before editing.",
    "- Do not delete working features.",
    "- Keep the implementation beginner-friendly.",
    "- Commit directly to main.",
    "- Explain every file changed.",
    "- Provide testing steps.",
    "- Prefer original repo-specific code and avoid copying external snippets.",
    "",
    "Do not break:",
    "- Existing frontend/backend connection",
    "- Current request submission flow",
    "- Backend health indicator",
    "",
    "Return:",
    "1. Files changed",
    "2. Short explanation of changes",
    "3. Testing steps"
  ].join("\n");
}

export default function Home() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState("No request submitted yet.");
  const [status, setStatus] = useState("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [commandCenterInput, setCommandCenterInput] = useState("");
  const [codexPrompt, setCodexPrompt] = useState(EMPTY_PROMPT_MESSAGE);
  const [copyMessage, setCopyMessage] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectFiles, setProjectFiles] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState("Default Project");
  const [newProjectName, setNewProjectName] = useState("");
  const [runInfo, setRunInfo] = useState<RunInfo | null>(null);

  const canCopyPrompt =
    codexPrompt !== EMPTY_PROMPT_MESSAGE &&
    codexPrompt !== "Add an instruction above to generate a Codex prompt.";

  async function checkBackendStatus() {
    try {
      const response = await fetch(`${API_BASE}/system/status`);

      if (!response.ok) {
        throw new Error("Backend status check failed");
      }

      setBackendStatus("online");
    } catch {
      setBackendStatus("offline");
    }
  }

  async function loadProjects() {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json();
      const items = data.items || [];
      setProjects(items);

      if (items.length > 0 && !items.find((p: ProjectItem) => p.name === selectedProject)) {
        setSelectedProject(items[0].name);
      }
    } catch {
      console.log("Could not load projects");
    }
  }

  async function loadHistory(projectName?: string) {
    try {
      const url = projectName
        ? `${API_BASE}/history?project_name=${encodeURIComponent(projectName)}`
        : `${API_BASE}/history`;

      const response = await fetch(url);
      const data = await response.json();
      setHistory(data.items || []);
    } catch {
      console.log("Could not load history");
    }
  }

  async function loadProjectFiles(projectName: string) {
    try {
      const response = await fetch(`${API_BASE}/project-files?project_name=${encodeURIComponent(projectName)}`);
      const data = await response.json();
      setProjectFiles(data.items || []);
    } catch {
      console.log("Could not load project files");
    }
  }

  async function loadRunInfo(projectName: string) {
    try {
      const response = await fetch(`${API_BASE}/run-info?project_name=${encodeURIComponent(projectName)}`);
      const data = await response.json();
      setRunInfo(data);
    } catch {
      console.log("Could not load run info");
    }
  }

  useEffect(() => {
    checkBackendStatus();
    loadProjects();
    loadHistory(selectedProject);
    loadProjectFiles(selectedProject);
    loadRunInfo(selectedProject);
  }, []);

  useEffect(() => {
    loadHistory(selectedProject);
    loadProjectFiles(selectedProject);
    loadRunInfo(selectedProject);
  }, [selectedProject]);

  function handleGeneratePrompt() {
    const trimmedInstruction = commandCenterInput.trim();

    if (!trimmedInstruction) {
      setCodexPrompt("Add an instruction above to generate a Codex prompt.");
      setCopyMessage("");
      return;
    }

    setCodexPrompt(buildCodexPrompt(trimmedInstruction, selectedProject));
    setCopyMessage("");
  }

  async function handleCopyPrompt() {
    if (!canCopyPrompt) {
      return;
    }

    try {
      await navigator.clipboard.writeText(codexPrompt);
      setCopyMessage("Prompt copied.");
    } catch {
      setCopyMessage("Copy failed. Select the prompt and copy it manually.");
    }
  }

  async function handleCreateProject() {
    if (!newProjectName.trim()) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: newProjectName
        })
      });

      const data = await response.json();

      if (data.ok && data.project) {
        setSelectedProject(data.project.name);
        setNewProjectName("");
        await loadProjects();
        await loadHistory(data.project.name);
        await loadProjectFiles(data.project.name);
        await loadRunInfo(data.project.name);
      }
    } catch {
      console.log("Could not create project");
    }
  }

  async function handleSubmit() {
    if (!request.trim()) {
      setResult("Please enter an instruction.");
      setStatus("error");
      return;
    }

    setResult("Sending request to backend...");
    setStatus("loading");

    try {
      const response = await fetch(`${API_BASE}/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          instruction: request,
          project_name: selectedProject
        })
      });

      const data = await response.json();

      if (!data.ok) {
        setResult(data.message || "Something went wrong.");
        setStatus("error");
        return;
      }

      setStatus(data.status);

      const filesText =
        data.created_files && data.created_files.length > 0
          ? "\n\nCreated Files:\n- " + data.created_files.join("\n- ")
          : "\n\nCreated Files:\n- No files generated for this request.";

      setResult(
        "Message: " + data.message +
        "\n\nProject: " + data.project_name +
        "\nModule Key: " + data.module_key +
        "\nTitle: " + data.title +
        "\nRoute Path: " + data.route_path +
        "\n\nInstruction: " + data.instruction +
        "\n\nPlan:\n- " + data.plan.join("\n- ") +
        filesText
      );

      setRequest("");
      loadHistory(selectedProject);
      loadProjectFiles(selectedProject);
      loadRunInfo(selectedProject);
    } catch {
      setResult("Could not connect to backend.");
      setStatus("error");
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-6 text-black sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-2 text-3xl font-bold sm:text-4xl">Builder Core Dashboard</h1>
        <p className="mb-3 text-gray-600">
          Builder Core v5 with generated app shells and run instructions.
        </p>
        <p
          className={
            backendStatus === "online"
              ? "mb-6 text-sm font-medium text-green-600"
              : backendStatus === "offline"
                ? "mb-6 text-sm font-medium text-red-600"
                : "mb-6 text-sm font-medium text-gray-500"
          }
        >
          {backendStatus === "checking" && "Backend: Checking..."}
          {backendStatus === "online" && "Backend: Online"}
          {backendStatus === "offline" && "Backend: Offline"}
        </p>

        <div className="mb-6 grid gap-6 lg:grid-cols-[2fr,1fr]">
          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-2 text-xl font-semibold">Command Center</h2>
            <p className="mb-4 text-sm text-gray-600">
              Describe what you want to build, fix, or upgrade, then generate a Codex-ready prompt you can send from ChatGPT.
            </p>

            <textarea
              value={commandCenterInput}
              onChange={(e) => setCommandCenterInput(e.target.value)}
              placeholder="Tell Builder Core what to build, fix, or upgrade..."
              className="mb-4 h-36 w-full rounded-xl border p-4"
            />

            <div className="mb-4 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={handleGeneratePrompt}
                className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
              >
                Generate Codex Prompt
              </button>
              <button
                type="button"
                onClick={handleCopyPrompt}
                disabled={!canCopyPrompt}
                className={
                  canCopyPrompt
                    ? "w-full rounded-xl border border-black px-5 py-3 text-black sm:w-auto"
                    : "w-full rounded-xl border border-gray-200 px-5 py-3 text-gray-400 sm:w-auto"
                }
              >
                Copy Prompt
              </button>
            </div>

            {copyMessage && (
              <p className="mb-3 text-sm text-gray-600">{copyMessage}</p>
            )}

            <p className="mb-2 text-sm font-semibold text-gray-700">Generated Codex Prompt</p>
            <textarea
              value={codexPrompt}
              readOnly
              className="h-72 w-full rounded-xl border bg-gray-50 p-4 text-sm"
            />
          </div>

          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-3 text-xl font-semibold">Automation Status</h2>
            <div className="mb-4 inline-flex rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700">
              Manual mode active
            </div>
            <p className="mb-3 text-sm text-gray-700">
              Future version will send tasks automatically.
            </p>
            <ul className="list-disc space-y-2 pl-5 text-sm text-gray-600">
              <li>No automatic repo modification without user confirmation.</li>
              <li>Authentication will be required before automation can act.</li>
              <li>Logs and transparent status updates will stay visible in the app.</li>
            </ul>
          </div>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">Projects</h2>

          <div className="mb-4 flex flex-col gap-3 md:flex-row">
            <input
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="New project name"
              className="flex-1 rounded-xl border px-4 py-3"
            />
            <button
              type="button"
              onClick={handleCreateProject}
              className="w-full rounded-xl bg-black px-5 py-3 text-white md:w-auto"
            >
              Create Project
            </button>
          </div>

          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="w-full rounded-xl border px-4 py-3 md:w-80"
          >
            {projects.length === 0 ? (
              <option>Default Project</option>
            ) : (
              projects.map((project) => (
                <option key={project.id} value={project.name}>
                  {project.name}
                </option>
              ))
            )}
          </select>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">New Request</h2>

          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="Examples:
Create a notes page with add, edit, and delete.
Build a vendor dashboard for comparing supplier quotes.
Add login page with email and password.
Create a dashboard with summary cards."
            className="mb-4 h-48 w-full rounded-xl border p-4"
          />

          <button
            type="button"
            onClick={handleSubmit}
            className="w-full rounded-xl bg-black px-5 py-3 text-white sm:w-auto"
          >
            Submit Request
          </button>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <div className="mb-3 flex items-center gap-3">
            <h2 className="text-xl font-semibold">Latest Result</h2>
            {status && (
              <span className="rounded-full border px-3 py-1 text-sm">
                {status}
              </span>
            )}
          </div>
          <pre className="whitespace-pre-wrap text-sm">{result}</pre>
        </div>

        <div className="mb-6 rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
          <h2 className="mb-4 text-xl font-semibold">Run Generated App</h2>

          {!runInfo ? (
            <p className="text-gray-500">No run info available.</p>
          ) : (
            <div className="space-y-3">
              <p><strong>Project:</strong> {runInfo.project_name}</p>
              <p><strong>Path:</strong> {runInfo.project_path}</p>
              <p><strong>Run Script:</strong> {runInfo.run_script}</p>
              <p className="text-sm text-gray-600">{runInfo.url_hint}</p>

              <div>
                <p className="mb-2 font-semibold">Commands:</p>
                <pre className="whitespace-pre-wrap rounded-xl border bg-gray-50 p-4 text-sm">
{runInfo.commands.join("\n")}
                </pre>
              </div>
            </div>
          )}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-4 text-xl font-semibold">
              Request History for {selectedProject}
            </h2>

            {history.length === 0 ? (
              <p className="text-gray-500">No requests yet.</p>
            ) : (
              <div className="space-y-4">
                {history.map((item, index) => (
                  <div key={index} className="rounded-xl border p-4">
                    <p className="mb-2 font-semibold">{item.instruction}</p>
                    <p className="mb-1 text-sm">Project: {item.project_name}</p>
                    <p className="mb-2 text-sm">Status: {item.status}</p>

                    <ul className="mb-3 list-disc pl-5 text-sm">
                      {item.plan.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ul>

                    {item.created_files && item.created_files.length > 0 && (
                      <div>
                        <p className="mb-1 text-sm font-semibold">Created Files:</p>
                        <ul className="list-disc pl-5 text-sm">
                          {item.created_files.map((file, fileIndex) => (
                            <li key={fileIndex}>{file}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-6">
            <h2 className="mb-4 text-xl font-semibold">
              Project Files for {selectedProject}
            </h2>

            {projectFiles.length === 0 ? (
              <p className="text-gray-500">No files yet.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {projectFiles.map((file, index) => (
                  <li key={index}>{file}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
