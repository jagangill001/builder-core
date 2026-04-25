"use client";

import { useEffect, useState } from "react";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "https://builder-core-599596796788.us-central1.run.app"
).replace(/\/$/, "");

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

export default function Home() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState("No request submitted yet.");
  const [status, setStatus] = useState("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectFiles, setProjectFiles] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState("Default Project");
  const [newProjectName, setNewProjectName] = useState("");
  const [runInfo, setRunInfo] = useState<RunInfo | null>(null);

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
    <main className="min-h-screen p-8 bg-gray-50 text-black">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Builder Core Dashboard</h1>
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

        <div className="bg-white border rounded-2xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Projects</h2>

          <div className="flex flex-col md:flex-row gap-3 mb-4">
            <input
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="New project name"
              className="border rounded-xl px-4 py-3 flex-1"
            />
            <button
              type="button"
              onClick={handleCreateProject}
              className="px-5 py-3 rounded-xl bg-black text-white"
            >
              Create Project
            </button>
          </div>

          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="border rounded-xl px-4 py-3 w-full md:w-80"
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

        <div className="bg-white border rounded-2xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">New Request</h2>

          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            placeholder="Examples:
Create a notes page with add, edit, and delete.
Build a vendor dashboard for comparing supplier quotes.
Add login page with email and password.
Create a dashboard with summary cards."
            className="w-full h-48 border rounded-xl p-4 mb-4"
          />

          <button
            type="button"
            onClick={handleSubmit}
            className="px-5 py-3 rounded-xl bg-black text-white"
          >
            Submit Request
          </button>
        </div>

        <div className="bg-white border rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-xl font-semibold">Latest Result</h2>
            {status && (
              <span className="text-sm px-3 py-1 rounded-full border">
                {status}
              </span>
            )}
          </div>
          <pre className="whitespace-pre-wrap text-sm">{result}</pre>
        </div>

        <div className="bg-white border rounded-2xl p-6 mb-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Run Generated App</h2>

          {!runInfo ? (
            <p className="text-gray-500">No run info available.</p>
          ) : (
            <div className="space-y-3">
              <p><strong>Project:</strong> {runInfo.project_name}</p>
              <p><strong>Path:</strong> {runInfo.project_path}</p>
              <p><strong>Run Script:</strong> {runInfo.run_script}</p>
              <p className="text-sm text-gray-600">{runInfo.url_hint}</p>

              <div>
                <p className="font-semibold mb-2">Commands:</p>
                <pre className="whitespace-pre-wrap text-sm bg-gray-50 border rounded-xl p-4">
{runInfo.commands.join("\n")}
                </pre>
              </div>
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white border rounded-2xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">
              Request History for {selectedProject}
            </h2>

            {history.length === 0 ? (
              <p className="text-gray-500">No requests yet.</p>
            ) : (
              <div className="space-y-4">
                {history.map((item, index) => (
                  <div key={index} className="border rounded-xl p-4">
                    <p className="font-semibold mb-2">{item.instruction}</p>
                    <p className="text-sm mb-1">Project: {item.project_name}</p>
                    <p className="text-sm mb-2">Status: {item.status}</p>

                    <ul className="list-disc pl-5 text-sm mb-3">
                      {item.plan.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ul>

                    {item.created_files && item.created_files.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold mb-1">Created Files:</p>
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

          <div className="bg-white border rounded-2xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">
              Project Files for {selectedProject}
            </h2>

            {projectFiles.length === 0 ? (
              <p className="text-gray-500">No files yet.</p>
            ) : (
              <ul className="list-disc pl-5 text-sm space-y-1">
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
