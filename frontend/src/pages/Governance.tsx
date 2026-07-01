import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  FolderKanban,
  LogOut,
  Plus,
  Radar,
  ShieldCheck,
  Upload
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  ErrorNote,
  Field,
  Input,
  PageHeader,
  Select,
  Textarea
} from "../components/ui";
import {
  addControlEvidence,
  clearGovernanceSession,
  createProject,
  getGovernanceSession,
  getPallasLens,
  listPolicyPacks,
  listProjectControls,
  listProjects,
  listSubAgents,
  type ControlInstance,
  type GovernanceProject,
  type PallasLens
} from "../lib/governanceApi";
import { cn } from "../lib/utils";

const riskTiers = ["low", "medium", "high", "critical"];

export default function Governance() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [session, setSession] = useState(() => getGovernanceSession());
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [newProjectName, setNewProjectName] = useState("");
  const [riskTier, setRiskTier] = useState("high");
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>(["nist-ssdf"]);
  const [evidenceDraft, setEvidenceDraft] = useState<Record<string, string>>({});

  const policyPacks = useQuery({
    queryKey: ["governance", "policy-packs"],
    queryFn: listPolicyPacks
  });
  const projects = useQuery({
    queryKey: ["governance", "projects"],
    queryFn: listProjects
  });

  const selectedProject = useMemo(
    () => projects.data?.find((project) => project.id === selectedProjectId) ?? null,
    [projects.data, selectedProjectId]
  );

  useEffect(() => {
    if (!selectedProjectId && projects.data?.length) {
      setSelectedProjectId(projects.data[0].id);
    }
  }, [projects.data, selectedProjectId]);

  const controls = useQuery({
    queryKey: ["governance", "projects", selectedProjectId, "controls"],
    queryFn: () => listProjectControls(selectedProjectId ?? ""),
    enabled: Boolean(selectedProjectId)
  });
  const lens = useQuery({
    queryKey: ["governance", "projects", selectedProjectId, "lens"],
    queryFn: () => getPallasLens(selectedProjectId ?? ""),
    enabled: Boolean(selectedProjectId)
  });
  const subAgents = useQuery({
    queryKey: ["governance", "projects", selectedProjectId, "sub-agents"],
    queryFn: () => listSubAgents(selectedProjectId ?? ""),
    enabled: Boolean(selectedProjectId)
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createProject({
        name: newProjectName,
        risk_tier: riskTier,
        compliance_frameworks: selectedFrameworks
      }),
    onSuccess: (project) => {
      setNewProjectName("");
      setSelectedProjectId(project.id);
      void queryClient.invalidateQueries({ queryKey: ["governance", "projects"] });
    }
  });

  const evidenceMutation = useMutation({
    mutationFn: ({ controlId, content }: { controlId: string; content: string }) =>
      addControlEvidence(selectedProjectId ?? "", controlId, content),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["governance", "projects", selectedProjectId, "controls"]
        }),
        queryClient.invalidateQueries({
          queryKey: ["governance", "projects", selectedProjectId, "lens"]
        })
      ]);
    }
  });

  const overlays = policyPacks.data?.overlays ?? [];
  const applicableControls = controls.data?.filter((control) => control.is_applicable) ?? [];

  function toggleFramework(frameworkId: string) {
    setSelectedFrameworks((current) =>
      current.includes(frameworkId)
        ? current.filter((item) => item !== frameworkId)
        : [...current, frameworkId]
    );
  }

  function logout() {
    clearGovernanceSession();
    setSession(null);
    navigate("/login");
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Governance Portal"
        description="Project controls, evidence readiness, framework overlays, and security review state."
        actions={
          <>
            {session ? <Badge tone="good">{session.user.role}</Badge> : <Badge>Guest</Badge>}
            {session ? (
              <Button variant="quiet" onClick={logout}>
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Sign out
              </Button>
            ) : (
              <Link to="/login">
                <Button>
                  <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                  Sign in
                </Button>
              </Link>
            )}
          </>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader title="New Project" />
            <form
              className="grid gap-3 p-4"
              onSubmit={(event) => {
                event.preventDefault();
                if (newProjectName.trim()) {
                  createMutation.mutate();
                }
              }}
            >
              <Field label="Project name">
                <Input
                  value={newProjectName}
                  onChange={(event) => setNewProjectName(event.target.value)}
                  placeholder="Release review"
                />
              </Field>
              <Field label="Risk tier">
                <Select value={riskTier} onChange={(event) => setRiskTier(event.target.value)}>
                  {riskTiers.map((tier) => (
                    <option key={tier} value={tier}>
                      {tier}
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="grid gap-2">
                <div className="text-xs font-medium text-muted">Framework overlays</div>
                <div className="grid gap-2">
                  {overlays.map((overlay) => (
                    <label
                      key={overlay.id}
                      className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2 text-sm text-text"
                    >
                      <input
                        checked={selectedFrameworks.includes(overlay.id)}
                        className="h-4 w-4"
                        onChange={() => toggleFramework(overlay.id)}
                        type="checkbox"
                      />
                      <span className="min-w-0 flex-1 truncate">{overlay.label ?? overlay.id}</span>
                      <span className="text-xs text-muted">{overlay.region_group}</span>
                    </label>
                  ))}
                </div>
              </div>
              <ErrorNote
                message={createMutation.error instanceof Error ? createMutation.error.message : null}
              />
              <Button disabled={!newProjectName.trim() || createMutation.isPending} type="submit">
                <Plus className="h-4 w-4" aria-hidden="true" />
                Create
              </Button>
            </form>
          </Card>

          <Card>
            <CardHeader title="Projects" meta={`${projects.data?.length ?? 0} total`} />
            {projects.data?.length ? (
              <div className="divide-y divide-line">
                {projects.data.map((project) => (
                  <button
                    key={project.id}
                    className={cn(
                      "grid w-full gap-1 px-4 py-3 text-left transition hover:bg-panel2",
                      selectedProjectId === project.id ? "bg-panel2" : ""
                    )}
                    onClick={() => setSelectedProjectId(project.id)}
                    type="button"
                  >
                    <span className="truncate text-sm font-medium text-text">{project.name}</span>
                    <span className="text-xs text-muted">
                      {project.risk_tier ?? "unrated"} / {project.control_profile ?? "profile pending"}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title={projects.isPending ? "Loading projects" : "No projects yet."} />
            )}
          </Card>
        </div>

        <div className="space-y-4">
          {selectedProject ? (
            <>
              <ProjectSummary project={selectedProject} lens={lens.data ?? null} />
              <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
                <ControlsPanel
                  controls={applicableControls}
                  evidenceDraft={evidenceDraft}
                  loading={controls.isPending}
                  onDraftChange={(controlId, value) =>
                    setEvidenceDraft((draft) => ({ ...draft, [controlId]: value }))
                  }
                  onSubmit={(controlId) => {
                    const content = evidenceDraft[controlId]?.trim();
                    if (!content) return;
                    evidenceMutation.mutate({ controlId, content });
                    setEvidenceDraft((draft) => ({ ...draft, [controlId]: "" }));
                  }}
                  submitting={evidenceMutation.isPending}
                />
                <LensPanel lens={lens.data ?? null} loading={lens.isPending} />
              </div>
              <SubAgentPanel runs={subAgents.data ?? []} />
            </>
          ) : (
            <Card>
              <EmptyState title={projects.isPending ? "Loading governance data" : "Select or create a project."} />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function ProjectSummary({
  project,
  lens
}: {
  project: GovernanceProject;
  lens: PallasLens | null;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Metric
        icon={<FolderKanban className="h-4 w-4" aria-hidden="true" />}
        label="Project"
        value={project.name}
      />
      <Metric label="Risk" value={project.risk_tier ?? "unrated"} />
      <Metric label="Frameworks" value={String(project.compliance_frameworks.length)} />
      <Metric
        icon={<Radar className="h-4 w-4" aria-hidden="true" />}
        label="Readiness"
        value={lens ? `${lens.readiness_score}` : "-"}
      />
    </div>
  );
}

function Metric({
  label,
  value,
  icon
}: {
  label: string;
  value: string;
  icon?: ReactNode;
}) {
  return (
    <Card className="p-4">
      <div className="mb-3 flex h-4 items-center gap-2 text-accent">{icon}</div>
      <div className="truncate text-xl font-semibold text-text">{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </Card>
  );
}

function ControlsPanel({
  controls,
  evidenceDraft,
  loading,
  onDraftChange,
  onSubmit,
  submitting
}: {
  controls: ControlInstance[];
  evidenceDraft: Record<string, string>;
  loading: boolean;
  onDraftChange: (controlId: string, value: string) => void;
  onSubmit: (controlId: string) => void;
  submitting: boolean;
}) {
  return (
    <Card>
      <CardHeader title="Control Evidence" meta={`${controls.length} applicable`} />
      {controls.length ? (
        <div className="divide-y divide-line">
          {controls.slice(0, 12).map((control) => (
            <div key={`${control.framework_id}-${control.control_id}`} className="grid gap-3 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={control.evidence_count > 0 ? "good" : "warn"}>
                  {control.status.replace(/_/g, " ")}
                </Badge>
                <Badge>{control.framework_id}</Badge>
                <span className="text-xs text-muted">{control.control_id}</span>
              </div>
              <div>
                <div className="text-sm font-medium text-text">{control.title}</div>
                <p className="mt-1 text-sm leading-5 text-muted">
                  {control.normalized_requirement}
                </p>
              </div>
              <div className="grid gap-2 md:grid-cols-[1fr_auto]">
                <Textarea
                  minLength={1}
                  onChange={(event) => onDraftChange(control.control_id, event.target.value)}
                  placeholder={control.expected_evidence[0] ?? "Evidence note"}
                  value={evidenceDraft[control.control_id] ?? ""}
                />
                <Button
                  disabled={submitting || !(evidenceDraft[control.control_id] ?? "").trim()}
                  onClick={() => onSubmit(control.control_id)}
                  type="button"
                >
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Add
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title={loading ? "Loading controls" : "No applicable controls."} />
      )}
    </Card>
  );
}

function LensPanel({ lens, loading }: { lens: PallasLens | null; loading: boolean }) {
  if (!lens) {
    return (
      <Card>
        <CardHeader title="Pallas Lens" />
        <EmptyState title={loading ? "Loading score" : "No score yet."} />
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader
        title="Pallas Lens"
        meta={`${lens.posture.replace(/-/g, " ")} / ${lens.control_totals.evidence_items} evidence items`}
      />
      <div className="grid gap-4 p-4">
        <div>
          <div className="flex items-end justify-between gap-3">
            <div className="text-4xl font-semibold text-text">{lens.readiness_score}</div>
            <Badge tone={lens.readiness_score >= 75 ? "good" : lens.readiness_score >= 45 ? "warn" : "bad"}>
              {lens.posture}
            </Badge>
          </div>
          <p className="mt-2 text-sm leading-5 text-muted">{lens.summary}</p>
        </div>
        <div className="grid gap-3">
          {lens.dimensions.map((dimension) => (
            <div key={dimension.key} className="grid gap-1.5">
              <div className="flex justify-between gap-3 text-xs">
                <span className="text-muted">{dimension.label}</span>
                <span className="font-medium text-text">{dimension.score}</span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-panel2">
                <div
                  className="h-full rounded bg-accent"
                  style={{ width: `${Math.max(4, dimension.score)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="grid gap-2">
          {lens.next_actions.slice(0, 4).map((action) => (
            <div
              key={`${action.control_id ?? action.title}-${action.action}`}
              className="rounded-md border border-line bg-panel2 p-3"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-accent" aria-hidden="true" />
                <div className="truncate text-sm font-medium text-text">{action.action}</div>
              </div>
              <div className="mt-1 text-xs leading-5 text-muted">{action.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function SubAgentPanel({ runs }: { runs: Array<{ id: string; gate: string; sub_agent_key: string; status: string }> }) {
  return (
    <Card>
      <CardHeader title="Sub-Agent Runs" meta={`${runs.length} tracked`} />
      {runs.length ? (
        <div className="grid gap-2 p-4 md:grid-cols-3">
          {runs.map((run) => (
            <div key={run.id} className="rounded-md border border-line bg-panel2 p-3">
              <div className="text-sm font-medium text-text">{run.sub_agent_key}</div>
              <div className="mt-1 text-xs text-muted">
                {run.gate} / {run.status.replace(/_/g, " ")}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No sub-agent runs yet." />
      )}
    </Card>
  );
}
