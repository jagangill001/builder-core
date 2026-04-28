import json
import os
from pathlib import Path
from typing import Any, Optional
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

app = FastAPI(title="Builder Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://builder-core-frontend-599596796788.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "builder_core.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

DEFAULT_GITHUB_OWNER = "jagangill001"
DEFAULT_GITHUB_REPO = "builder-core"
DEFAULT_GITHUB_BRANCH = "main"
DEFAULT_GITHUB_CHECKS_WORKFLOW = "Repo Checks"
DEFAULT_GITHUB_DEPLOY_WORKFLOW = "Deploy Cloud Run"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

    requests = relationship("BuildRequestRecord", back_populates="project", cascade="all, delete-orphan")

class BuildRequestRecord(Base):
    __tablename__ = "build_requests"

    id = Column(Integer, primary_key=True, index=True)
    instruction = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="requests")
    plans = relationship("PlanStep", back_populates="request", cascade="all, delete-orphan")
    files = relationship("CreatedFile", back_populates="request", cascade="all, delete-orphan")

class PlanStep(Base):
    __tablename__ = "plan_steps"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("build_requests.id"), nullable=False)
    step_text = Column(Text, nullable=False)

    request = relationship("BuildRequestRecord", back_populates="plans")

class CreatedFile(Base):
    __tablename__ = "created_files"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("build_requests.id"), nullable=False)
    file_path = Column(Text, nullable=False)

    request = relationship("BuildRequestRecord", back_populates="files")

Base.metadata.create_all(bind=engine)

class BuildRequest(BaseModel):
    instruction: str
    project_name: Optional[str] = "Default Project"

class ProjectCreate(BaseModel):
    name: str

def safe_name(value: str) -> str:
    return value.strip().replace(" ", "_").replace("-", "_").lower()

def project_root(project_name: str) -> Path:
    root = GENERATED_DIR / safe_name(project_name)
    root.mkdir(parents=True, exist_ok=True)
    return root

def app_root(project_name: str) -> Path:
    root = project_root(project_name) / "app"
    root.mkdir(parents=True, exist_ok=True)
    return root

def registry_path(project_name: str) -> Path:
    return project_root(project_name) / "module_registry.json"

def write_text_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)

def read_registry(project_name: str):
    path = registry_path(project_name)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"project_name": project_name, "modules": []}

def write_registry(project_name: str, data: dict):
    path = registry_path(project_name)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)

def ensure_project_scaffold(project_name: str):
    root = project_root(project_name)

    write_text_file(
        root / "README.txt",
        f"Generated project scaffold for {project_name}\n\nThis project was created by Builder Core v5.\n"
    )

    if not registry_path(project_name).exists():
        write_registry(project_name, {"project_name": project_name, "modules": []})

    write_text_file(
        root / "package.json",
        json.dumps(
            {
                "name": safe_name(project_name),
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start"
                },
                "dependencies": {
                    "next": "^16.2.2",
                    "react": "^19.0.0",
                    "react-dom": "^19.0.0"
                },
                "devDependencies": {
                    "@types/node": "^20.0.0",
                    "@types/react": "^19.0.0",
                    "@types/react-dom": "^19.0.0",
                    "typescript": "^5.0.0"
                }
            },
            indent=2
        )
    )

    write_text_file(
        root / "next.config.mjs",
        """const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
"""
    )

    write_text_file(
        root / "tsconfig.json",
        """{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": false,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
"""
    )

    write_text_file(
        root / "next-env.d.ts",
        """/// <reference types="next" />
/// <reference types="next/image-types/global" />

// This file was generated by Builder Core.
"""
    )

    write_text_file(
        root / "run_project.ps1",
        f"""cd "{root}"
npm install
npm run dev
"""
    )

def update_module_registry(project_name: str, module_key: str, route_path: str, title: str):
    data = read_registry(project_name)

    exists = any(m["module_key"] == module_key for m in data["modules"])
    if not exists:
        data["modules"].append({
            "module_key": module_key,
            "route_path": route_path,
            "title": title
        })

    return write_registry(project_name, data)

def build_project_shell(project_name: str):
    data = read_registry(project_name)
    modules = data.get("modules", [])
    app_dir = app_root(project_name)
    created = []

    nav_links = "\n".join([
        f'              <a href="{m["route_path"]}" style={{{{ color: "#2563eb", textDecoration: "none", fontWeight: 600 }}}}>{m["title"]}</a>'
        for m in modules
    ])

    module_cards = "\n".join([
        f"""          <div style={{{{ border: "1px solid #ddd", borderRadius: "12px", padding: "1rem" }}}}>
            <h2 style={{{{ marginTop: 0 }}}}>{m["title"]}</h2>
            <p>Route: {m["route_path"]}</p>
            <a href="{m["route_path"]}" style={{{{ color: "#2563eb", textDecoration: "none", fontWeight: 600 }}}}>Open module</a>
          </div>"""
        for m in modules
    ])

    layout_code = f"""export const metadata = {{
  title: "{project_name}",
  description: "Generated by Builder Core",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body style={{{{ margin: 0, fontFamily: "Arial, sans-serif", background: "#f8fafc", color: "#111827" }}}}>
        <header style={{{{ padding: "1rem 1.5rem", borderBottom: "1px solid #e5e7eb", background: "white" }}}}>
          <div style={{{{ maxWidth: "1100px", margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}}}>
            <div>
              <strong>{project_name}</strong>
            </div>
            <nav style={{{{ display: "flex", gap: "1rem", flexWrap: "wrap" }}}}>
{nav_links if nav_links else '              <span style={{ color: "#6b7280" }}>No modules yet</span>'}
            </nav>
          </div>
        </header>
        <div style={{{{ maxWidth: "1100px", margin: "0 auto", padding: "1.5rem" }}}}>
          {{children}}
        </div>
      </body>
    </html>
  );
}}
"""

    home_code = f"""export default function HomePage() {{
  return (
    <main>
      <section style={{{{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem", marginBottom: "1.5rem" }}}}>
        <h1 style={{{{ marginTop: 0, fontSize: "2rem" }}}}>{project_name}</h1>
        <p>This app shell was generated by Builder Core.</p>
      </section>

      <section style={{{{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}}}>
{module_cards if module_cards else '        <p>No modules generated yet.</p>'}
      </section>
    </main>
  );
}}
"""

    created.append(write_text_file(app_dir / "layout.tsx", layout_code))
    created.append(write_text_file(app_dir / "page.tsx", home_code))
    return created

def write_manifest(project_name: str, module_key: str, instruction: str, created_files: list[str], plan: list[str], route_path: str, title: str):
    manifest = {
        "project_name": project_name,
        "module_key": module_key,
        "title": title,
        "route_path": route_path,
        "instruction": instruction,
        "created_files": created_files,
        "plan": plan
    }
    manifest_path = project_root(project_name) / f"{module_key}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return str(manifest_path)

def generate_plan(instruction: str):
    text = instruction.lower()

    if "notes" in text:
        return [
            "Create notes page UI",
            "Add note form with title and content fields",
            "Create backend route for notes",
            "Add notes data model",
            "Add list, edit, and delete actions"
        ], "notes_page", "/notes", "Notes"

    if "vendor" in text:
        return [
            "Create vendor dashboard page",
            "Add vendor table with name, price, and contact fields",
            "Create backend route for vendor data",
            "Add vendor search and filter tools",
            "Add quote comparison section"
        ], "vendor_dashboard", "/vendors", "Vendors"

    if "login" in text or "auth" in text:
        return [
            "Create login page UI",
            "Add email and password form",
            "Create backend auth route",
            "Add user session handling",
            "Add protected dashboard access"
        ], "login_page", "/login", "Login"

    if "dashboard" in text:
        return [
            "Create dashboard layout",
            "Add summary cards",
            "Create backend route for dashboard data",
            "Add charts or tables",
            "Connect page to live data"
        ], "dashboard_page", "/dashboard", "Dashboard"

    return [
        "Understand requested feature",
        "Create frontend page",
        "Create backend route",
        "Add database model if needed",
        "Add testing and staging preview"
    ], "generic_module", "/module", "Module"

def build_notes_module(project_name: str):
    created = []
    root = app_root(project_name) / "notes"

    page_code = """export default function NotesPage() {
  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Notes Page</h1>
      <p>This file was generated by Builder Core.</p>

      <form style={{ display: "grid", gap: "1rem", maxWidth: "500px", marginTop: "1rem" }}>
        <input type="text" placeholder="Note title" style={{ padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: "10px" }} />
        <textarea placeholder="Write your note..." rows={6} style={{ padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: "10px" }} />
        <button type="submit" style={{ padding: "0.75rem", background: "black", color: "white", border: "none", borderRadius: "10px" }}>
          Save Note
        </button>
      </form>
    </main>
  );
}
"""

    api_text = """Suggested backend routes for notes:
GET /notes
POST /notes
PUT /notes/{id}
DELETE /notes/{id}
"""

    created.append(write_text_file(root / "page.tsx", page_code))
    created.append(write_text_file(root / "api.txt", api_text))
    return created

def build_vendor_module(project_name: str):
    created = []
    root = app_root(project_name) / "vendors"

    page_code = """export default function VendorDashboard() {
  const vendors = [
    { name: "Vendor A", price: "$1200", contact: "vendora@example.com" },
    { name: "Vendor B", price: "$980", contact: "vendorb@example.com" },
    { name: "Vendor C", price: "$1100", contact: "vendorc@example.com" }
  ];

  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Vendor Dashboard</h1>
      <p>Compare supplier quotes and contacts.</p>

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Vendor</th>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Price</th>
            <th style={{ border: "1px solid #ccc", padding: "0.75rem", textAlign: "left" }}>Contact</th>
          </tr>
        </thead>
        <tbody>
          {vendors.map((vendor) => (
            <tr key={vendor.name}>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.name}</td>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.price}</td>
              <td style={{ border: "1px solid #ccc", padding: "0.75rem" }}>{vendor.contact}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
"""

    api_text = """Suggested backend routes for vendors:
GET /vendors
POST /vendors
GET /vendors/{id}
PUT /vendors/{id}
DELETE /vendors/{id}
"""

    created.append(write_text_file(root / "page.tsx", page_code))
    created.append(write_text_file(root / "api.txt", api_text))
    return created

def build_login_module(project_name: str):
    created = []
    root = app_root(project_name) / "login"

    page_code = """export default function LoginPage() {
  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Login Page</h1>
      <p>Sign in to access the dashboard.</p>

      <form style={{ display: "grid", gap: "1rem", maxWidth: "400px", marginTop: "1rem" }}>
        <input type="email" placeholder="Email address" style={{ padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: "10px" }} />
        <input type="password" placeholder="Password" style={{ padding: "0.75rem", border: "1px solid #d1d5db", borderRadius: "10px" }} />
        <button type="submit" style={{ padding: "0.75rem", background: "black", color: "white", border: "none", borderRadius: "10px" }}>
          Login
        </button>
      </form>
    </main>
  );
}
"""

    api_text = """Suggested backend routes for auth:
POST /login
POST /logout
GET /session
"""

    created.append(write_text_file(root / "page.tsx", page_code))
    created.append(write_text_file(root / "api.txt", api_text))
    return created

def build_dashboard_module(project_name: str):
    created = []
    root = app_root(project_name) / "dashboard"

    page_code = """export default function DashboardPage() {
  const cards = [
    { title: "Users", value: "128" },
    { title: "Requests", value: "42" },
    { title: "Modules Built", value: "7" },
    { title: "System Status", value: "Healthy" }
  ];

  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Dashboard</h1>
      <p>System overview.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "1rem", marginTop: "1rem" }}>
        {cards.map((card) => (
          <div key={card.title} style={{ border: "1px solid #ccc", borderRadius: "12px", padding: "1rem" }}>
            <h2 style={{ margin: 0, fontSize: "1rem" }}>{card.title}</h2>
            <p style={{ fontSize: "1.5rem", fontWeight: "bold", marginTop: "0.5rem" }}>{card.value}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
"""

    api_text = """Suggested backend routes for dashboard:
GET /dashboard/summary
GET /dashboard/stats
"""

    created.append(write_text_file(root / "page.tsx", page_code))
    created.append(write_text_file(root / "api.txt", api_text))
    return created

def build_generic_module(project_name: str):
    created = []
    root = app_root(project_name) / "module"

    page_code = """export default function GeneratedModulePage() {
  return (
    <main style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
      <h1>Generated Module</h1>
      <p>This is a generic module scaffold created by Builder Core.</p>
    </main>
  );
}
"""

    api_text = """Suggested backend routes:
GET /module
POST /module
"""

    created.append(write_text_file(root / "page.tsx", page_code))
    created.append(write_text_file(root / "api.txt", api_text))
    return created

def generate_files(project_name: str, module_key: str):
    ensure_project_scaffold(project_name)

    if module_key == "notes_page":
        return build_notes_module(project_name)

    if module_key == "vendor_dashboard":
        return build_vendor_module(project_name)

    if module_key == "login_page":
        return build_login_module(project_name)

    if module_key == "dashboard_page":
        return build_dashboard_module(project_name)

    return build_generic_module(project_name)

def get_or_create_project(db, project_name: str):
    project = db.query(Project).filter(Project.name == project_name).first()
    if project:
        return project

    project = Project(name=project_name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def normalize_project_name(project_name: Optional[str]) -> str:
    return (project_name or "Default Project").strip() or "Default Project"

def build_run_info_payload(project_name: str):
    root = project_root(project_name)
    return {
        "project_name": project_name,
        "project_path": str(root),
        "run_script": str(root / "run_project.ps1"),
        "commands": [
            f'cd "{root}"',
            "npm install",
            "npm run dev"
        ],
        "url_hint": "The generated app usually runs on http://localhost:3000 unless you stop the main frontend first or choose another port."
    }

def get_github_repo_config():
    owner = (os.environ.get("GITHUB_OWNER") or DEFAULT_GITHUB_OWNER).strip() or DEFAULT_GITHUB_OWNER
    repo = (os.environ.get("GITHUB_REPO") or DEFAULT_GITHUB_REPO).strip() or DEFAULT_GITHUB_REPO
    branch = (os.environ.get("GITHUB_DEFAULT_BRANCH") or DEFAULT_GITHUB_BRANCH).strip() or DEFAULT_GITHUB_BRANCH
    token = (os.environ.get("GITHUB_STATUS_TOKEN") or "").strip()
    checks_workflow = (os.environ.get("GITHUB_CHECKS_WORKFLOW_NAME") or DEFAULT_GITHUB_CHECKS_WORKFLOW).strip() or DEFAULT_GITHUB_CHECKS_WORKFLOW
    deploy_workflow = (os.environ.get("GITHUB_DEPLOY_WORKFLOW_NAME") or DEFAULT_GITHUB_DEPLOY_WORKFLOW).strip() or DEFAULT_GITHUB_DEPLOY_WORKFLOW

    return {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "token": token,
        "checks_workflow": checks_workflow,
        "deploy_workflow": deploy_workflow,
    }

def github_api_json(url: str, token: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "builder-core-github-status"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urlrequest.Request(url, headers=headers)
    with urlrequest.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def summarize_commit(data: dict[str, Any]):
    commit = data.get("commit", {})
    author = commit.get("author", {})

    return {
        "sha": data.get("sha"),
        "short_sha": str(data.get("sha", ""))[:7],
        "message": commit.get("message"),
        "url": data.get("html_url"),
        "author": author.get("name"),
        "timestamp": author.get("date")
    }

def summarize_workflow_run(run: Optional[dict[str, Any]]):
    if not run:
        return None

    return {
        "name": run.get("name"),
        "status": run.get("status") or "unknown",
        "conclusion": run.get("conclusion"),
        "url": run.get("html_url"),
        "event": run.get("event"),
        "branch": run.get("head_branch"),
        "sha": run.get("head_sha"),
        "short_sha": str(run.get("head_sha", ""))[:7],
        "updated_at": run.get("updated_at")
    }

def find_workflow_run(workflow_runs: list[dict[str, Any]], workflow_name: str):
    for run in workflow_runs:
        if run.get("name") == workflow_name:
            return summarize_workflow_run(run)

    return None

def describe_workflow_state(workflow: Optional[dict[str, Any]]):
    if not workflow:
        return "not_found"

    if workflow.get("status") != "completed":
        return str(workflow.get("status") or "unknown")

    return str(workflow.get("conclusion") or "completed")

def build_github_summary(checks_workflow: Optional[dict[str, Any]], deploy_workflow: Optional[dict[str, Any]], branch: str):
    deploy_state = describe_workflow_state(deploy_workflow)
    checks_state = describe_workflow_state(checks_workflow)

    if deploy_state in {"queued", "in_progress", "waiting", "requested"}:
        return f"GitHub deploy tracking is live. The deploy workflow is currently {deploy_state.replace('_', ' ')} on {branch}."

    if deploy_state == "success":
        return f"GitHub deploy tracking is live. The deploy workflow completed successfully on {branch}."

    if deploy_state in {"failure", "cancelled", "timed_out"}:
        return f"GitHub deploy tracking is live. The deploy workflow needs attention because it ended with {deploy_state}."

    if checks_state in {"queued", "in_progress", "waiting", "requested"}:
        return f"GitHub tracking is connected. Repo checks are still {checks_state.replace('_', ' ')} on {branch}."

    if checks_state == "success":
        return f"GitHub tracking is connected. Repo checks are green on {branch}, and the deploy workflow is waiting for the next rollout."

    if checks_state in {"failure", "cancelled", "timed_out"}:
        return f"GitHub tracking is connected. Repo checks need attention because they ended with {checks_state}."

    return "GitHub tracking is connected. Builder Core can see the repo state, but no recent workflow run matched the configured workflow names."

def build_github_next_step(checks_workflow: Optional[dict[str, Any]], deploy_workflow: Optional[dict[str, Any]], branch: str):
    deploy_state = describe_workflow_state(deploy_workflow)
    checks_state = describe_workflow_state(checks_workflow)

    if deploy_state in {"queued", "in_progress", "waiting", "requested"}:
        return "Next: wait for the deploy workflow to finish, then verify the live frontend and backend."

    if deploy_state == "success":
        return "Next: refresh the app and confirm the newest Cloud Run revision is the one you expect."

    if deploy_state in {"failure", "cancelled", "timed_out"}:
        return "Next: open the deploy workflow run and review the failing step before moving to the next stage."

    if checks_state in {"queued", "in_progress", "waiting", "requested"}:
        return "Next: let Repo Checks finish before trusting the deployment stage."

    if checks_state == "success":
        return f"Next: the repo is ready for the next change on {branch}. Watch for the deploy workflow after the next merge."

    if checks_state in {"failure", "cancelled", "timed_out"}:
        return "Next: inspect the Repo Checks workflow, fix the issue, and rerun the pipeline."

    return "Next: push or merge a change to create a fresh GitHub workflow run for Builder Core to track."

def build_github_status_payload():
    config = get_github_repo_config()
    owner = config["owner"]
    repo = config["repo"]
    branch = config["branch"]
    token = config["token"]
    repo_label = f"{owner}/{repo}"

    commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{urlparse.quote(branch, safe='')}"
    runs_url = (
        f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        f"?branch={urlparse.quote(branch, safe='')}&per_page=20"
    )

    try:
        commit_data = github_api_json(commit_url, token)
        runs_data = github_api_json(runs_url, token)
        workflow_runs = runs_data.get("workflow_runs", [])

        checks_workflow = find_workflow_run(workflow_runs, config["checks_workflow"])
        deploy_workflow = find_workflow_run(workflow_runs, config["deploy_workflow"])

        return {
            "ok": True,
            "connected": True,
            "source": "live_github",
            "repo": repo_label,
            "branch": branch,
            "configured_with_token": bool(token),
            "latest_commit": summarize_commit(commit_data),
            "checks_workflow": checks_workflow,
            "deploy_workflow": deploy_workflow,
            "summary": build_github_summary(checks_workflow, deploy_workflow, branch),
            "next_step": build_github_next_step(checks_workflow, deploy_workflow, branch)
        }
    except urlerror.HTTPError as exc:
        return {
            "ok": False,
            "connected": False,
            "source": "github_error",
            "repo": repo_label,
            "branch": branch,
            "configured_with_token": bool(token),
            "latest_commit": None,
            "checks_workflow": None,
            "deploy_workflow": None,
            "summary": "GitHub status tracking is not available right now.",
            "next_step": "Next: try again later or add GITHUB_STATUS_TOKEN for higher GitHub API limits.",
            "error": f"GitHub API returned HTTP {exc.code}."
        }
    except (urlerror.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return {
            "ok": False,
            "connected": False,
            "source": "github_error",
            "repo": repo_label,
            "branch": branch,
            "configured_with_token": bool(token),
            "latest_commit": None,
            "checks_workflow": None,
            "deploy_workflow": None,
            "summary": "GitHub status tracking is not available right now.",
            "next_step": "Next: retry the GitHub status check after the network is available again.",
            "error": str(exc)
        }

def classify_chat_intent(instruction: str) -> str:
    text = instruction.lower()

    if any(phrase in text for phrase in ["what can you do", "help me understand", "explain", "what is builder core"]):
        return "chat"

    if any(phrase in text for phrase in ["how do i run", "run command", "launch", "start the app", "prepare run command"]):
        return "run"

    return "build"

def build_chat_risks(intent: str):
    if intent == "run":
        return [
            "Starting from the wrong folder can cause npm or uvicorn to fail.",
            "Running frontend and backend with mismatched ports will break the live preview."
        ]

    if intent == "chat":
        return [
            "Jumping into code changes too early can make the next step unclear.",
            "Skipping a quick repo check can turn a simple request into a risky edit."
        ]

    return [
        "Changing the wrong project files could break an already working feature.",
        "Skipping verification can hide frontend or backend regressions until deploy time."
    ]

def build_chat_testing_plan(intent: str, project_name: str):
    base_checks = [
        "Confirm /system/status still reports successfully in the app.",
        "Confirm the main command flow still responds in the Command Center.",
        f"Review the generated output for {project_name} before moving to deployment."
    ]

    if intent == "run":
        return base_checks + [
            "Verify the listed run commands start from the generated project folder.",
            "Confirm the expected local URL loads after npm run dev."
        ]

    if intent == "chat":
        return base_checks + [
            "Confirm the suggested next steps match the user request.",
            "Verify no file generation was triggered for an explanation-only request."
        ]

    return base_checks + [
        "Check the created files and module route before sending the task to Codex.",
        "Open the generated project or route preview after the simulated deploy finishes."
    ]

def build_next_steps(intent: str, project_name: str, plan: list[str], build_triggered: bool):
    if intent == "run":
        return [
            f"Open the {project_name} project folder and use the run commands below.",
            "Keep the backend status badge online before testing the generated app.",
            "Return to the Command Center if you want Builder Core to make another change."
        ]

    if intent == "chat":
        return [
            "Refine the instruction if you want Builder Core to switch from planning into code generation.",
            "Keep the project selected so the next request lands in the right workspace.",
            "Use the generated Codex prompt if you want a more explicit implementation handoff."
        ]

    next_steps = [
        "Review the plan and Codex prompt in the conversation before approving the next step.",
        "Use Send to Codex to continue the simulated automation pipeline.",
        f"Run the generated {project_name} project locally after deployment if you want a preview."
    ]

    if not plan:
        next_steps[0] = "Clarify the goal before moving into the simulated Codex flow."

    if build_triggered:
        next_steps.insert(1, "Inspect the created files so you know exactly what changed.")

    return next_steps

def build_codex_prompt(project_name: str, instruction: str, plan: list[str]):
    plan_lines = [f"- {step}" for step in plan] or ["- Inspect the repo and choose the smallest safe change set."]

    return "\n".join([
        "Repo: jagangill001/builder-core",
        f"Selected project: {project_name}",
        "",
        "Goal:",
        instruction,
        "",
        "Plan:",
        *plan_lines,
        "",
        "Safety rules:",
        "- Inspect the repo before editing.",
        "- Do not break working features.",
        "- Commit to main.",
        "- Explain files changed.",
        "- Provide testing steps.",
        "",
        "Legal rules:",
        "- Write original code for this repo.",
        "- Do not blindly copy third-party snippets.",
        "- Licensed frameworks are allowed when used normally."
    ])

def build_assistant_reply(intent: str, project_name: str, instruction: str, plan: list[str], build_result: Optional[dict] = None):
    if intent == "run":
        return (
            f"I reviewed your run request for {project_name}. "
            "I prepared the run guidance and the next steps you need so you can start the app safely."
        )

    if intent == "chat":
        return (
            f"I reviewed your request for {project_name}. "
            "I kept this in planning mode, outlined the next move, and prepared a Codex-ready prompt if you want to continue."
        )

    module_title = build_result.get("title") if build_result else "the requested module"
    route_path = build_result.get("route_path") if build_result else "the generated route"
    step_count = len(plan)

    return (
        f"I planned your request for {project_name}, prepared {step_count} implementation steps, "
        f"and updated the builder output for {module_title} at {route_path}. "
        "You can review the change summary below and then continue through the simulated Codex and deploy pipeline."
    )

def execute_plan_request(instruction: str, project_name: str):
    db = SessionLocal()
    try:
        if not instruction:
            return {"ok": False, "message": "Instruction is empty."}

        project = get_or_create_project(db, project_name)
        ensure_project_scaffold(project_name)

        plan, module_key, route_path, title = generate_plan(instruction)
        created_files = generate_files(project_name, module_key)

        registry_file = update_module_registry(project_name, module_key, route_path, title)
        shell_files = build_project_shell(project_name)
        manifest_file = write_manifest(project_name, module_key, instruction, created_files, plan, route_path, title)

        all_files = created_files + [registry_file, manifest_file] + shell_files

        request_record = BuildRequestRecord(
            instruction=instruction,
            status="success",
            project_id=project.id
        )
        db.add(request_record)
        db.commit()
        db.refresh(request_record)

        for step in plan:
            db.add(PlanStep(request_id=request_record.id, step_text=step))

        for file_path in all_files:
            db.add(CreatedFile(request_id=request_record.id, file_path=file_path))

        db.commit()

        return {
            "ok": True,
            "message": "Plan created successfully.",
            "instruction": instruction,
            "project_name": project_name,
            "module_key": module_key,
            "route_path": route_path,
            "title": title,
            "status": "success",
            "plan": plan,
            "created_files": all_files
        }
    finally:
        db.close()

@app.get("/")
def home():
    return {"status": "Builder Core Running"}

@app.get("/projects")
def get_projects():
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.name.asc()).all()
        return {
            "items": [{"id": p.id, "name": p.name} for p in projects]
        }
    finally:
        db.close()

@app.post("/projects")
def create_project(payload: ProjectCreate):
    db = SessionLocal()
    try:
        name = payload.name.strip()
        if not name:
            return {"ok": False, "message": "Project name is empty."}

        existing = db.query(Project).filter(Project.name == name).first()
        if existing:
            return {"ok": True, "message": "Project already exists.", "project": {"id": existing.id, "name": existing.name}}

        project = Project(name=name)
        db.add(project)
        db.commit()
        db.refresh(project)

        ensure_project_scaffold(name)
        build_project_shell(name)

        return {
            "ok": True,
            "message": "Project created successfully.",
            "project": {"id": project.id, "name": project.name}
        }
    finally:
        db.close()

@app.get("/history")
def get_history(project_name: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(BuildRequestRecord).order_by(BuildRequestRecord.id.desc())

        if project_name:
            query = query.join(Project).filter(Project.name == project_name)

        records = query.all()

        items = []
        for record in records:
            items.append({
                "instruction": record.instruction,
                "status": record.status,
                "project_name": record.project.name,
                "plan": [step.step_text for step in record.plans],
                "created_files": [file.file_path for file in record.files]
            })

        return {"items": items}
    finally:
        db.close()

@app.get("/project-files")
def get_project_files(project_name: str):
    root = project_root(project_name)
    if not root.exists():
        return {"items": []}

    items = []
    for path in root.rglob("*"):
        if path.is_file():
            items.append(str(path))

    return {"items": sorted(items)}

@app.get("/run-info")
def get_run_info(project_name: str):
    return build_run_info_payload(project_name)

@app.post("/plan")
def create_plan(payload: BuildRequest):
    instruction = payload.instruction.strip()
    project_name = normalize_project_name(payload.project_name)
    return execute_plan_request(instruction, project_name)

@app.post("/chat")
def chat(payload: BuildRequest):
    instruction = payload.instruction.strip()
    project_name = normalize_project_name(payload.project_name)

    if not instruction:
        return {
            "ok": False,
            "message": "Instruction is empty.",
            "assistant_reply": "Please enter a command so I can plan it and respond.",
            "project_name": project_name,
            "intent": "chat",
            "plan": [],
            "risks": [],
            "testing_plan": [],
            "next_steps": []
        }

    intent = classify_chat_intent(instruction)
    build_result = None

    if intent == "build":
        build_result = execute_plan_request(instruction, project_name)
        if not build_result.get("ok"):
            return {
                **build_result,
                "assistant_reply": "I could not complete the builder step for that request.",
                "intent": intent,
                "risks": build_chat_risks(intent),
                "testing_plan": build_chat_testing_plan(intent, project_name),
                "next_steps": build_next_steps(intent, project_name, [], False)
            }

        plan = build_result.get("plan", [])
    elif intent == "run":
        plan = [
            "Inspect the selected project folder.",
            "Return the safest run commands and script path.",
            "Explain the expected preview URL and verification steps."
        ]
    else:
        plan = [
            "Understand the goal and keep the next move narrow and safe.",
            "Summarize what Builder Core can do for the selected project.",
            "Prepare a Codex-ready instruction if the user wants implementation next."
        ]

    risks = build_chat_risks(intent)
    testing_plan = build_chat_testing_plan(intent, project_name)
    next_steps = build_next_steps(intent, project_name, plan, build_result is not None)
    codex_prompt = build_codex_prompt(project_name, instruction, plan)
    assistant_reply = build_assistant_reply(intent, project_name, instruction, plan, build_result)
    run_info = build_run_info_payload(project_name)

    response = {
        "ok": True,
        "message": build_result.get("message", "Chat response ready.") if build_result else "Chat response ready.",
        "assistant_reply": assistant_reply,
        "project_name": project_name,
        "intent": intent,
        "plan": plan,
        "risks": risks,
        "testing_plan": testing_plan,
        "next_steps": next_steps,
        "codex_prompt": codex_prompt,
        "build_triggered": build_result is not None,
        "run_info": run_info
    }

    if build_result:
        response.update(build_result)

    return response

@app.get("/github/status")
def github_status():
    return build_github_status_payload()
        
@app.get("/system/status")
def system_status():
    return {"status": "ok"}

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
