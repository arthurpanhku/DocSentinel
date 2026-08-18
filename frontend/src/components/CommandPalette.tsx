import * as Dialog from "@radix-ui/react-dialog";
import { ArrowRight, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { cn } from "../lib/utils";
import { navigationItems } from "../navigation";
import { IconButton } from "./ui";

export function CommandPalette({
  open,
  onOpenChange
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return navigationItems;
    return navigationItems.filter((item) =>
      [item.label, item.description, item.group, ...item.keywords]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [query]);

  function go(to: string) {
    navigate(to);
    onOpenChange(false);
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-[#020408]/75 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-[14vh] z-50 w-[min(92vw,640px)] -translate-x-1/2 overflow-hidden rounded-2xl border border-line bg-panel shadow-command">
          <Dialog.Title className="sr-only">Search navigation</Dialog.Title>
          <Dialog.Description className="sr-only">
            Find and open a DocSentinel workspace.
          </Dialog.Description>
          <div className="flex items-center gap-3 border-b border-line px-4">
            <Search className="h-5 w-5 shrink-0 text-muted" aria-hidden="true" />
            <input
              autoFocus
              aria-label="Search navigation"
              className="h-14 min-w-0 flex-1 bg-transparent text-sm text-text outline-none placeholder:text-muted"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages, tools, and workflows..."
              value={query}
            />
            <Dialog.Close asChild>
              <IconButton
                className="h-8 w-8 border-0 bg-transparent"
                label="Close search"
              >
                <X aria-hidden="true" />
              </IconButton>
            </Dialog.Close>
          </div>
          <div className="max-h-[min(58vh,520px)] overflow-y-auto p-2">
            {filtered.length ? (
              filtered.map((item) => {
                const Icon = item.icon;
                return (
                  <Dialog.Close asChild key={item.to}>
                    <button
                      className={cn(
                        "focus-ring group grid w-full grid-cols-[40px_1fr_auto] items-center gap-3 rounded-xl px-3 py-2.5 text-left",
                        "text-muted transition hover:bg-panel2 hover:text-text"
                      )}
                      onClick={() => go(item.to)}
                      type="button"
                    >
                      <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-line bg-canvas text-accent">
                        <Icon className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <span className="min-w-0">
                        <span className="block text-sm font-medium text-text">
                          {item.label}
                        </span>
                        <span className="mt-0.5 block truncate text-xs text-muted">
                          {item.group} · {item.description}
                        </span>
                      </span>
                      <ArrowRight
                        className="h-4 w-4 opacity-0 transition group-hover:opacity-100"
                        aria-hidden="true"
                      />
                    </button>
                  </Dialog.Close>
                );
              })
            ) : (
              <div className="px-4 py-12 text-center">
                <div className="text-sm font-medium text-text">No page found</div>
                <div className="mt-1 text-xs text-muted">
                  Try a workflow, tool, or page name.
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between border-t border-line bg-canvas/60 px-4 py-2 text-[11px] text-muted">
            <span>{filtered.length} destinations</span>
            <span>Press Esc to close</span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
