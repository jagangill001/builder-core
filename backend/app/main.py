from pathlib import Path
from typing import Optional
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

app = FastAPI(title="Builder Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "builder_core.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

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

@app.post("/plan")
def create_plan(payload: BuildRequest):
    db = SessionLocal()
    try:
        instruction = payload.instruction.strip()
        project_name = (payload.project_name or "Default Project").strip() or "Default Project"

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
