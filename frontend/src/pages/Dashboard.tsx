import { ArrowRight, FileCheck2, RefreshCw, ShieldAlert, TimerReset } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { StatusBadge, taskTitle } from "../components/domain";
import { Badge, Button, Card, CardHeader, EmptyState, ErrorNote } from "../components/ui";
import { getActivity, getHealth, getLLMConfig, getRemediations, listAssessments } from "../lib/api";
import { compactId, formatDate, severityRank } from "../lib/utils";
import type { ActivityEntry, AssessmentTask, LLMConfig, TrackedRemediation } from "../types";

export default function Dashboard() {
  const [tasks, setTasks] = useState<AssessmentTask[]>([]);
  const [health, setHealth] = useState<string>("checking");
  const [llm, setLlm] = useState<LLMConfig | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [remediations, setRemediations] = useState<TrackedRemediation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [healthResult, llmResult, taskResult] = await Promise.all([
        getHealth().catch(() => ({ status: "down" })),
        getLLMConfig().catch(() => null),
        listAssessments({ limit: 200 })
      ]);
      setHealth(healthResult.status);
      setLlm(llmResult);
      setTasks(taskResult);

      const recent = taskResult.slice(0, 4);
      const [activityResult, remediationResult] = await Promise.all([
        Promise.all(recent.map((task) => getActivity(task.task_id).catch(() => []))),
        Promise.all(recent.map((task) => getRemediations(task.task_id).catch(() => [])))
      ]);
      setActivity(activityResult.flat().slice(-12).reverse());
      setRemediations(remediationResult.flat());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const stats = useMemo(() => {
    const pendingReview = tasks.filter((task) => ["review_pending", "escalated"].includes(task.status)).length;
    const highRisk = tasks.reduce((count, task) => {
      const risk = task.report?.risk_items?.some((item) => severityRank(item.severity) >= 3);
      return count + (risk ? 1 : 0);
    }, 0);
    const openRemediations = remediations.filter((item) => !["verified", "closed"].includes(item.tracking.status)).length;
    return { pendingReview, highRisk, openRemediations };
  }, [remediations, tasks]);

  const newest = [...tasks].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 8);

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-xl font-semibold text-text">Command Center</h1>
          <p className="mt-1 text-sm text-muted">Assessments, review queues, remediation work, and system status.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={health === "ok" ? "good" : "bad"}>API {health}</Badge>
          <Badge tone="accent">{llm ? `${llm.provider}: ${llm.model}` : "LLM unknown"}</Badge>
          <Button onClick={() => void load()} variant="quiet" disabled={loading}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Link to="/assessments">
            <Button>
              <FileCheck2 className="h-4 w-4" />
              New assessment
            </Button>
          </Link>
        </div>
      </div>

      <ErrorNote message={error} />

      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Total tasks" value={tasks.length} icon={<FileCheck2 className="h-4 w-4" />} />
        <Metric label="Needs review" value={stats.pendingReview} icon={<TimerReset className="h-4 w-4" />} tone="warn" />
        <Metric label="High risk tasks" value={stats.highRisk} icon={<ShieldAlert className="h-4 w-4" />} tone="bad" />
        <Metric label="Open remediations" value={stats.openRemediations} icon={<ArrowRight className="h-4 w-4" />} tone="accent" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
        <Card>
          <CardHeader title="Recent Assessments" />
          {newest.length ? (
            <div className="divide-y divide-line">
              {newest.map((task) => (
                <Link key={task.task_id} to="/assessments" className="grid gap-2 px-4 py-3 transition hover:bg-panel2 md:grid-cols-[1fr_auto]">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-text">{taskTitle(task)}</div>
                    <div className="mt-1 text-xs text-muted">
                      {compactId(task.task_id)} · {formatDate(task.created_at)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.report?.phase ? <Badge tone="accent">{task.report.phase}</Badge> : null}
                    <StatusBadge status={task.status} />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No assessments yet." action={<Link to="/assessments"><Button>Submit documents</Button></Link>} />
          )}
        </Card>

        <Card>
          <CardHeader title="Activity" />
          {activity.length ? (
            <div className="divide-y divide-line">
              {activity.map((entry, index) => (
                <div key={`${entry.type}-${entry.at}-${index}`} className="px-4 py-3">
                  <div className="text-sm text-text">{entry.message || entry.type.replace(/_/g, " ")}</div>
                  <div className="mt-1 text-xs text-muted">
                    {entry.action ? `${entry.action} · ` : ""}
                    {entry.status ? `${entry.status} · ` : ""}
                    {formatDate(entry.at)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No recent activity." />
          )}
        </Card>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  icon,
  tone = "neutral"
}: {
  label: string;
  value: number;
  icon: ReactNode;
  tone?: "neutral" | "warn" | "bad" | "accent";
}) {
  const color = {
    neutral: "text-text",
    warn: "text-warn",
    bad: "text-bad",
    accent: "text-accent"
  }[tone];
  return (
    <Card className="p-4">
      <div className={`mb-3 ${color}`}>{icon}</div>
      <div className="text-2xl font-semibold text-text">{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </Card>
  );
}
