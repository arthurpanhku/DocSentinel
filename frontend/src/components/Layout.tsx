import {
  Activity,
  BrainCircuit,
  Database,
  Gauge,
  ListChecks,
  Settings,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { cn } from "../lib/utils";

const navItems = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/assessments", label: "Assessments", icon: ListChecks },
  { to: "/kb", label: "Knowledge Base", icon: Database },
  { to: "/skills", label: "Skills", icon: BrainCircuit },
  { to: "/settings", label: "Settings", icon: Settings }
];

export default function Layout() {
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-line bg-canvas/95 lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-line px-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-accent/25 bg-accent/10 text-accent">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-text">DocSentinel</div>
            <div className="truncate text-xs text-muted">SSDLC security console</div>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex h-10 items-center gap-3 rounded-md px-3 text-sm transition",
                    isActive ? "bg-panel2 text-text" : "text-muted hover:bg-panel hover:text-text"
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-line p-4 text-xs text-muted">
          <div className="mb-2 flex items-center gap-2 text-text">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            Console preview
          </div>
          <p className="leading-5">Built for local FastAPI hosting at /console.</p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-canvas/85 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3 lg:hidden">
              <ShieldCheck className="h-5 w-5 text-accent" />
              <span className="truncate text-sm font-semibold text-text">DocSentinel</span>
            </div>
            <div className="hidden items-center gap-2 text-xs text-muted lg:flex">
              <Activity className="h-4 w-4 text-accent" />
              Full lifecycle review, KB, and skill operations
            </div>
            <div className="flex items-center gap-1 overflow-x-auto lg:hidden">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    title={item.label}
                    className={({ isActive }) =>
                      cn(
                        "focus-ring flex h-9 w-9 shrink-0 items-center justify-center rounded-md border",
                        isActive ? "border-accent/35 bg-accent/10 text-accent" : "border-line bg-panel text-muted"
                      )
                    }
                  >
                    <Icon className="h-4 w-4" />
                  </NavLink>
                );
              })}
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
