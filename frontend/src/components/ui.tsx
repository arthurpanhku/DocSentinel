import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes
} from "react";
import { forwardRef } from "react";

import { cn } from "../lib/utils";

export function Card({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-xl border border-line bg-panel shadow-[0_1px_0_rgba(255,255,255,0.025)]",
        className
      )}
      {...props}
    >
      {children}
    </section>
  );
}

export function CardHeader({ title, action, meta }: { title: string; action?: ReactNode; meta?: ReactNode }) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-3 border-b border-line px-4 py-3">
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold tracking-tight text-text">{title}</h2>
        {meta ? <div className="mt-1 text-xs text-muted">{meta}</div> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "default" | "quiet" | "danger" | "success";
  }
>(function Button({ className, variant = "default", ...props }, ref) {
  const variants = {
    default: "border-accent/40 bg-accent text-[#06111f] hover:bg-[#75b4ff]",
    quiet: "border-line bg-panel2 text-text hover:border-muted/40 hover:bg-[#1d2430]",
    danger: "border-bad/35 bg-bad/12 text-bad hover:bg-bad/18",
    success: "border-good/35 bg-good/12 text-good hover:bg-good/18"
  };
  return (
    <button
      ref={ref}
      className={cn(
        "focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-lg border px-3.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});

export function Tooltip({
  label,
  children
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          sideOffset={6}
          className="z-50 rounded border border-line bg-panel2 px-2 py-1 text-xs text-text shadow-command"
        >
          {label}
          <TooltipPrimitive.Arrow className="fill-line" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}

export const IconButton = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    label: string;
    children: ReactNode;
  }
>(function IconButton({ label, className, children, ...props }, ref) {
  return (
    <Tooltip label={label}>
      <button
        ref={ref}
        aria-label={label}
        className={cn(
          "focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-line bg-panel text-muted transition hover:border-muted/40 hover:bg-panel2 hover:text-text disabled:cursor-not-allowed disabled:opacity-50 [&_svg]:h-4 [&_svg]:w-4",
          className
        )}
        {...props}
      >
        {children}
      </button>
    </Tooltip>
  );
});

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "focus-ring h-10 w-full rounded-lg border border-line bg-canvas px-3 text-sm text-text transition placeholder:text-muted hover:border-muted/40",
        className
      )}
      {...props}
    />
  );
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "focus-ring h-10 w-full rounded-lg border border-line bg-canvas px-3 text-sm text-text transition hover:border-muted/40",
        className
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "focus-ring min-h-24 w-full resize-y rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm leading-5 text-text transition placeholder:text-muted hover:border-muted/40",
        className
      )}
      {...props}
    />
  );
}

export function Badge({
  children,
  tone = "neutral",
  className
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "warn" | "bad" | "accent";
  className?: string;
}) {
  const tones = {
    neutral: "border-line bg-panel2 text-muted",
    good: "border-good/35 bg-good/10 text-good",
    warn: "border-warn/35 bg-warn/10 text-warn",
    bad: "border-bad/35 bg-bad/10 text-bad",
    accent: "border-accent/35 bg-accent/10 text-accent"
  };
  return (
    <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 px-4 py-10 text-center text-sm text-muted">
      <div className="max-w-sm leading-5">{title}</div>
      {action}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-1.5 text-xs font-medium text-muted">
      <span>{label}</span>
      {children}
    </label>
  );
}

export function ErrorNote({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="rounded-md border border-bad/30 bg-bad/10 px-3 py-2 text-sm text-bad"
    >
      {message}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div className="min-w-0">
        <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-accent">
          DocSentinel workspace
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-text">{title}</h1>
        {description ? (
          <p className="mt-1.5 max-w-3xl text-sm leading-6 text-muted">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
