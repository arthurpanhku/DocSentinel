import { API_BASE, request } from "./api";

export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
  errors: unknown[];
}

export interface GovernanceUser {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: string;
}

export interface GovernanceSession {
  access_token: string;
  token_type: string;
  user: GovernanceUser;
}

export interface PolicyPackItem {
  id: string;
  name: string;
  label?: string;
  version: string;
  description: string;
  region_group?: string;
  type?: "base" | "overlay";
}

export interface PolicyPackResponse {
  active: PolicyPackItem & {
    schemas: string[];
    control_profiles: Record<string, string>;
  };
  available: PolicyPackItem[];
  overlays: PolicyPackItem[];
  all: PolicyPackItem[];
}

export interface GovernanceProject {
  id: string;
  name: string;
  description?: string | null;
  business_owner?: string | null;
  risk_tier?: string | null;
  control_profile?: string | null;
  compliance_frameworks: string[];
  review_mode?: string | null;
  status: string;
  system_type?: string | null;
  hosting_type?: string | null;
  data_classification?: string | null;
  risk_level?: number | null;
  organization?: string | null;
  created_at?: string | null;
}

export interface ControlInstance {
  id: string;
  project_id: string;
  control_id: string;
  framework_id: string;
  title: string;
  normalized_requirement: string;
  expected_evidence: string[];
  review_focus: string[];
  is_applicable: boolean;
  is_mandatory: boolean;
  review_mode: string;
  status: string;
  ai_confidence?: number | null;
  evidence_count: number;
}

export interface PallasLens {
  project_id: string;
  readiness_score: number;
  posture: string;
  summary: string;
  dimensions: Array<{ key: string; label: string; score: number; why: string }>;
  control_totals: {
    total: number;
    applicable: number;
    mandatory_applicable: number;
    evidence_items: number;
  };
  status_counts: Record<string, number>;
  frameworks: Record<string, Record<string, number>>;
  next_actions: Array<{
    priority: string;
    control_id?: string | null;
    title: string;
    action: string;
    reason: string;
  }>;
}

export interface SubAgentRun {
  id: string;
  project_id: string;
  gate: string;
  sub_agent_key: string;
  status: string;
  comment?: string | null;
  run_output: Record<string, unknown>;
}

const sessionKey = "docsentinel-governance-session";

function governanceHeaders(init?: RequestInit) {
  const headers = new Headers(init?.headers);
  const session = getGovernanceSession();
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

export function getGovernanceSession(): GovernanceSession | null {
  const raw = window.localStorage.getItem(sessionKey);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GovernanceSession;
  } catch {
    window.localStorage.removeItem(sessionKey);
    return null;
  }
}

export function saveGovernanceSession(session: GovernanceSession) {
  window.localStorage.setItem(sessionKey, JSON.stringify(session));
}

export function clearGovernanceSession() {
  window.localStorage.removeItem(sessionKey);
}

async function governanceRequest<T>(path: string, init?: RequestInit) {
  return request<ApiEnvelope<T>>(`${API_BASE}${path}`, {
    ...init,
    headers: governanceHeaders(init)
  }).then((response) => response.data);
}

export function login(email: string, password: string) {
  return governanceRequest<GovernanceSession>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function listPolicyPacks() {
  return governanceRequest<PolicyPackResponse>("/policy-packs");
}

export function listProjects() {
  return governanceRequest<GovernanceProject[]>("/projects");
}

export function createProject(input: {
  name: string;
  risk_tier?: string;
  compliance_frameworks: string[];
}) {
  return governanceRequest<GovernanceProject>("/projects", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function listProjectControls(projectId: string) {
  return governanceRequest<ControlInstance[]>(`/projects/${projectId}/controls`);
}

export function getPallasLens(projectId: string) {
  return governanceRequest<PallasLens>(`/projects/${projectId}/pallas-lens`);
}

export function addControlEvidence(projectId: string, controlId: string, content: string) {
  return governanceRequest(`/projects/${projectId}/controls/${controlId}/evidence`, {
    method: "POST",
    body: JSON.stringify({ evidence_type: "text", content })
  });
}

export function listSubAgents(projectId: string) {
  return governanceRequest<SubAgentRun[]>(`/projects/${projectId}/sub-agents`);
}
