import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes
} from "react";

import { cn } from "../lib/utils";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cn("rounded-md border border-line bg-panel", className)}>{children}</section>;
}

export function CardHeader({ title, action, meta }: { title: string; action?: ReactNode; meta?: ReactNode }) {
  return (
    <div className="flex min-h-12 items-center justify-between gap-3 border-b border-line px-4 py-3">
      <div className="min-w-0">
        <h2 className="truncate text-sm font-medium text-text">{title}</h2>
        {meta ? <div className="mt-1 text-xs text-muted">{meta}</div> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "quiet" | "danger" | "success" }) {
  const variants = {
    default: "border-accent/35 bg-accent/12 text-accent hover:bg-accent/18",
    quiet: "border-line bg-panel2 text-text hover:bg-[#1a2028]",
    danger: "border-bad/35 bg-bad/12 text-bad hover:bg-bad/18",
    success: "border-good/35 bg-good/12 text-good hover:bg-good/18"
  };
  return (
    <button
      className={cn(
        "focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md border px-3 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

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

export function IconButton({
  label,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
}) {
  return (
    <Tooltip label={label}>
      <button
        aria-label={label}
        className={cn(
          "focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-line bg-panel text-muted transition hover:bg-panel2 hover:text-text disabled:cursor-not-allowed disabled:opacity-50 [&_svg]:h-4 [&_svg]:w-4",
          className
        )}
        {...props}
      >
        {children}
      </button>
    </Tooltip>
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "focus-ring h-9 w-full rounded-md border border-line bg-[#0d1117] px-3 text-sm text-text placeholder:text-muted",
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
        "focus-ring h-9 w-full rounded-md border border-line bg-[#0d1117] px-3 text-sm text-text",
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
        "focus-ring min-h-24 w-full resize-y rounded-md border border-line bg-[#0d1117] px-3 py-2 text-sm text-text placeholder:text-muted",
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
    <span className={cn("inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center gap-3 px-4 py-8 text-center text-sm text-muted">
      <div>{title}</div>
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
    <div className="flex min-h-14 flex-col justify-between gap-3 border-b border-line pb-4 sm:flex-row sm:items-end">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold text-text">{title}</h1>
        {description ? (
          <p className="mt-1 max-w-3xl text-sm leading-5 text-muted">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
