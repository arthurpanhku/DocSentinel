import { clsx, type ClassValue } from "clsx";

export function cn(...values: ClassValue[]) {
  return clsx(values);
}

export function formatDate(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function severityRank(severity?: string | null) {
  return { critical: 4, high: 3, medium: 2, low: 1, info: 0 }[
    (severity || "").toLowerCase() as "critical" | "high" | "medium" | "low" | "info"
  ] ?? 0;
}

export function compactId(id?: string | null) {
  if (!id) return "";
  return id.length > 12 ? `${id.slice(0, 8)}...${id.slice(-4)}` : id;
}

export function splitLines(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
