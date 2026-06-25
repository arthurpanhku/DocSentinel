import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import {
  BrainCircuit,
  Database,
  Gauge,
  ListChecks,
  Menu,
  Network,
  Settings,
  ShieldCheck,
  X,
  type LucideIcon
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { getHealth } from "../lib/api";
import { cn } from "../lib/utils";
import { Badge, IconButton } from "./ui";

type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
};

const navItems: NavItem[] = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/assessments", label: "Assessments", icon: ListChecks },
  { to: "/kb", label: "Knowledge Base", icon: Database },
  { to: "/skills", label: "Skills", icon: BrainCircuit },
  { to: "/integrations", label: "Agent Integrations", icon: Network },
  { to: "/settings", label: "Settings", icon: Settings }
];

function Brand() {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-accent/30 bg-accent/10 text-accent">
        <ShieldCheck className="h-4 w-4" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="truncate text-sm font-semibold text-text">DocSentinel</div>
        <div className="truncate text-[11px] text-muted">Trustworthy review</div>
      </div>
    </div>
  );
}

function Navigation({ mobile = false }: { mobile?: boolean }) {
  return (
    <nav aria-label="Primary navigation" className="space-y-1 p-3">
      {navItems.map((item) => {
        const Icon = item.icon;
        const link = (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "focus-ring flex h-9 items-center gap-3 rounded-md px-3 text-sm transition",
                isActive
                  ? "bg-panel2 text-text"
                  : "text-muted hover:bg-panel2/70 hover:text-text"
              )
            }
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            <span>{item.label}</span>
          </NavLink>
        );

        return mobile ? (
          <Dialog.Close key={item.to} asChild>
            {link}
          </Dialog.Close>
        ) : (
          link
        );
      })}
    </nav>
  );
}

function HealthIndicator() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000
  });
  const online = health.data?.status === "ok";

  return (
    <div className="flex items-center gap-2 text-xs text-muted">
      <span
        aria-hidden="true"
        className={cn(
          "h-2 w-2 rounded-full",
          health.isPending ? "bg-muted" : online ? "bg-good" : "bg-bad"
        )}
      />
      <span>{health.isPending ? "Checking API" : online ? "API connected" : "API unavailable"}</span>
    </div>
  );
}

export default function Layout() {
  return (
    <div className="min-h-screen bg-canvas">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-56 border-r border-line bg-canvas lg:flex lg:flex-col">
        <div className="flex h-14 items-center border-b border-line px-4">
          <Brand />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <Navigation />
        </div>
        <div className="border-t border-line px-4 py-3">
          <HealthIndicator />
        </div>
      </aside>

      <div className="lg:pl-56">
        <header className="sticky top-0 z-10 border-b border-line bg-canvas/95 backdrop-blur">
          <div className="flex h-14 items-center justify-between gap-3 px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <div className="lg:hidden">
                <Dialog.Root>
                  <Dialog.Trigger asChild>
                    <IconButton label="Open navigation">
                      <Menu aria-hidden="true" />
                    </IconButton>
                  </Dialog.Trigger>
                  <Dialog.Portal>
                    <Dialog.Overlay className="fixed inset-0 z-40 bg-black/55" />
                    <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-[min(86vw,280px)] flex-col border-r border-line bg-canvas shadow-command">
                      <Dialog.Title className="sr-only">Navigation</Dialog.Title>
                      <div className="flex h-14 items-center justify-between border-b border-line px-4">
                        <Brand />
                        <Dialog.Close asChild>
                          <IconButton label="Close navigation">
                            <X aria-hidden="true" />
                          </IconButton>
                        </Dialog.Close>
                      </div>
                      <div className="min-h-0 flex-1 overflow-y-auto">
                        <Navigation mobile />
                      </div>
                      <div className="border-t border-line px-4 py-3">
                        <HealthIndicator />
                      </div>
                    </Dialog.Content>
                  </Dialog.Portal>
                </Dialog.Root>
              </div>
              <div className="hidden lg:block">
                <div className="text-xs text-muted">Workspace</div>
                <div className="text-sm font-medium text-text">Local review</div>
              </div>
              <div className="lg:hidden">
                <div className="truncate text-sm font-semibold text-text">DocSentinel</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge>Local-first</Badge>
              <div className="hidden sm:block">
                <HealthIndicator />
              </div>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] px-4 py-5 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
