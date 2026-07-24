import { Check, FileUp, MessageSquare, RefreshCw, Send, Shield, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { SeverityBadge, StatusBadge, taskTitle } from "../components/domain";
import { ThreatEvidencePanel } from "../components/ThreatEvidencePanel";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  ErrorNote,
  Field,
  IconButton,
  Input,
  PageHeader,
  Select,
  Textarea
} from "../components/ui";
import {
  addComment,
  getActivity,
  getAssessment,
  getRemediations,
  listAssessments,
  listSkills,
  reviewAssessment,
  submitAssessment,
  updateRemediation
} from "../lib/api";
import { compactId, formatDate, severityRank, splitLines } from "../lib/utils";
import type {
  ActivityEntry,
  AssessmentPhase,
  AssessmentTask,
  RemediationTracking,
  Skill,
  TrackedRemediation
} from "../types";

const phases: AssessmentPhase[] = [
  "auto",
  "requirements",
  "design",
  "development",
  "testing",
  "deployment",
  "operations",
  "full_ssdlc"
];

const statusOptions = [
  { label: "All", value: "" },
  { label: "Needs review", value: "review_pending,escalated" },
  { label: "Running", value: "pending,running" },
  { label: "Closed", value: "approved,rejected,completed,failed" }
];

export default function Assessments() {
  const [tasks, setTasks] = useState<AssessmentTask[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<AssessmentTask | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [remediations, setRemediations] = useState<TrackedRemediation[]>([]);
  const [status, setStatus] = useState("");
  const [assigneeFilter, setAssigneeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadTasks(nextSelectedId = selectedId) {
    setLoading(true);
    setError(null);
    try {
      const result = await listAssessments({
        status: status || undefined,
        assignee: assigneeFilter || undefined,
        limit: 200
      });
      const sorted = [...result].sort((a, b) => {
        const ar = severityRank(a.report?.risk_items?.[0]?.severity);
        const br = severityRank(b.report?.risk_items?.[0]?.severity);
        if (br !== ar) return br - ar;
        return b.created_at.localeCompare(a.created_at);
      });
      setTasks(sorted);
      const preferred = nextSelectedId && sorted.some((task) => task.task_id === nextSelectedId) ? nextSelectedId : sorted[0]?.task_id ?? null;
      setSelectedId(preferred);
      if (preferred) await loadDetail(preferred);
      else {
        setSelected(null);
        setActivity([]);
        setRemediations([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load assessments.");
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(taskId: string) {
    setError(null);
    try {
      const [task, taskActivity, tracked] = await Promise.all([
        getAssessment(taskId),
        getActivity(taskId).catch(() => []),
        getRemediations(taskId).catch(() => [])
      ]);
      setSelected(task);
      setActivity(taskActivity);
      setRemediations(tracked);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load assessment detail.");
    }
  }

  useEffect(() => {
    void listSkills().then(setSkills).catch(() => setSkills([]));
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [status, assigneeFilter]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const files = form.getAll("files").filter((value): value is File => value instanceof File && value.size > 0);
    if (!files.length) {
      setError("Select at least one document.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await submitAssessment({
        files,
        scenarioId: String(form.get("scenario_id") || ""),
        projectId: String(form.get("project_id") || ""),
        phase: String(form.get("phase") || "auto") as AssessmentPhase,
        skillId: String(form.get("skill_id") || ""),
        collaborativeMode: form.get("collaborative_mode") === "on"
      });
      event.currentTarget.reset();
      await loadTasks(created.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assessment submission failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReview(action: "approve" | "reject" | "comment" | "escalate", form: HTMLFormElement) {
    if (!selected) return;
    const body = new FormData(form);
    setBusy(true);
    setError(null);
    try {
      await reviewAssessment(selected.task_id, {
        action,
        comment: String(body.get("review_comment") || ""),
        assignee: String(body.get("review_assignee") || "")
      });
      form.reset();
      await loadTasks(selected.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const content = String(form.get("comment") || "").trim();
    if (!content) return;
    setBusy(true);
    try {
      await addComment(selected.task_id, content);
      event.currentTarget.reset();
      await loadDetail(selected.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comment failed.");
    } finally {
      setBusy(false);
    }
  }

  const summary = useMemo(() => {
    const report = selected?.report;
    return {
      risks: report?.risk_items?.length ?? 0,
      gaps: report?.compliance_gaps?.length ?? 0,
      rems: report?.remediations?.length ?? 0,
      high: report?.risk_items?.filter((risk) => severityRank(risk.severity) >= 3).length ?? 0
    };
  }, [selected]);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Assessments"
        description="Submit project material, inspect evidence-backed drafts, and complete human review."
      />
      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <div className="space-y-4">
        <Card>
          <CardHeader title="Submit Assessment" meta="Files, phase, skill, and review mode." />
          <form onSubmit={handleSubmit} className="space-y-3 p-4">
            <Field label="Documents">
              <Input name="files" type="file" multiple accept=".txt,.md,.pdf,.docx,.xlsx,.pptx" />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <Field label="SSDLC phase">
                <Select name="phase" defaultValue="auto">
                  {phases.map((phase) => <option key={phase} value={phase}>{phase}</option>)}
                </Select>
              </Field>
              <Field label="Skill">
                <Select name="skill_id" defaultValue="ssdlc-design">
                  <option value="">Default</option>
                  {skills.map((skill) => <option key={skill.id} value={skill.id}>{skill.name}</option>)}
                </Select>
              </Field>
            </div>
            <Field label="Scenario">
              <Input name="scenario_id" placeholder="threat-modeling" />
            </Field>
            <Field label="Project">
              <Input name="project_id" placeholder="SNOW-1234 or repo/project" />
            </Field>
            <label className="flex items-center gap-2 text-sm text-muted">
              <input name="collaborative_mode" type="checkbox" defaultChecked className="h-4 w-4 accent-accent" />
              Human review before closure
            </label>
            <Button className="w-full" disabled={busy}>
              <FileUp className="h-4 w-4" />
              Submit
            </Button>
          </form>
        </Card>

        <Card>
          <CardHeader
            title="Queue"
            action={
              <IconButton
                label="Refresh assessment queue"
                onClick={() => void loadTasks()}
                disabled={loading}
              >
                <RefreshCw aria-hidden="true" />
              </IconButton>
            }
          />
          <div className="grid gap-2 border-b border-line p-3">
            <Select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statusOptions.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
            </Select>
            <Input value={assigneeFilter} onChange={(event) => setAssigneeFilter(event.target.value)} placeholder="Filter assignee" />
          </div>
          {tasks.length ? (
            <div className="max-h-[52vh] divide-y divide-line overflow-auto">
              {tasks.map((task) => (
                <button
                  key={task.task_id}
                  onClick={() => {
                    setSelectedId(task.task_id);
                    void loadDetail(task.task_id);
                  }}
                  className={`w-full px-4 py-3 text-left transition hover:bg-panel2 ${selectedId === task.task_id ? "bg-panel2" : ""}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="line-clamp-2 text-sm font-medium text-text">{taskTitle(task)}</div>
                      <div className="mt-1 text-xs text-muted">{compactId(task.task_id)} · {formatDate(task.created_at)}</div>
                    </div>
                    <StatusBadge status={task.status} />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState title={loading ? "Loading queue..." : "No tasks found."} />
          )}
        </Card>
        </div>

        <div className="space-y-4">
        <ErrorNote message={error} />
        {selected ? (
          <>
            <Card>
              <CardHeader
                title="Assessment Detail"
                meta={`${compactId(selected.task_id)} · ${formatDate(selected.created_at)}`}
                action={<StatusBadge status={selected.status} />}
              />
              <div className="space-y-4 p-4">
                <div>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    {selected.report?.phase ? <Badge tone="accent">{selected.report.phase}</Badge> : null}
                    {selected.report?.confidence !== undefined ? <Badge>confidence {selected.report.confidence.toFixed(2)}</Badge> : null}
                    {selected.assignee ? <Badge tone="warn">assignee {selected.assignee}</Badge> : null}
                  </div>
                  <p className="text-sm leading-6 text-text">{selected.report?.summary || "Report is not available yet."}</p>
                  {selected.error_message ? <ErrorNote message={selected.error_message} /> : null}
                </div>
                <div className="grid gap-3 sm:grid-cols-4">
                  <MiniMetric label="Risks" value={summary.risks} />
                  <MiniMetric label="High/Critical" value={summary.high} tone="bad" />
                  <MiniMetric label="Gaps" value={summary.gaps} tone="warn" />
                  <MiniMetric label="Remediations" value={summary.rems} tone="accent" />
                </div>
              </div>
            </Card>

            <ReportSections task={selected} remediations={remediations} onRemediationSaved={() => loadDetail(selected.task_id)} setError={setError} />

            <Card>
              <CardHeader title="Review" meta="Available while task is review pending or escalated." />
              <form
                className="space-y-3 p-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleReview("comment", event.currentTarget);
                }}
              >
                <div className="grid gap-3 md:grid-cols-[1fr_220px]">
                  <Field label="Comment">
                    <Textarea name="review_comment" placeholder="Leave a review note." />
                  </Field>
                  <Field label="Assignee">
                    <Input name="review_assignee" placeholder="security-lead" />
                  </Field>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit" variant="quiet" disabled={busy || !canReview(selected)}>
                    <MessageSquare className="h-4 w-4" />
                    Comment
                  </Button>
                  <Button type="button" variant="success" disabled={busy || !canReview(selected)} onClick={(event) => void handleReview("approve", event.currentTarget.form!)}>
                    <Check className="h-4 w-4" />
                    Approve
                  </Button>
                  <Button type="button" variant="danger" disabled={busy || !canReview(selected)} onClick={(event) => void handleReview("reject", event.currentTarget.form!)}>
                    <X className="h-4 w-4" />
                    Reject
                  </Button>
                  <Button type="button" disabled={busy || !canReview(selected)} onClick={(event) => void handleReview("escalate", event.currentTarget.form!)}>
                    <Shield className="h-4 w-4" />
                    Escalate
                  </Button>
                </div>
              </form>
            </Card>

            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader title="Comments" />
                <div className="space-y-3 p-4">
                  <form onSubmit={handleAddComment} className="flex gap-2">
                    <Input name="comment" placeholder="Add comment" />
                    <IconButton label="Add comment" type="submit" disabled={busy}>
                      <Send aria-hidden="true" />
                    </IconButton>
                  </form>
                  <div className="divide-y divide-line">
                    {selected.comments?.length ? selected.comments.map((comment, index) => (
                      <div key={index} className="py-3 text-sm">
                        <div className="text-text">{String(comment.content || "")}</div>
                        <div className="mt-1 text-xs text-muted">{String(comment.user_id || comment.action || "review")} · {formatDate(String(comment.at || ""))}</div>
                      </div>
                    )) : <EmptyState title="No comments." />}
                  </div>
                </div>
              </Card>
              <Card>
                <CardHeader title="Activity" />
                {activity.length ? (
                  <div className="max-h-96 divide-y divide-line overflow-auto">
                    {[...activity].reverse().map((entry, index) => (
                      <div key={`${entry.at}-${entry.type}-${index}`} className="px-4 py-3 text-sm">
                        <div className="text-text">{entry.message || entry.type.replace(/_/g, " ")}</div>
                        <div className="mt-1 text-xs text-muted">{entry.action || entry.status || entry.owner || ""} {formatDate(entry.at)}</div>
                      </div>
                    ))}
                  </div>
                ) : <EmptyState title="No activity." />}
              </Card>
            </div>
          </>
        ) : (
          <Card>
            <EmptyState title="Select or submit an assessment." />
          </Card>
        )}
        </div>
      </div>
    </div>
  );
}

function canReview(task: AssessmentTask) {
  return task.status === "review_pending" || task.status === "escalated";
}

function MiniMetric({ label, value, tone = "neutral" }: { label: string; value: number; tone?: "neutral" | "bad" | "warn" | "accent" }) {
  const color = { neutral: "text-text", bad: "text-bad", warn: "text-warn", accent: "text-accent" }[tone];
  return (
    <div className="rounded-md border border-line bg-panel2 p-3">
      <div className={`text-xl font-semibold ${color}`}>{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </div>
  );
}

function ReportSections({
  task,
  remediations,
  onRemediationSaved,
  setError
}: {
  task: AssessmentTask;
  remediations: TrackedRemediation[];
  onRemediationSaved: () => void;
  setError: (value: string | null) => void;
}) {
  const report = task.report;
  if (!report) return null;
  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader title="Risks" />
        {report.risk_items.length ? (
          <div className="divide-y divide-line">
            {report.risk_items.map((risk) => (
              <div key={risk.id} className="px-4 py-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-text">{risk.title}</div>
                    <p className="mt-1 text-sm leading-6 text-muted">{risk.description}</p>
                  </div>
                  <SeverityBadge severity={risk.severity} />
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {risk.category ? <Badge>{risk.category}</Badge> : null}
                  {risk.source_ref ? <Badge>{risk.source_ref}</Badge> : null}
                </div>
              </div>
            ))}
          </div>
        ) : <EmptyState title="No risks reported." />}
      </Card>

      <Card>
        <CardHeader title="Compliance Gaps" />
        {report.compliance_gaps.length ? (
          <div className="divide-y divide-line">
            {report.compliance_gaps.map((gap) => (
              <div key={gap.id} className="px-4 py-3">
                <div className="text-sm font-medium text-text">{gap.control_or_clause}</div>
                <p className="mt-1 text-sm leading-6 text-muted">{gap.gap_description}</p>
                {gap.evidence_suggestion ? <p className="mt-2 text-xs text-muted">Evidence: {gap.evidence_suggestion}</p> : null}
              </div>
            ))}
          </div>
        ) : <EmptyState title="No compliance gaps reported." />}
      </Card>

      <Card>
        <CardHeader title="Remediation Tracking" />
        {remediations.length ? (
          <div className="divide-y divide-line">
            {remediations.map((item) => (
              <RemediationRow
                key={item.remediation.id}
                taskId={task.task_id}
                item={item}
                onSaved={onRemediationSaved}
                setError={setError}
              />
            ))}
          </div>
        ) : <EmptyState title="No remediation items." />}
      </Card>

      <Card>
        <CardHeader title="Sources" />
        {report.sources.length ? (
          <div className="grid gap-3 p-4 md:grid-cols-2">
            {report.sources.map((source) => (
              <div key={source.id} className="rounded-md border border-line bg-panel2 p-3">
                <div className="text-xs font-medium text-text">{source.file}{source.page ? `#p${source.page}` : ""}</div>
                <p className="mt-2 text-xs leading-5 text-muted">{source.excerpt}</p>
              </div>
            ))}
          </div>
        ) : <EmptyState title="No citations." />}
      </Card>

      {report.threat_model ? (
        <ThreatEvidencePanel
          threatModel={report.threat_model}
          sources={report.sources}
        />
      ) : null}
      {report.vulnerabilities?.length ? <FutureJson title="Vulnerabilities" value={report.vulnerabilities} /> : null}
      {report.cross_phase_refs?.length ? <FutureJson title="Cross Phase References" value={report.cross_phase_refs} /> : null}
    </div>
  );
}

function RemediationRow({
  taskId,
  item,
  onSaved,
  setError
}: {
  taskId: string;
  item: TrackedRemediation;
  onSaved: () => void;
  setError: (value: string | null) => void;
}) {
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await updateRemediation(taskId, item.remediation.id, {
        status: String(form.get("status") || "open") as RemediationTracking["status"],
        owner: String(form.get("owner") || ""),
        external_ticket: String(form.get("external_ticket") || ""),
        notes: String(form.get("notes") || ""),
        evidence_refs: splitLines(String(form.get("evidence_refs") || ""))
      });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save remediation.");
    }
  }

  return (
    <form onSubmit={save} className="space-y-3 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-text">{item.remediation.action}</div>
          <div className="mt-1 flex flex-wrap gap-2">
            {item.remediation.priority ? <Badge tone="warn">{item.remediation.priority}</Badge> : null}
            <Badge>{item.tracking.status}</Badge>
          </div>
        </div>
        <Button variant="quiet">Save</Button>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <Field label="Status">
          <Select name="status" defaultValue={item.tracking.status}>
            {["open", "in_progress", "resolved", "verified", "closed"].map((value) => <option key={value} value={value}>{value}</option>)}
          </Select>
        </Field>
        <Field label="Owner">
          <Input name="owner" defaultValue={item.tracking.owner || ""} />
        </Field>
        <Field label="Ticket">
          <Input name="external_ticket" defaultValue={item.tracking.external_ticket || ""} />
        </Field>
        <Field label="Evidence refs">
          <Input name="evidence_refs" defaultValue={item.tracking.evidence_refs.join("\n")} />
        </Field>
      </div>
      <Field label="Notes">
        <Textarea name="notes" defaultValue={item.tracking.notes || ""} />
      </Field>
    </form>
  );
}

function FutureJson({ title, value }: { title: string; value: unknown }) {
  return (
    <Card>
      <CardHeader title={title} />
      <pre className="max-h-80 overflow-auto p-4 text-xs leading-5 text-muted">{JSON.stringify(value, null, 2)}</pre>
    </Card>
  );
}
