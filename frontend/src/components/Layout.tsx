import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronRight,
  FilePlus2,
  Menu,
  Search,
  ShieldCheck,
  UserRound,
  X
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { getHealth } from "../lib/api";
import { getGovernanceSession } from "../lib/governanceApi";
import { cn } from "../lib/utils";
import {
  navigationGroups,
  navigationItemForPath,
  type NavigationItem
} from "../navigation";
import { CommandPalette } from "./CommandPalette";
import { Badge, Button, IconButton } from "./ui";

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link
      aria-label={compact ? "DocSentinel home" : undefined}
      className="focus-ring flex min-w-0 items-center gap-3 rounded-lg"
      to="/"
    >
      <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-accent shadow-[inset_0_0_18px_rgba(88,166,255,0.08)]">
        <ShieldCheck className="h-4 w-4" aria-hidden="true" />
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border-2 border-canvas bg-good" />
      </div>
      {!compact ? (
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold tracking-tight text-text">
            DocSentinel
          </div>
          <div className="truncate text-[11px] text-muted">
            Security review workspace
          </div>
        </div>
      ) : null}
    </Link>
  );
}

function NavigationLink({
  item,
  mobile
}: {
  item: NavigationItem;
  mobile: boolean;
}) {
  const Icon = item.icon;
  const link = (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      className={({ isActive }) =>
        cn(
          "focus-ring group relative flex min-h-10 items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
          isActive
            ? "bg-accent/10 font-medium text-text"
            : "text-muted hover:bg-panel2/80 hover:text-text"
        )
      }
    >
      {({ isActive }) => (
        <>
          <span
            aria-hidden="true"
            className={cn(
              "absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent transition-opacity",
              isActive ? "opacity-100" : "opacity-0"
            )}
          />
          <Icon
            className={cn(
              "h-4 w-4 shrink-0 transition",
              isActive ? "text-accent" : "text-muted group-hover:text-text"
            )}
            aria-hidden="true"
          />
          <span className="truncate">{item.label}</span>
        </>
      )}
    </NavLink>
  );

  return mobile ? <Dialog.Close asChild>{link}</Dialog.Close> : link;
}

function Navigation({ mobile = false }: { mobile?: boolean }) {
  return (
    <nav aria-label="Primary navigation" className="space-y-5 px-3 py-4">
      {navigationGroups.map((group) => (
        <div key={group.label}>
          <div className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted/70">
            {group.label}
          </div>
          <div className="space-y-0.5">
            {group.items.map((item) => (
              <NavigationLink
                item={item}
                key={item.to}
                mobile={mobile}
              />
            ))}
          </div>
        </div>
      ))}
    </nav>
  );
}

function HealthIndicator({ detailed = false }: { detailed?: boolean }) {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000
  });
  const online = health.data?.status === "ok";
  const label = health.isPending
    ? "Checking API"
    : online
      ? "All systems operational"
      : "API unavailable";

  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span className="relative flex h-2.5 w-2.5 shrink-0" aria-hidden="true">
        {online ? (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-good opacity-30" />
        ) : null}
        <span
          className={cn(
            "relative inline-flex h-2.5 w-2.5 rounded-full",
            health.isPending ? "bg-muted" : online ? "bg-good" : "bg-bad"
          )}
        />
      </span>
      <div className="min-w-0">
        <div className="truncate text-xs text-text">{label}</div>
        {detailed ? (
          <div className="mt-0.5 text-[10px] text-muted">
            Local API · checked every 30s
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SidebarFooter() {
  const session = getGovernanceSession();
  return (
    <div className="space-y-2 border-t border-line p-3">
      <div className="rounded-xl border border-line bg-panel p-3">
        <HealthIndicator detailed />
      </div>
      <Link
        className="focus-ring flex items-center gap-3 rounded-xl px-3 py-2 text-muted transition hover:bg-panel hover:text-text"
        to={session ? "/governance" : "/login"}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-panel">
          <UserRound className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block truncate text-xs font-medium text-text">
            {session?.user.full_name || session?.user.username || "Governance access"}
          </span>
          <span className="mt-0.5 block truncate text-[10px] text-muted">
            {session ? session.user.role : "Sign in to review controls"}
          </span>
        </span>
      </Link>
    </div>
  );
}

function MobileNavigation() {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <IconButton label="Open navigation">
          <Menu aria-hidden="true" />
        </IconButton>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-[#020408]/75 backdrop-blur-sm" />
        <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-[min(88vw,300px)] flex-col border-r border-line bg-canvas shadow-command">
          <Dialog.Title className="sr-only">Navigation</Dialog.Title>
          <Dialog.Description className="sr-only">
            Open a DocSentinel workspace.
          </Dialog.Description>
          <div className="flex h-16 items-center justify-between border-b border-line px-4">
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
          <SidebarFooter />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export default function Layout() {
  const location = useLocation();
  const current = navigationItemForPath(location.pathname);
  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-canvas">
      <a
        className="focus-ring fixed left-3 top-3 z-[70] -translate-y-20 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-canvas transition focus:translate-y-0"
        href="#main-content"
      >
        Skip to main content
      </a>

      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-line bg-canvas/95 lg:flex lg:flex-col">
        <div className="flex h-16 items-center border-b border-line px-4">
          <Brand />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <Navigation />
        </div>
        <SidebarFooter />
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-line bg-canvas/88 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <div className="lg:hidden">
                <MobileNavigation />
              </div>
              <div className="hidden min-w-0 items-center gap-2 sm:flex">
                <span className="text-xs text-muted">{current.group}</span>
                <ChevronRight className="h-3 w-3 text-muted/60" aria-hidden="true" />
                <span className="truncate text-xs font-medium text-text">
                  {current.label}
                </span>
              </div>
              <div className="sm:hidden">
                <Brand compact />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                aria-label="Search navigation"
                className="focus-ring hidden h-10 w-[min(30vw,280px)] items-center gap-2 rounded-lg border border-line bg-panel px-3 text-left text-sm text-muted transition hover:border-muted/40 hover:bg-panel2 sm:flex"
                onClick={() => setCommandOpen(true)}
                type="button"
              >
                <Search className="h-4 w-4" aria-hidden="true" />
                <span className="min-w-0 flex-1 truncate">Search or jump to...</span>
                <kbd className="rounded border border-line bg-canvas px-1.5 py-0.5 font-sans text-[10px] text-muted">
                  ⌘K
                </kbd>
              </button>
              <IconButton
                className="sm:hidden"
                label="Search navigation"
                onClick={() => setCommandOpen(true)}
              >
                <Search aria-hidden="true" />
              </IconButton>
              {current.to !== "/assessments" ? (
                <Link className="hidden sm:block" to="/assessments#new-assessment">
                  <Button>
                    <FilePlus2 className="h-4 w-4" aria-hidden="true" />
                    New assessment
                  </Button>
                </Link>
              ) : null}
              <Badge className="hidden xl:inline-flex" tone="accent">
                Local workspace
              </Badge>
            </div>
          </div>
        </header>

        <main
          className="mx-auto w-full max-w-[1520px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8"
          id="main-content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>

      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
