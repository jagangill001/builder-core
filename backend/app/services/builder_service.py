from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

from app.database import GENERATED_DIR

MODULE_BLUEPRINTS: dict[str, dict[str, str]] = {
    "booking_page": {
        "module_key": "booking_page",
        "route_path": "/booking",
        "title": "Booking",
    },
    "notes_page": {
        "module_key": "notes_page",
        "route_path": "/notes",
        "title": "Notes",
    },
    "vendor_dashboard": {
        "module_key": "vendor_dashboard",
        "route_path": "/vendors",
        "title": "Vendors",
    },
    "login_page": {
        "module_key": "login_page",
        "route_path": "/login",
        "title": "Login",
    },
    "dashboard_page": {
        "module_key": "dashboard_page",
        "route_path": "/dashboard",
        "title": "Dashboard",
    },
    "generic_module": {
        "module_key": "generic_module",
        "route_path": "/module",
        "title": "Module",
    },
}


def safe_name(value: str) -> str:
    return value.strip().replace(" ", "_").replace("-", "_").lower()


def project_root(project_name: str, create: bool = True) -> Path:
    root = GENERATED_DIR / safe_name(project_name)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def app_root(project_name: str, create: bool = True) -> Path:
    root = project_root(project_name, create=create) / "app"
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def registry_path(project_name: str, create: bool = True) -> Path:
    path = project_root(project_name, create=create) / "module_registry.json"
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path(project_name: str, module_key: str) -> Path:
    return project_root(project_name) / f"{module_key}_manifest.json"


def route_file_path(project_name: str, route_path: str) -> Path:
    cleaned = route_path.strip("/")
    if not cleaned:
        return app_root(project_name) / "page.tsx"
    return app_root(project_name) / cleaned / "page.tsx"


def assistant_memory_path() -> Path:
    return GENERATED_DIR / "_assistant_memory.json"


def write_text_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json_file(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)


def read_registry(project_name: str) -> dict[str, Any]:
    path = registry_path(project_name, create=False)
    if not path.exists():
        return {"project_name": project_name, "modules": []}
    return read_json_file(path, {"project_name": project_name, "modules": []})


def write_registry(project_name: str, data: dict[str, Any]) -> str:
    return write_json_file(registry_path(project_name), data)


def update_module_registry(project_name: str, module_key: str, route_path: str, title: str) -> str:
    data = read_registry(project_name)
    modules = data.setdefault("modules", [])

    updated = False
    for module in modules:
        if module.get("module_key") == module_key:
            module["route_path"] = route_path
            module["title"] = title
            updated = True
            break

    if not updated:
        modules.append(
            {
                "module_key": module_key,
                "route_path": route_path,
                "title": title,
            }
        )

    data["project_name"] = project_name
    return write_registry(project_name, data)


def ensure_project_scaffold(project_name: str) -> None:
    root = project_root(project_name)
    app_root(project_name)

    write_text_file(
        root / "README.txt",
        f"Generated project scaffold for {project_name}\n\nThis project was created by Builder Core v6.\n",
    )

    if not registry_path(project_name, create=False).exists():
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
                    "start": "next start",
                },
                "dependencies": {
                    "next": "^16.2.2",
                    "react": "^19.0.0",
                    "react-dom": "^19.0.0",
                },
                "devDependencies": {
                    "@types/node": "^20.0.0",
                    "@types/react": "^19.0.0",
                    "@types/react-dom": "^19.0.0",
                    "typescript": "^5.0.0",
                },
            },
            indent=2,
        ),
    )

    write_text_file(
        root / "next.config.mjs",
        dedent(
            """
            const nextConfig = {
              reactStrictMode: true,
            };

            export default nextConfig;
            """
        ).strip()
        + "\n",
    )

    write_text_file(
        root / "tsconfig.json",
        dedent(
            """
            {
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
        ).strip()
        + "\n",
    )

    write_text_file(
        root / "next-env.d.ts",
        dedent(
            """
            /// <reference types="next" />
            /// <reference types="next/image-types/global" />

            // This file was generated by Builder Core.
            """
        ).strip()
        + "\n",
    )

    write_text_file(
        root / "run_project.ps1",
        dedent(
            f"""
            cd "{root}"
            npm install
            npm run dev
            """
        ).strip()
        + "\n",
    )

    write_text_file(
        root / "run_project.sh",
        dedent(
            """
            #!/usr/bin/env sh
            set -eu

            cd "$(dirname "$0")"
            npm install
            npm run dev
            """
        ).strip()
        + "\n",
    )


def build_project_shell(project_name: str) -> list[str]:
    data = read_registry(project_name)
    modules = data.get("modules", [])
    project_app_dir = app_root(project_name)
    created: list[str] = []

    nav_links = "\n".join(
        [
            f'              <a href="{module["route_path"]}" style={{{{ color: "#2563eb", textDecoration: "none", fontWeight: 600 }}}}>{module["title"]}</a>'
            for module in modules
        ]
    )

    module_cards = "\n".join(
        [
            f"""          <div style={{{{ border: "1px solid #ddd", borderRadius: "12px", padding: "1rem" }}}}>
            <h2 style={{{{ marginTop: 0 }}}}>{module["title"]}</h2>
            <p>Route: {module["route_path"]}</p>
            <a href="{module["route_path"]}" style={{{{ color: "#2563eb", textDecoration: "none", fontWeight: 600 }}}}>Open module</a>
          </div>"""
            for module in modules
        ]
    )

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
        <p>This app shell was generated by Builder Core and is ready for module updates.</p>
      </section>

      <section style={{{{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}}}>
{module_cards if module_cards else '        <p>No modules generated yet.</p>'}
      </section>
    </main>
  );
}}
"""

    created.append(write_text_file(project_app_dir / "layout.tsx", layout_code))
    created.append(write_text_file(project_app_dir / "page.tsx", home_code))
    return created


def write_manifest(
    project_name: str,
    module_key: str,
    instruction: str,
    created_files: list[str],
    plan: list[str],
    route_path: str,
    title: str,
    intent: str,
) -> str:
    manifest = {
        "project_name": project_name,
        "module_key": module_key,
        "title": title,
        "route_path": route_path,
        "instruction": instruction,
        "intent": intent,
        "created_files": created_files,
        "plan": plan,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    return write_json_file(manifest_path(project_name, module_key), manifest)


def resolve_module_blueprint(instruction: str, fallback_module_key: str | None = None) -> dict[str, str]:
    text = instruction.lower()
    keyword_map = [
        ("booking_page", ("booking", "appointment", "schedule", "repair business", "repair shop")),
        ("notes_page", ("notes", "note")),
        ("vendor_dashboard", ("vendor", "supplier", "quote")),
        ("login_page", ("login", "auth", "sign in", "signin")),
        ("dashboard_page", ("dashboard", "chart", "analytics")),
    ]

    for module_key, keywords in keyword_map:
        if any(keyword in text for keyword in keywords):
            return MODULE_BLUEPRINTS[module_key].copy()

    if fallback_module_key and fallback_module_key in MODULE_BLUEPRINTS:
        return MODULE_BLUEPRINTS[fallback_module_key].copy()

    return MODULE_BLUEPRINTS["generic_module"].copy()


def _render_notes_page() -> str:
    return dedent(
        """
        "use client";

        import { FormEvent, useState } from "react";

        type Note = {
          id: number;
          title: string;
          content: string;
        };

        const starterNotes: Note[] = [
          { id: 1, title: "Kickoff call", content: "Confirm scope, owner, and timeline." },
          { id: 2, title: "Parts checklist", content: "Track the materials needed before launch." },
        ];

        export default function NotesPage() {
          const [notes, setNotes] = useState(starterNotes);
          const [editingId, setEditingId] = useState<number | null>(null);
          const [title, setTitle] = useState("");
          const [content, setContent] = useState("");

          function resetForm() {
            setTitle("");
            setContent("");
            setEditingId(null);
          }

          function handleSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();

            if (!title.trim() || !content.trim()) {
              return;
            }

            if (editingId !== null) {
              setNotes((current) =>
                current.map((note) =>
                  note.id === editingId ? { ...note, title: title.trim(), content: content.trim() } : note
                )
              );
              resetForm();
              return;
            }

            setNotes((current) => [
              {
                id: Date.now(),
                title: title.trim(),
                content: content.trim(),
              },
              ...current,
            ]);
            resetForm();
          }

          function handleEdit(note: Note) {
            setEditingId(note.id);
            setTitle(note.title);
            setContent(note.content);
          }

          function handleDelete(noteId: number) {
            setNotes((current) => current.filter((note) => note.id !== noteId));
            if (editingId === noteId) {
              resetForm();
            }
          }

          return (
            <main style={{ display: "grid", gap: "1.5rem" }}>
              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
                <h1 style={{ marginTop: 0 }}>Notes Workspace</h1>
                <p style={{ color: "#4b5563" }}>
                  Capture ideas, edit them in place, and remove stale notes without leaving the module.
                </p>

                <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem", marginTop: "1rem", maxWidth: "560px" }}>
                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    type="text"
                    placeholder="Note title"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <textarea
                    value={content}
                    onChange={(event) => setContent(event.target.value)}
                    rows={5}
                    placeholder="Write your note"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px", resize: "vertical" }}
                  />
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <button
                      type="submit"
                      style={{ padding: "0.85rem 1rem", border: "none", borderRadius: "12px", background: "#111827", color: "white", fontWeight: 600 }}
                    >
                      {editingId === null ? "Save note" : "Update note"}
                    </button>
                    <button
                      type="button"
                      onClick={resetForm}
                      style={{ padding: "0.85rem 1rem", border: "1px solid #d1d5db", borderRadius: "12px", background: "white" }}
                    >
                      Clear
                    </button>
                  </div>
                </form>
              </section>

              <section style={{ display: "grid", gap: "1rem" }}>
                {notes.map((note) => (
                  <article key={note.id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start" }}>
                      <div>
                        <h2 style={{ marginTop: 0, marginBottom: "0.5rem" }}>{note.title}</h2>
                        <p style={{ margin: 0, color: "#4b5563", whiteSpace: "pre-wrap" }}>{note.content}</p>
                      </div>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          type="button"
                          onClick={() => handleEdit(note)}
                          style={{ padding: "0.65rem 0.9rem", borderRadius: "10px", border: "1px solid #d1d5db", background: "white" }}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(note.id)}
                          style={{ padding: "0.65rem 0.9rem", borderRadius: "10px", border: "none", background: "#fee2e2", color: "#991b1b" }}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </section>
            </main>
          );
        }
        """
    ).strip() + "\n"


def _render_booking_page() -> str:
    return dedent(
        """
        "use client";

        import { FormEvent, useState } from "react";

        type Booking = {
          id: number;
          customer: string;
          service: string;
          date: string;
          status: string;
        };

        const starterBookings: Booking[] = [
          { id: 1, customer: "Ava Johnson", service: "Brake inspection", date: "2026-04-17", status: "Confirmed" },
          { id: 2, customer: "Marco Smith", service: "Oil change", date: "2026-04-18", status: "Pending" },
        ];

        export default function BookingPage() {
          const [bookings, setBookings] = useState(starterBookings);
          const [customer, setCustomer] = useState("");
          const [service, setService] = useState("");
          const [date, setDate] = useState("");

          function handleSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();
            if (!customer.trim() || !service.trim() || !date) {
              return;
            }

            setBookings((current) => [
              {
                id: Date.now(),
                customer: customer.trim(),
                service: service.trim(),
                date,
                status: "Pending",
              },
              ...current,
            ]);
            setCustomer("");
            setService("");
            setDate("");
          }

          return (
            <main style={{ display: "grid", gap: "1.5rem" }}>
              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
                <h1 style={{ marginTop: 0 }}>Repair Booking Page</h1>
                <p style={{ color: "#4b5563" }}>
                  Capture service appointments, keep the shop schedule visible, and review incoming requests in one place.
                </p>

                <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem", marginTop: "1rem", maxWidth: "560px" }}>
                  <input
                    value={customer}
                    onChange={(event) => setCustomer(event.target.value)}
                    type="text"
                    placeholder="Customer name"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <input
                    value={service}
                    onChange={(event) => setService(event.target.value)}
                    type="text"
                    placeholder="Requested service"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <input
                    value={date}
                    onChange={(event) => setDate(event.target.value)}
                    type="date"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <button
                    type="submit"
                    style={{ width: "fit-content", padding: "0.85rem 1rem", border: "none", borderRadius: "12px", background: "#111827", color: "white", fontWeight: 600 }}
                  >
                    Add booking
                  </button>
                </form>
              </section>

              <section style={{ display: "grid", gap: "1rem" }}>
                {bookings.map((booking) => (
                  <article key={booking.id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                      <div>
                        <h2 style={{ marginTop: 0, marginBottom: "0.35rem" }}>{booking.customer}</h2>
                        <p style={{ margin: 0, color: "#4b5563" }}>{booking.service}</p>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <p style={{ margin: 0, fontWeight: 600 }}>{booking.date}</p>
                        <span style={{ display: "inline-block", marginTop: "0.35rem", padding: "0.3rem 0.6rem", borderRadius: "999px", background: "#e0f2fe", color: "#0c4a6e", fontSize: "0.85rem" }}>
                          {booking.status}
                        </span>
                      </div>
                    </div>
                  </article>
                ))}
              </section>
            </main>
          );
        }
        """
    ).strip() + "\n"


def _render_vendor_page() -> str:
    return dedent(
        """
        "use client";

        import { useState } from "react";

        const starterVendors = [
          { name: "Northstar Parts", price: 1200, leadTime: "3 days", contact: "sales@northstarparts.com" },
          { name: "Precision Supply", price: 980, leadTime: "5 days", contact: "quotes@precisionsupply.com" },
          { name: "Atlas Components", price: 1100, leadTime: "2 days", contact: "ops@atlascomponents.com" },
        ];

        export default function VendorDashboard() {
          const [query, setQuery] = useState("");
          const normalized = query.trim().toLowerCase();
          const filteredVendors = normalized
            ? starterVendors.filter((vendor) =>
                [vendor.name, vendor.contact, vendor.leadTime].some((value) => value.toLowerCase().includes(normalized))
              )
            : starterVendors;

          return (
            <main style={{ display: "grid", gap: "1.5rem" }}>
              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
                <h1 style={{ marginTop: 0 }}>Vendor Dashboard</h1>
                <p style={{ color: "#4b5563" }}>
                  Compare supplier quotes, filter contacts, and track lead times before choosing a vendor.
                </p>

                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  type="text"
                  placeholder="Filter vendors by name, contact, or lead time"
                  style={{ width: "100%", maxWidth: "420px", marginTop: "1rem", padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                />
              </section>

              <section style={{ display: "grid", gap: "1rem" }}>
                {filteredVendors.map((vendor) => (
                  <article key={vendor.name} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                      <div>
                        <h2 style={{ marginTop: 0, marginBottom: "0.35rem" }}>{vendor.name}</h2>
                        <p style={{ margin: 0, color: "#4b5563" }}>{vendor.contact}</p>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <p style={{ margin: 0, fontWeight: 700 }}>${vendor.price.toLocaleString()}</p>
                        <p style={{ margin: 0, color: "#4b5563" }}>{vendor.leadTime}</p>
                      </div>
                    </div>
                  </article>
                ))}
              </section>
            </main>
          );
        }
        """
    ).strip() + "\n"


def _render_login_page() -> str:
    return dedent(
        """
        export default function LoginPage() {
          return (
            <main style={{ display: "grid", gap: "1.5rem" }}>
              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem", maxWidth: "520px" }}>
                <h1 style={{ marginTop: 0 }}>Login Page</h1>
                <p style={{ color: "#4b5563" }}>
                  Add a simple sign-in entry point for your project and keep the rest of the app focused on authenticated work.
                </p>

                <form style={{ display: "grid", gap: "0.85rem", marginTop: "1rem" }}>
                  <input
                    type="email"
                    placeholder="Email address"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    style={{ padding: "0.85rem", border: "1px solid #d1d5db", borderRadius: "12px" }}
                  />
                  <button
                    type="submit"
                    style={{ width: "fit-content", padding: "0.85rem 1rem", border: "none", borderRadius: "12px", background: "#111827", color: "white", fontWeight: 600 }}
                  >
                    Sign in
                  </button>
                </form>
              </section>
            </main>
          );
        }
        """
    ).strip() + "\n"


def _render_dashboard_page() -> str:
    return dedent(
        """
        const metrics = [
          { label: "New requests", value: 28, tone: "#2563eb" },
          { label: "Open builds", value: 8, tone: "#059669" },
          { label: "Issues found", value: 3, tone: "#dc2626" },
          { label: "Deploy ready", value: 5, tone: "#7c3aed" },
        ];

        const chartSeries = [
          { label: "Mon", value: 42 },
          { label: "Tue", value: 55 },
          { label: "Wed", value: 37 },
          { label: "Thu", value: 68 },
          { label: "Fri", value: 61 },
        ];

        export default function DashboardPage() {
          return (
            <main style={{ display: "grid", gap: "1.5rem" }}>
              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
                <h1 style={{ marginTop: 0 }}>Operations Dashboard</h1>
                <p style={{ color: "#4b5563" }}>
                  Track the health of the current project with summary cards and a lightweight activity chart.
                </p>
              </section>

              <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
                {metrics.map((metric) => (
                  <article key={metric.label} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1rem" }}>
                    <p style={{ marginTop: 0, marginBottom: "0.5rem", color: "#6b7280" }}>{metric.label}</p>
                    <p style={{ margin: 0, fontSize: "2rem", fontWeight: 700, color: metric.tone }}>{metric.value}</p>
                  </article>
                ))}
              </section>

              <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}>
                <h2 style={{ marginTop: 0 }}>Activity trend</h2>
                <div style={{ display: "grid", gap: "0.85rem", marginTop: "1rem" }}>
                  {chartSeries.map((item) => (
                    <div key={item.label} style={{ display: "grid", gap: "0.4rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </div>
                      <div style={{ height: "12px", borderRadius: "999px", background: "#e5e7eb", overflow: "hidden" }}>
                        <div style={{ width: `${item.value}%`, height: "100%", background: "#2563eb" }} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </main>
          );
        }
        """
    ).strip() + "\n"


def _render_generic_page(instruction: str) -> str:
    summary_literal = json.dumps(instruction.strip() or "Generated module request")
    return dedent(
        f"""
        const requestSummary = {summary_literal};

        export default function GeneratedModulePage() {{
          return (
            <main style={{{{ display: "grid", gap: "1.5rem" }}}}>
              <section style={{{{ background: "white", border: "1px solid #e5e7eb", borderRadius: "16px", padding: "1.5rem" }}}}>
                <h1 style={{{{ marginTop: 0 }}}}>Generated Module</h1>
                <p style={{{{ color: "#4b5563" }}}}>
                  Builder Core created a starter module for this request:
                </p>
                <blockquote style={{{{ margin: 0, padding: "1rem", borderRadius: "12px", background: "#f9fafb", border: "1px solid #e5e7eb" }}}}>
                  {{requestSummary}}
                </blockquote>
              </section>
            </main>
          );
        }}
        """
    ).strip() + "\n"


def render_module_files(module_key: str, instruction: str) -> tuple[str, str]:
    if module_key == "notes_page":
        return (
            _render_notes_page(),
            dedent(
                """
                Suggested backend routes for notes:
                GET /notes
                POST /notes
                PUT /notes/{id}
                DELETE /notes/{id}
                """
            ).strip()
            + "\n",
        )

    if module_key == "booking_page":
        return (
            _render_booking_page(),
            dedent(
                """
                Suggested backend routes for bookings:
                GET /bookings
                POST /bookings
                PUT /bookings/{id}
                DELETE /bookings/{id}
                """
            ).strip()
            + "\n",
        )

    if module_key == "vendor_dashboard":
        return (
            _render_vendor_page(),
            dedent(
                """
                Suggested backend routes for vendors:
                GET /vendors
                POST /vendors
                GET /vendors/{id}
                PUT /vendors/{id}
                DELETE /vendors/{id}
                """
            ).strip()
            + "\n",
        )

    if module_key == "login_page":
        return (
            _render_login_page(),
            dedent(
                """
                Suggested backend routes for auth:
                POST /login
                POST /logout
                GET /session
                """
            ).strip()
            + "\n",
        )

    if module_key == "dashboard_page":
        return (
            _render_dashboard_page(),
            dedent(
                """
                Suggested backend routes for dashboard:
                GET /dashboard/summary
                GET /dashboard/stats
                """
            ).strip()
            + "\n",
        )

    return (
        _render_generic_page(instruction),
        dedent(
            """
            Suggested backend routes:
            GET /module
            POST /module
            """
        ).strip()
        + "\n",
    )


def generate_module_files(project_name: str, module_key: str, instruction: str) -> list[str]:
    ensure_project_scaffold(project_name)
    blueprint = MODULE_BLUEPRINTS.get(module_key, MODULE_BLUEPRINTS["generic_module"])
    route_dir = blueprint["route_path"].strip("/") or "module"
    page_code, api_text = render_module_files(module_key, instruction)

    return [
        write_text_file(app_root(project_name) / route_dir / "page.tsx", page_code),
        write_text_file(app_root(project_name) / route_dir / "api.txt", api_text),
    ]


def list_project_files(project_name: str) -> list[str]:
    root = project_root(project_name, create=False)
    if not root.exists():
        return []
    return sorted(str(path) for path in root.rglob("*") if path.is_file())


def inspect_project(project_name: str) -> dict[str, Any]:
    root = project_root(project_name, create=False)
    registry = read_registry(project_name)
    files = list_project_files(project_name)

    routes: set[str] = set()
    app_dir = root / "app"
    if app_dir.exists():
        for page in app_dir.rglob("page.tsx"):
            relative = page.relative_to(app_dir)
            if relative.parent == Path("."):
                routes.add("/")
            else:
                routes.add("/" + str(relative.parent).replace("\\", "/"))

    manifest_files = []
    if root.exists():
        manifest_files = sorted(str(path) for path in root.glob("*_manifest.json"))

    if not routes:
        routes.add("/")

    return {
        "project_root": str(root),
        "modules": registry.get("modules", []),
        "routes": sorted(routes),
        "files": files[:25],
        "manifest_files": manifest_files,
        "summary": {
            "file_count": len(files),
            "module_count": len(registry.get("modules", [])),
            "manifest_count": len(manifest_files),
        },
    }


def get_run_info(project_name: str) -> dict[str, Any]:
    ensure_project_scaffold(project_name)
    root = project_root(project_name)
    frontend_public_url = os.getenv("FRONTEND_PUBLIC_URL", "").strip()
    url_hint = "Generated apps usually run on http://localhost:3000."
    if frontend_public_url:
        url_hint = f"Builder Core frontend is live at {frontend_public_url}."
    return {
        "project_name": project_name,
        "project_path": str(root),
        "run_script": str(root / "run_project.sh"),
        "windows_run_script": str(root / "run_project.ps1"),
        "commands": [
            f'cd "{root}"',
            "npm install",
            "npm run dev",
        ],
        "url_hint": url_hint,
    }
