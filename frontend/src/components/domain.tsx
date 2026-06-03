import type { AssessmentTask, Severity, TaskStatus } from "../types";
import { Badge } from "./ui";

export function statusTone(status: TaskStatus): "neutral" | "good" | "warn" | "bad" | "accent" {
  if (status === "approved" || status === "completed") return "good";
  if (status === "review_pending" || status === "escalated" || status === "running") return "warn";
  if (status === "failed" || status === "rejected") return "bad";
  return "neutral";
}

export function severityTone(severity?: string | null): "neutral" | "good" | "warn" | "bad" | "accent" {
  if (severity === "critical" || severity === "high") return "bad";
  if (severity === "medium") return "warn";
  if (severity === "low") return "good";
  return "neutral";
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  return <Badge tone={statusTone(status)}>{status.replace("_", " ")}</Badge>;
}

export function SeverityBadge({ severity }: { severity?: Severity | string | null }) {
  if (!severity) return null;
  return <Badge tone={severityTone(severity)}>{severity}</Badge>;
}

export function taskTitle(task: AssessmentTask) {
  return task.report?.summary || task.error_message || "Assessment draft pending";
}
