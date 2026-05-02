import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

try:
    from app.app_planner import AppPlannerService
    from app.chat_assistant import ASSISTANT_MODES, ChatAssistantService
    from app.bridge import BridgeService
    from app.command_router import route_user_message
    from app.crawler_plan import CrawlerPlanService
    from app.document_ingest import DocumentIngestService
    from app.intelligence import build_intelligence_brief, get_supported_modes
    from app.learning import LearningService
    from app.market_analyzer import MarketAnalyzerService
    from app.model_router import ModelRouterService
    from app.orchestrator import UnifiedOrchestrator
    from app.private_search import PrivateSearchService
    from app.prompt_builder import (
        build_acceptance_checks,
        build_codex_prompt as build_manual_codex_prompt,
        build_legal_safe_instructions,
        build_summary_requirements,
        get_project_context,
    )
    from app.research_engine import ResearchEngineService
    from app.research_tasks import RESEARCH_CATEGORIES, ResearchTaskService, SUPPORTED_SOURCES
    from app.safety import check_request_safety
    from app.self_improvement import SelfImprovementService
    from app.services import AutomationTaskService, FileStorageService
    from app.storage import ProjectStorageService
    from app.tasks import BackendTaskRunner
    from app.tool_registry import ToolRegistryService
    from app.web_ingest import WebIngestService
except ImportError:
    from app_planner import AppPlannerService
    from chat_assistant import ASSISTANT_MODES, ChatAssistantService
    from bridge import BridgeService
    from command_router import route_user_message
    from crawler_plan import CrawlerPlanService
    from document_ingest import DocumentIngestService
    from intelligence import build_intelligence_brief, get_supported_modes
    from learning import LearningService
    from market_analyzer import MarketAnalyzerService
    from model_router import ModelRouterService
    from orchestrator import UnifiedOrchestrator
    from private_search import PrivateSearchService
    from prompt_builder import (
        build_acceptance_checks,
        build_codex_prompt as build_manual_codex_prompt,
        build_legal_safe_instructions,
        build_summary_requirements,
        get_project_context,
    )
    from research_engine import ResearchEngineService
    from research_tasks import RESEARCH_CATEGORIES, ResearchTaskService, SUPPORTED_SOURCES
    from safety import check_request_safety
    from self_improvement import SelfImprovementService
    from services import AutomationTaskService, FileStorageService
    from storage import ProjectStorageService
    from tasks import BackendTaskRunner
    from tool_registry import ToolRegistryService
    from web_ingest import WebIngestService

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
REPO_ROOT = BASE_DIR.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "builder_core.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

DEFAULT_GITHUB_OWNER = "jagangill001"
DEFAULT_GITHUB_REPO = "builder-core"
DEFAULT_GITHUB_BRANCH = "main"
DEFAULT_GITHUB_CHECKS_WORKFLOW = "Repo Checks"
DEFAULT_GITHUB_DEPLOY_WORKFLOW = "Deploy Cloud Run"
DEFAULT_BACKEND_PUBLIC_URL = "https://builder-core-599596796788.us-central1.run.app"
DEFAULT_FRONTEND_PUBLIC_URL = "https://builder-core-frontend-599596796788.us-central1.run.app"

project_storage_service = ProjectStorageService(BASE_DIR)
automation_task_service = AutomationTaskService(BASE_DIR, project_storage_service)
file_storage_service = FileStorageService(BASE_DIR)
bridge_service = BridgeService()
learning_service = LearningService(REPO_ROOT, project_storage_service)
model_router_service = ModelRouterService()
private_search_service = PrivateSearchService(project_storage_service)
research_engine_service = ResearchEngineService(project_storage_service, private_search_service)
market_analyzer_service = MarketAnalyzerService(project_storage_service)
app_planner_service = AppPlannerService(project_storage_service)
assistant_service = ChatAssistantService(project_storage_service, learning_service, model_router_service, private_search_service)
research_task_service = ResearchTaskService(project_storage_service, learning_service)
self_improvement_service = SelfImprovementService(project_storage_service)
web_ingest_service = WebIngestService(project_storage_service, private_search_service)
document_ingest_service = DocumentIngestService(project_storage_service, private_search_service, learning_service)
crawler_plan_service = CrawlerPlanService(project_storage_service, web_ingest_service)
tool_registry_service = ToolRegistryService(project_storage_service)
orchestrator_service = UnifiedOrchestrator(
    storage=project_storage_service,
    learning=learning_service,
    task_service=automation_task_service,
    model_router=model_router_service,
    private_search=private_search_service,
    research_engine=research_engine_service,
    market_analyzer=market_analyzer_service,
    app_planner=app_planner_service,
    self_improvement=self_improvement_service,
    tool_registry=tool_registry_service,
)

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


def get_route_paths() -> set[str]:
    return {route.path for route in app.routes}


task_runner = BackendTaskRunner(
    task_service=automation_task_service,
    project_storage=project_storage_service,
    learning_service=learning_service,
    bridge_service=bridge_service,
    repo_root=REPO_ROOT,
    route_provider=get_route_paths,
)

class BuildRequest(BaseModel):
    instruction: str
    project_name: Optional[str] = "Default Project"

class ProjectCreate(BaseModel):
    name: str

class AutomationTaskCreate(BaseModel):
    command: str
    project_name: Optional[str] = "Default Project"
    status: Optional[str] = "received"
    current_stage: Optional[str] = "received"
    progress: Optional[int] = 1
    github_commit: Optional[str] = None
    workflow_status: Optional[str] = None
    logs: Optional[list[str]] = None
    errors: Optional[list[str]] = None
    summary: Optional[dict[str, Any]] = None
    bridge_status: Optional[dict[str, Any]] = None
    files_changed: Optional[list[str]] = None

class AutomationTaskUpdate(BaseModel):
    command: Optional[str] = None
    project_name: Optional[str] = None
    status: Optional[str] = None
    current_stage: Optional[str] = None
    stage: Optional[str] = None
    progress: Optional[int] = None
    github_commit: Optional[str] = None
    workflow_status: Optional[str] = None
    logs: Optional[list[str]] = None
    errors: Optional[list[str]] = None
    summary: Optional[dict[str, Any]] = None
    bridge_status: Optional[dict[str, Any]] = None
    files_changed: Optional[list[str]] = None
    stage_history: Optional[list[dict[str, Any]]] = None
    config_problems: Optional[list[str]] = None
    manual_setup: Optional[list[str]] = None
    testing_result: Optional[dict[str, Any]] = None
    deploy_result: Optional[dict[str, Any]] = None
    manual_advance: Optional[bool] = False

class TaskCreateRequest(BaseModel):
    command: str
    project_name: Optional[str] = "Default Project"

class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    stage: Optional[str] = None
    current_stage: Optional[str] = None
    progress: Optional[int] = None
    manual_advance: Optional[bool] = False

class MemoryEntryCreate(BaseModel):
    note: str
    category: Optional[str] = "manual_note"
    project_name: Optional[str] = "Builder Core"

class CodexPromptRequest(BaseModel):
    command: str
    project_name: Optional[str] = "Builder Core"

class IntelligencePlanRequest(BaseModel):
    command: str
    project_name: Optional[str] = "Builder Core"

class CodexSummaryRequest(BaseModel):
    codex_summary: str

class AssistantChatRequest(BaseModel):
    message: str
    mode: str = "general"
    save_to_memory: bool = True

class AssistantIdeaRequest(BaseModel):
    topic: str
    goal: str

class ResearchTaskCreateRequest(BaseModel):
    topic: str
    goal: str
    category: str = "general"
    sources: list[str] = Field(default_factory=lambda: ["memory"])
    run_now: bool = True

class SelfImprovementCreateRequest(BaseModel):
    note: str
    category: str = "chat"

class StorageCollectionRecordRequest(BaseModel):
    collection: str
    record: dict[str, Any]

class SearchAddRequest(BaseModel):
    title: str
    text: str
    source_type: str
    url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

class SearchQueryRequest(BaseModel):
    query: str
    limit: int = 10

class DocumentIngestRequest(BaseModel):
    title: str
    text: str
    source_type: str
    tags: list[str] = Field(default_factory=list)

class UrlIngestRequest(BaseModel):
    url: str
    source_note: Optional[str] = None

class CrawlerPlanRequest(BaseModel):
    seed_urls: list[str] = Field(default_factory=list)
    max_pages: int = 5

class CommandRequest(BaseModel):
    message: str
    mode: str = "auto"
    save_to_memory: bool = True

class StorageFileCreate(BaseModel):
    filename: str
    content: str
    content_type: Optional[str] = "text/plain"
    task_id: Optional[str] = None

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)

    return model.dict(exclude_none=True)


def get_prompt_generation_context() -> dict[str, Any]:
    project_structure_summary = project_storage_service.get_project_structure_summary()
    project_context = get_project_context(project_structure_summary)
    memory = project_storage_service.get_project_memory(8)
    assistant_memory = project_storage_service.get_assistant_memory(5)
    self_improvement_notes = [
        {
            "type": "self_improvement",
            "note": item.get("next_recommended_improvement") or item.get("project_lesson") or item.get("user_message"),
        }
        for item in project_storage_service.get_self_improvements(4)
    ]
    lessons = learning_service.get_lessons(8)
    known_issues = learning_service.get_known_issues()
    return {
        "project_context": project_context,
        "memory": memory + assistant_memory + self_improvement_notes,
        "lessons": lessons,
        "known_issues": known_issues,
    }


def get_intelligence_generation_context() -> dict[str, Any]:
    return {
        "project_memory": project_storage_service.get_project_memory(12),
        "lessons": learning_service.get_lessons(12),
        "latest_summary": project_storage_service.get_latest_summary(),
    }


def summarize_stage_history(task: dict[str, Any]) -> list[str]:
    stage_history = task.get("stage_history")
    if not isinstance(stage_history, list):
        return []

    ordered: list[str] = []
    seen: set[str] = set()
    for item in stage_history:
        if not isinstance(item, dict):
            continue

        stage = str(item.get("stage", "")).strip()
        if not stage or stage in seen:
            continue

        ordered.append(stage)
        seen.add(stage)
    return ordered


def build_manual_codex_summary(task: dict[str, Any], codex_summary: str, extracted: dict[str, Any]) -> dict[str, Any]:
    task_logs = list(task.get("logs") or [])
    task_errors = list(task.get("errors") or [])
    known_issues = extracted.get("known_issues", [])
    if isinstance(known_issues, list):
        for item in known_issues:
            text = str(item).strip()
            if text and text not in task_errors:
                task_errors.append(text)

    what_completed = extracted.get("what_completed", [])
    what_remains = extracted.get("what_remains", [])
    next_recommended_step = extracted.get(
        "next_recommendation",
        "Review the Codex summary and choose the next small Builder Core upgrade.",
    )

    return {
        "task_id": task.get("id"),
        "original_command": task.get("command"),
        "final_status": "completed_manual_codex",
        "stages_completed": summarize_stage_history(task) + ["prompt_ready", "summary_received"],
        "files_changed": extracted.get("files_changed", []),
        "folder_used": str(REPO_ROOT),
        "backend_logs": task_logs + ["Codex summary was pasted back into Builder Core."],
        "errors": task_errors,
        "what_completed": what_completed,
        "what_still_needs_manual_setup": what_remains,
        "next_recommended_step": next_recommended_step,
        "bridge_status": task.get("bridge_status", {}),
        "message": "Codex summary saved. Builder Core updated project memory and learning from the manual Codex result.",
        "codex_summary": codex_summary,
        "known_issues": known_issues,
        "updated_at": utc_now_iso(),
    }


def create_saved_intelligence_brief(command: str, project_name: str) -> dict[str, Any]:
    intelligence_context = get_intelligence_generation_context()
    brief = build_intelligence_brief(
        command=command,
        project_memory=intelligence_context["project_memory"],
        lessons=intelligence_context["lessons"],
        latest_summary=intelligence_context["latest_summary"],
    )

    saved_brief = project_storage_service.save_latest_intelligence_brief(
        {
            **brief,
            "project_name": project_name,
        }
    )
    project_storage_service.save_project_memory(
        {
            "type": "intelligence_brief",
            "project_name": project_name,
            "command": command,
            "note": brief["recommended_memory_note"],
            "mode": brief["mode"],
            "brief_id": brief["id"],
            "risk_level": brief["safety_firewall"].get("risk_level"),
        }
    )
    return saved_brief

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
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_STATUS_TOKEN") or "").strip()
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

def get_public_service_urls():
    backend_url = (os.environ.get("BACKEND_PUBLIC_URL") or DEFAULT_BACKEND_PUBLIC_URL).strip().rstrip("/")
    frontend_url = (os.environ.get("FRONTEND_PUBLIC_URL") or DEFAULT_FRONTEND_PUBLIC_URL).strip().rstrip("/")

    return {
        "backend": backend_url,
        "frontend": frontend_url,
    }

def check_public_service(url: str, expect_status_json: bool = False):
    if not url:
        return {
            "url": url,
            "reachable": False,
            "healthy": False,
            "status_code": None,
            "error": "URL not configured."
        }

    headers = {
        "User-Agent": "builder-core-deploy-status"
    }
    request = urlrequest.Request(url, headers=headers)

    try:
        with urlrequest.urlopen(request, timeout=8) as response:
            status_code = getattr(response, "status", response.getcode())
            body = response.read().decode("utf-8", errors="replace")
            reachable = 200 <= status_code < 400
            payload = {
                "url": url,
                "reachable": reachable,
                "healthy": reachable,
                "status_code": status_code
            }

            if expect_status_json:
                try:
                    data = json.loads(body)
                    reported_status = str(data.get("status", ""))
                    payload["reported_status"] = reported_status
                    payload["healthy"] = reachable and reported_status == "ok"
                except json.JSONDecodeError:
                    payload["healthy"] = False
                    payload["error"] = "Invalid JSON response."

            return payload
    except urlerror.HTTPError as exc:
        return {
            "url": url,
            "reachable": False,
            "healthy": False,
            "status_code": exc.code,
            "error": f"HTTP {exc.code}"
        }
    except (urlerror.URLError, TimeoutError, ValueError) as exc:
        return {
            "url": url,
            "reachable": False,
            "healthy": False,
            "status_code": None,
            "error": str(exc)
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

def build_deploy_status_summary(
    github_payload: dict[str, Any],
    deploy_running: bool,
    deploy_succeeded: bool,
    backend_healthy: bool,
    frontend_reachable: Optional[bool]
):
    if deploy_running:
        return "GitHub Actions running"

    if deploy_succeeded and backend_healthy and frontend_reachable:
        return "Ready to refresh"

    if deploy_succeeded and backend_healthy:
        return "Cloud Run is live"

    if deploy_succeeded:
        return "Deploy succeeded"

    if not github_payload.get("connected"):
        return "GitHub status not connected"

    if backend_healthy:
        return "Backend health is online while Builder Core waits for the next deploy signal."

    return str(github_payload.get("summary") or "Waiting for deploy status.")

def build_deploy_status_next_step(
    github_payload: dict[str, Any],
    deploy_running: bool,
    deploy_succeeded: bool,
    backend_healthy: bool,
    frontend_reachable: Optional[bool]
):
    if deploy_running:
        return "Next: wait for GitHub Actions to finish the deployment."

    if deploy_succeeded and backend_healthy and frontend_reachable:
        return "Next: refresh the app to load the newest live version."

    if deploy_succeeded and backend_healthy:
        return "Next: confirm the frontend URL is reachable before refreshing."

    if deploy_succeeded:
        return "Next: wait for the live backend and frontend checks to finish."

    return str(github_payload.get("next_step") or "Next: wait for the next tracked deployment update.")

def build_github_status_payload():
    config = get_github_repo_config()
    owner = config["owner"]
    repo = config["repo"]
    branch = config["branch"]
    token = config["token"]
    repo_label = f"{owner}/{repo}"

    if not token:
        return {
            "ok": True,
            "connected": False,
            "source": "not_configured",
            "repo": repo_label,
            "branch": branch,
            "configured_with_token": False,
            "latest_commit": None,
            "checks_workflow": None,
            "deploy_workflow": None,
            "summary": "GitHub status not connected",
            "next_step": "Next: set GITHUB_TOKEN in the backend environment to enable live GitHub workflow polling."
        }

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
            "next_step": "Next: try again later or add GITHUB_TOKEN for higher GitHub API limits.",
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

def build_deploy_status_payload():
    github_payload = build_github_status_payload()
    public_urls = get_public_service_urls()
    backend_check = check_public_service(f"{public_urls['backend']}/system/status", expect_status_json=True)
    frontend_check = check_public_service(public_urls["frontend"]) if public_urls["frontend"] else None
    deploy_workflow = github_payload.get("deploy_workflow")
    checks_workflow = github_payload.get("checks_workflow")
    deploy_state = describe_workflow_state(deploy_workflow)

    deploy_running = deploy_state in {"queued", "in_progress", "waiting", "requested"}
    deploy_succeeded = deploy_state == "success"
    backend_healthy = bool(backend_check.get("healthy"))
    frontend_reachable = None if frontend_check is None else bool(frontend_check.get("healthy"))
    ready_to_refresh = deploy_succeeded and backend_healthy and frontend_reachable is True

    return {
        "ok": True,
        "connected": bool(github_payload.get("connected")),
        "source": github_payload.get("source", "deploy_status"),
        "repo": github_payload.get("repo"),
        "branch": github_payload.get("branch"),
        "configured_with_token": bool(github_payload.get("configured_with_token")),
        "latest_commit": github_payload.get("latest_commit"),
        "checks_workflow": checks_workflow,
        "deploy_workflow": deploy_workflow,
        "deploy_running": deploy_running,
        "deploy_succeeded": deploy_succeeded,
        "backend_healthy": backend_healthy,
        "frontend_reachable": frontend_reachable,
        "ready_to_refresh": ready_to_refresh,
        "backend_check": backend_check,
        "frontend_check": frontend_check,
        "summary": build_deploy_status_summary(
            github_payload,
            deploy_running,
            deploy_succeeded,
            backend_healthy,
            frontend_reachable
        ),
        "next_step": build_deploy_status_next_step(
            github_payload,
            deploy_running,
            deploy_succeeded,
            backend_healthy,
            frontend_reachable
        ),
        "updated_at": utc_now_iso(),
        "error": github_payload.get("error")
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
        "Use the compact task bar and Next button to continue the tracked automation stages.",
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

@app.post("/prompts/codex")
def create_codex_prompt(payload: CodexPromptRequest):
    command = payload.command.strip()
    project_name = normalize_project_name(payload.project_name)

    if not command:
        raise HTTPException(status_code=400, detail="Command is empty.")

    prompt_context = get_prompt_generation_context()
    intelligence_brief = create_saved_intelligence_brief(command, project_name)
    prompt = build_manual_codex_prompt(
        command=command,
        project_context=prompt_context["project_context"],
        memory=prompt_context["memory"],
        lessons=prompt_context["lessons"],
        known_issues=prompt_context["known_issues"],
        intelligence_brief=intelligence_brief,
    )

    bridge_status = bridge_service.build_bridge_status_payload()
    task = automation_task_service.create_task(
        command=command,
        project_name=project_name,
        status="prompt_ready",
        current_stage="planning",
        progress=10,
        logs=[
            "Codex prompt generated for manual execution.",
            "Builder Core is waiting for the user to copy this prompt into Codex.",
        ],
        errors=[],
        summary=None,
        bridge_status=bridge_status,
        files_changed=[],
        generated_prompt=prompt,
        intelligence_mode=intelligence_brief.get("mode"),
        intelligence_brief=intelligence_brief,
    )

    prompt_record = {
        "task_id": task["id"],
        "command": command,
        "project_name": project_name,
        "status": "prompt_ready",
        "prompt": prompt,
        "created_at": utc_now_iso(),
    }
    project_storage_service.save_latest_prompt(prompt_record)
    project_storage_service.save_project_memory(
        {
            "type": "prompt_generated",
            "task_id": task["id"],
            "command": command,
            "project_name": project_name,
            "note": "Generated a Codex prompt for manual execution.",
            "prompt_preview": prompt[:500],
        }
    )

    return {
        "task_id": task["id"],
        "prompt": prompt,
        "status": "prompt_ready",
        "intelligence_brief": intelligence_brief,
    }

@app.get("/prompts/latest")
def get_latest_prompt():
    latest_prompt = project_storage_service.get_latest_prompt()
    if latest_prompt is None:
        return {
            "ok": False,
            "message": "No Codex prompt has been generated yet.",
            "item": None,
        }

    return {
        "ok": True,
        "item": latest_prompt,
    }


@app.post("/intelligence/plan")
def create_intelligence_plan(payload: IntelligencePlanRequest):
    command = payload.command.strip()
    project_name = normalize_project_name(payload.project_name)

    if not command:
        raise HTTPException(status_code=400, detail="Command is empty.")

    brief = create_saved_intelligence_brief(command, project_name)
    return {
        "ok": True,
        "brief": brief,
        "supported_modes": get_supported_modes(),
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
    }


@app.get("/intelligence")
def get_intelligence():
    return {
        "ok": True,
        "latest_brief": project_storage_service.get_latest_intelligence_brief(),
        "intelligence_history": project_storage_service.get_intelligence_history(12),
        "supported_modes": get_supported_modes(),
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
        "notes": [
            "Builder Core structures research and planning safely.",
            "It does not claim to replace a lawyer, analyst, teacher, or other licensed expert.",
        ],
    }

@app.post("/assistant/chat")
def assistant_chat(payload: AssistantChatRequest):
    message = payload.message.strip()
    mode = (payload.mode or "general").strip().lower()

    if not message:
        raise HTTPException(status_code=400, detail="Assistant message is empty.")

    if mode not in ASSISTANT_MODES:
        mode = "general"

    safety = check_request_safety(message, category=mode)
    if not safety["allowed"]:
        return {
            "chat_id": f"chat_blocked_{utc_now_iso()}",
            "reply": safety["reason"],
            "suggestions": [safety["safe_alternative"]],
            "memory_used": [],
            "saved_to_memory": False,
            "next_actions": [safety["safe_alternative"]],
            "created_at": utc_now_iso(),
            "assistant_status": model_router_service.get_active_model_status(),
        }

    result = assistant_service.chat(message=message, mode=mode, save_to_memory=bool(payload.save_to_memory))

    if payload.save_to_memory:
        self_improvement_service.record_interaction_lesson(
            {
                "category": "chat",
                "user_message": message,
                "assistant_reply": result["reply"],
                "suggestions": result["suggestions"],
                "status": "saved_to_memory",
            }
        )

    return result


@app.get("/assistant/history")
def assistant_history(limit: int = 30):
    return {
        "ok": True,
        "items": assistant_service.get_history(limit),
        "assistant_status": assistant_service.build_status(),
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
    }


@app.post("/assistant/idea")
def assistant_idea(payload: AssistantIdeaRequest):
    topic = payload.topic.strip()
    goal = payload.goal.strip()

    if not topic and not goal:
        raise HTTPException(status_code=400, detail="Idea topic or goal is required.")

    return assistant_service.generate_ideas(topic=topic, goal=goal)


@app.get("/assistant/model-status")
def assistant_model_status():
    return model_router_service.get_active_model_status()


@app.get("/tools")
def get_tools():
    return {
        "ok": True,
        "items": tool_registry_service.list_tools(),
        "status": tool_registry_service.get_tool_status(),
    }


@app.get("/storage/status")
def storage_status():
    return project_storage_service.health_check()


@app.post("/storage/test")
def storage_test():
    return project_storage_service.run_storage_test()


@app.post("/search/add")
def search_add(payload: SearchAddRequest):
    safety = check_request_safety(payload.text, category=payload.source_type)
    if not safety["allowed"]:
        return {
            "ok": False,
            "document_id": None,
            "chunks_created": 0,
            "saved_to_search": False,
            "warnings": [safety["reason"], safety["safe_alternative"]],
        }

    result = private_search_service.add_document_to_index(
        title=payload.title,
        text=payload.text,
        source_type=payload.source_type,
        url=payload.url,
        metadata=payload.metadata,
    )
    return {
        "ok": True,
        **result,
    }


@app.post("/search/query")
def search_query(payload: SearchQueryRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query is empty.")

    return private_search_service.search_private_index(query=query, limit=max(1, min(payload.limit, 20)))


@app.get("/search/status")
def search_status():
    return private_search_service.get_search_status()


@app.post("/search/rebuild")
def search_rebuild():
    return private_search_service.rebuild_index_from_storage()


@app.post("/documents/ingest-text")
def document_ingest_text(payload: DocumentIngestRequest):
    title = payload.title.strip()
    text = payload.text.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Document title is empty.")
    if not text:
        raise HTTPException(status_code=400, detail="Document text is empty.")

    return document_ingest_service.ingest_text(title=title, text=text, source_type=payload.source_type, tags=payload.tags)


@app.post("/search/ingest-url")
def search_ingest_url(payload: UrlIngestRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is empty.")
    return web_ingest_service.ingest_url(url=url, source_note=payload.source_note)


@app.post("/crawler/plan")
def crawler_plan(payload: CrawlerPlanRequest):
    if not payload.seed_urls:
        raise HTTPException(status_code=400, detail="At least one seed URL is required.")
    return crawler_plan_service.create_crawl_plan(seed_urls=payload.seed_urls, max_pages=payload.max_pages)


@app.post("/command")
def command(payload: CommandRequest):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Command message is empty.")
    return orchestrator_service.run_unified_workflow(
        message=message,
        mode=payload.mode or "auto",
        save_to_memory=bool(payload.save_to_memory),
    )


@app.post("/research/tasks")
def create_research_task(payload: ResearchTaskCreateRequest):
    topic = payload.topic.strip()
    goal = payload.goal.strip()
    category = (payload.category or "general").strip().lower()
    sources = payload.sources or ["memory"]

    if not topic:
        raise HTTPException(status_code=400, detail="Research topic is empty.")

    if not goal:
        raise HTTPException(status_code=400, detail="Research goal is empty.")

    if category not in RESEARCH_CATEGORIES:
        category = "general"

    task = research_task_service.create_task(
        topic=topic,
        goal=goal,
        category=category,
        sources=sources,
        run_now=bool(payload.run_now),
    )

    return {
        "research_id": task["research_id"],
        "topic": task["topic"],
        "goal": task["goal"],
        "category": task["category"],
        "sources": task["sources"],
        "status": task["status"],
        "summary": task["summary"],
        "findings": task["findings"],
        "limitations": task["limitations"],
        "next_steps": task["next_steps"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
        "web_connected": task.get("web_connected", False),
    }


@app.get("/research/tasks")
def list_research_tasks(limit: int = 20):
    return {
        "ok": True,
        "items": research_task_service.list_tasks(limit),
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
        "notes": [
            "Research tasks are saved honestly and do not secretly run forever in the background.",
            "Web research is not connected yet in this build.",
        ],
    }


@app.get("/research/tasks/{research_id}")
def get_research_task(research_id: str):
    item = research_task_service.get_task(research_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research task not found.")

    return item


@app.get("/self-improvement")
def get_self_improvement():
    return {
        "ok": True,
        "items": self_improvement_service.get_improvement_notes(20),
        "next_recommended_upgrade": self_improvement_service.suggest_next_project_upgrade(),
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
        "notes": [
            "This is memory-based improvement, not real AI model training.",
            "Builder Core learns from saved chats, tasks, and summaries only.",
        ],
    }


@app.post("/self-improvement")
def create_self_improvement_entry(payload: SelfImprovementCreateRequest):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=400, detail="Self-improvement note is empty.")

    item = self_improvement_service.record_interaction_lesson(
        {
            "category": payload.category or "chat",
            "user_message": note,
            "assistant_reply": "",
            "status": "manual_note",
        }
    )
    return {
        "ok": True,
        "item": item,
        "next_recommended_upgrade": self_improvement_service.suggest_next_project_upgrade(),
    }

@app.post("/tasks")
def create_task(payload: TaskCreateRequest):
    command = payload.command.strip()
    project_name = normalize_project_name(payload.project_name)

    if not command:
        raise HTTPException(status_code=400, detail="Command is empty.")

    item = task_runner.create_task(command=command, project_name=project_name)
    return {
        "task_id": item["id"],
        "status": item["status"],
        "stage": item["stage"],
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message,
    }

@app.get("/tasks")
def list_tasks(limit: int = 20):
    return {
        "items": automation_task_service.list_tasks(limit=limit),
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message,
    }

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    item = automation_task_service.get_task(task_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return item

@app.patch("/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdateRequest):
    task = automation_task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    if payload.manual_advance:
        item = task_runner.manual_advance(task_id)
    else:
        item = automation_task_service.update_task(task_id, model_to_dict(payload))

    if item is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return item

@app.post("/tasks/{task_id}/codex-summary")
def save_codex_summary(task_id: str, payload: CodexSummaryRequest):
    codex_summary = payload.codex_summary.strip()
    if not codex_summary:
        raise HTTPException(status_code=400, detail="Codex summary is empty.")

    task = automation_task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    extracted = learning_service.extract_codex_summary_details(codex_summary)
    logs = list(task.get("logs") or [])
    logs.append("Codex summary received from the user.")

    stage_history = list(task.get("stage_history") or [])
    stage_history.append(
        {
            "stage": "summary_received",
            "status": "completed_manual_codex",
            "progress": 100,
            "timestamp": utc_now_iso(),
            "message": "Codex summary was saved manually.",
        }
    )

    summary = build_manual_codex_summary(task, codex_summary, extracted)
    updates = {
        "status": "completed_manual_codex",
        "stage": "completed",
        "current_stage": "completed",
        "progress": 100,
        "logs": logs,
        "errors": summary["errors"],
        "summary": summary,
        "codex_summary": codex_summary,
        "files_changed": extracted.get("files_changed", []),
        "stage_history": stage_history,
        "known_issues": extracted.get("known_issues", []),
        "what_completed": extracted.get("what_completed", []),
        "what_remains": extracted.get("what_remains", []),
        "next_recommended_step": extracted.get("next_recommendation"),
    }
    updated = automation_task_service.update_task(task_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    project_storage_service.save_latest_summary(summary)
    project_storage_service.save_project_memory(
        {
            "type": "codex_summary",
            "task_id": task_id,
            "command": task.get("command"),
            "project_name": task.get("project_name", "Builder Core"),
            "note": "Saved a manual Codex summary for this Builder Core task.",
            "mode": task.get("intelligence_mode"),
            "codex_summary": codex_summary,
            "files_changed": extracted.get("files_changed", []),
            "known_issues": extracted.get("known_issues", []),
            "next_recommended_step": extracted.get("next_recommendation"),
        }
    )
    lesson = learning_service.record_codex_summary_lesson(updated, codex_summary)
    self_improvement_service.record_interaction_lesson(
        {
            "category": "project",
            "command": task.get("command"),
            "summary": codex_summary,
            "status": "completed_manual_codex",
            "suggestions": [extracted.get("next_recommendation")],
        }
    )

    return {
        "ok": True,
        "message": "Codex summary saved.",
        "item": updated,
        "lesson": lesson,
    }

@app.post("/automation/tasks")
def create_automation_task(payload: AutomationTaskCreate):
    command = payload.command.strip()
    project_name = normalize_project_name(payload.project_name)

    if not command:
        raise HTTPException(status_code=400, detail="Task command is empty.")

    item = automation_task_service.create_task(
        command=command,
        project_name=project_name,
        status=payload.status or "received",
        current_stage=payload.current_stage or "received",
        progress=payload.progress or 1,
        github_commit=payload.github_commit,
        workflow_status=payload.workflow_status,
        logs=payload.logs,
        errors=payload.errors,
        summary=payload.summary,
        bridge_status=payload.bridge_status,
        files_changed=payload.files_changed,
    )
    return {
        "ok": True,
        "message": "Automation task created.",
        "item": item,
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message
    }

@app.get("/automation/tasks")
def list_automation_tasks():
    return {
        "ok": True,
        "items": automation_task_service.list_tasks(),
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message
    }

@app.get("/automation/tasks/{task_id}")
def get_automation_task(task_id: str):
    item = automation_task_service.get_task(task_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Automation task not found.")

    return {
        "ok": True,
        "item": item,
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message
    }

@app.patch("/automation/tasks/{task_id}")
def update_automation_task(task_id: str, payload: AutomationTaskUpdate):
    if payload.manual_advance:
        item = task_runner.manual_advance(task_id)
    else:
        item = automation_task_service.update_task(task_id, model_to_dict(payload))

    if item is None:
        raise HTTPException(status_code=404, detail="Automation task not found.")

    return {
        "ok": True,
        "message": "Automation task updated.",
        "item": item,
        "storage_backend": automation_task_service.storage_backend,
        "storage_message": automation_task_service.storage_message
    }

@app.get("/automation/github-status")
def automation_github_status():
    return bridge_service.build_github_status_payload()

@app.get("/automation/deploy-status")
def automation_deploy_status():
    return bridge_service.build_deploy_status_payload()

@app.get("/memory")
def get_memory():
    return {
        "ok": True,
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
        "project_memory": project_storage_service.get_project_memory(20),
        "assistant_memory": project_storage_service.get_assistant_memory(20),
        "chat_history": project_storage_service.get_chat_history(20),
        "research_tasks": project_storage_service.get_research_tasks(10),
        "research_results": project_storage_service.get_research_results(10),
        "self_improvement": project_storage_service.get_self_improvements(10),
        "app_plans": project_storage_service.list_records("app_plans", 10),
        "market_analysis": project_storage_service.list_records("market_analysis", 10),
        "command_history": project_storage_service.list_records("command_history", 10),
        "latest_summary": project_storage_service.get_latest_summary(),
        "latest_prompt": project_storage_service.get_latest_prompt(),
        "prompt_history": project_storage_service.get_prompt_history(10),
        "latest_intelligence_brief": project_storage_service.get_latest_intelligence_brief(),
        "intelligence_history": project_storage_service.get_intelligence_history(10),
        "latest_bridge_status": project_storage_service.get_latest_bridge_status(),
        "known_environment_problems": project_storage_service.get_known_environment_problems(),
        "cloud_ready_notes": project_storage_service.cloud_ready_notes,
    }

@app.post("/memory")
def create_memory_entry(payload: MemoryEntryCreate):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=400, detail="Memory note is empty.")

    entry = project_storage_service.save_project_memory(
        {
            "type": payload.category or "manual_note",
            "project_name": payload.project_name or "Builder Core",
            "note": note,
        }
    )
    return {
        "ok": True,
        "item": entry,
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
    }

@app.get("/learning")
def get_learning():
    payload = learning_service.build_learning_payload()
    return {
        "ok": True,
        **payload,
    }

@app.post("/learning/scan")
def scan_learning():
    summary = learning_service.scan_project_structure()
    project_storage_service.save_project_memory(
        {
            "type": "learning_scan",
            "project_name": "Builder Core",
            "note": "Project structure scan completed.",
            "summary": summary,
        }
    )
    return {
        "ok": True,
        "summary": summary,
        "storage_backend": project_storage_service.storage_backend,
        "storage_message": project_storage_service.storage_message,
    }

@app.post("/storage/files")
def create_storage_file(payload: StorageFileCreate):
    filename = payload.filename.strip()
    if not filename:
        return {
            "ok": False,
            "message": "Filename is empty.",
            "storage_backend": file_storage_service.storage_backend,
            "storage_message": file_storage_service.storage_message
        }

    item = file_storage_service.create_file(
        filename=filename,
        content=payload.content,
        content_type=payload.content_type or "text/plain",
        task_id=payload.task_id
    )
    return {
        "ok": True,
        "message": "Storage file created.",
        "item": item,
        "storage_backend": file_storage_service.storage_backend,
        "storage_message": file_storage_service.storage_message
    }

@app.get("/storage/files")
def list_storage_files():
    return {
        "ok": True,
        "items": file_storage_service.list_files(),
        "storage_backend": file_storage_service.storage_backend,
        "storage_message": file_storage_service.storage_message
    }

@app.get("/storage/files/{file_id}")
def get_storage_file(file_id: str):
    item = file_storage_service.get_file(file_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Storage file not found.")

    return {
        "ok": True,
        "item": item,
        "storage_backend": file_storage_service.storage_backend,
        "storage_message": file_storage_service.storage_message
    }

@app.delete("/storage/files/{file_id}")
def delete_storage_file(file_id: str):
    item = file_storage_service.delete_file(file_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Storage file not found.")

    return {
        "ok": True,
        "message": "Storage file deleted.",
        "item": item,
        "storage_backend": file_storage_service.storage_backend,
        "storage_message": file_storage_service.storage_message
    }

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
    return bridge_service.build_github_status_payload()
        
@app.get("/system/status")
def system_status():
    storage_status_payload = project_storage_service.health_check()
    model_status = model_router_service.get_active_model_status()
    bridge_status = bridge_service.build_bridge_status_payload()
    search_status_payload = private_search_service.get_search_status()
    tool_status = tool_registry_service.get_tool_status()
    public_urls = bridge_service.get_public_urls()

    return {
        "status": "ok",
        "service": "Builder Core",
        "manual_codex_mode": True,
        "intelligence_center_enabled": True,
        "assistant_enabled": True,
        "assistant_status": assistant_service.build_status(),
        "assistant_mode": model_status.get("assistant_mode"),
        "active_brain": model_status.get("active_brain"),
        "local_model_provider": model_status.get("local_model_provider"),
        "research_system_enabled": True,
        "supported_intelligence_modes": get_supported_modes(),
        "bridge_status": bridge_status,
        "task_storage_backend": automation_task_service.storage_backend,
        "task_storage_message": automation_task_service.storage_message,
        "memory_storage_backend": project_storage_service.storage_backend,
        "memory_storage_message": project_storage_service.storage_message,
        "storage_mode_requested": project_storage_service.storage_mode_requested,
        "storage_mode": storage_status_payload.get("storage_mode"),
        "firestore_enabled": storage_status_payload.get("firestore_enabled"),
        "using_firestore": storage_status_payload.get("using_firestore"),
        "using_fallback": storage_status_payload.get("using_fallback"),
        "firestore_warnings": storage_status_payload.get("warnings", []),
        "gcp_project_id": storage_status_payload.get("gcp_project_id"),
        "cloud_ready_notes": project_storage_service.cloud_ready_notes,
        "file_storage_backend": file_storage_service.storage_backend,
        "file_storage_message": file_storage_service.storage_message,
        "memory_count": storage_status_payload.get("project_memory_count", 0),
        "research_task_count": storage_status_payload.get("research_task_count", 0),
        "private_search_document_count": search_status_payload.get("document_count", 0),
        "private_search_chunk_count": search_status_payload.get("chunk_count", 0),
        "command_router_status": {
            "mode": "rule_based",
            "supported_workflows": [
                "normal_chat",
                "research_only",
                "market_analysis",
                "app_builder",
                "research_to_app_plan",
                "codex_prompt_only",
                "save_summary",
                "cloud_storage_setup",
                "private_search",
                "document_ingest",
                "url_ingest",
                "crawler_plan",
            ],
        },
        "orchestrator_status": {
            "enabled": True,
            "engine": "internal_unified_orchestrator",
            "uses_private_search": True,
            "uses_market_analyzer": True,
            "uses_app_planner": True,
        },
        "internal_tool_registry_status": tool_status,
        "storage_status": storage_status_payload,
        "search_status": search_status_payload,
        "frontend_url": public_urls.get("frontend"),
        "backend_url": public_urls.get("backend"),
        "latest_summary_available": project_storage_service.get_latest_summary() is not None,
        "latest_prompt_available": project_storage_service.get_latest_prompt() is not None,
        "latest_intelligence_available": project_storage_service.get_latest_intelligence_brief() is not None,
        "assistant_memory_available": len(project_storage_service.get_assistant_memory(1)) > 0,
        "chat_history_available": len(project_storage_service.get_chat_history(1)) > 0,
        "research_tasks_available": len(project_storage_service.get_research_tasks(1)) > 0,
        "self_improvement_available": len(project_storage_service.get_self_improvements(1)) > 0,
        "project_structure_scanned": project_storage_service.get_project_structure_summary() is not None,
        "legal_safe_prompting": {
            "summary_requirements": build_summary_requirements(),
            "acceptance_checks": build_acceptance_checks(),
            "legal_safe_instructions": build_legal_safe_instructions(),
        },
    }

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
