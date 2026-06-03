export type AssessmentPhase =
  | "auto"
  | "requirements"
  | "design"
  | "development"
  | "testing"
  | "deployment"
  | "operations"
  | "full_ssdlc";

export type TaskStatus =
  | "pending"
  | "running"
  | "review_pending"
  | "approved"
  | "rejected"
  | "escalated"
  | "completed"
  | "failed";

export type Severity = "low" | "medium" | "high" | "critical";

export interface RiskItem {
  id: string;
  title: string;
  severity: Severity;
  description?: string | null;
  source_ref?: string | null;
  category?: string | null;
  phase?: string | null;
  confidence?: number | null;
  citation_ids?: string[];
}

export interface ComplianceGap {
  id: string;
  control_or_clause: string;
  gap_description: string;
  evidence_suggestion?: string | null;
  framework?: string | null;
  phase?: string | null;
}

export interface Remediation {
  id: string;
  action: string;
  priority?: "low" | "medium" | "high" | "critical" | null;
  related_risk_ids?: string[];
  related_gap_ids?: string[];
  related_vuln_ids?: string[];
  related_threat_ids?: string[];
  external_ticket?: string | null;
  phase?: string | null;
}

export interface SourceCitation {
  id: string;
  file: string;
  page?: number | null;
  paragraph_id?: string | null;
  excerpt: string;
  evidence_link?: string | null;
  score?: number | null;
}

export interface ThreatModel {
  methodology?: string;
  threats?: Array<Record<string, unknown>>;
}

export interface Vulnerability {
  id: string;
  title: string;
  severity: string;
  source_tool?: string;
  cwe_id?: string;
  cvss_score?: number;
  location?: string;
  description?: string;
  remediation?: string;
  status?: string;
}

export interface AssessmentReport {
  version: string;
  task_id: string;
  phase?: string | null;
  status: "completed" | "partial" | "failed";
  summary: string;
  risk_items: RiskItem[];
  compliance_gaps: ComplianceGap[];
  remediations: Remediation[];
  confidence: number;
  sources: SourceCitation[];
  threat_model?: ThreatModel | null;
  vulnerabilities?: Vulnerability[];
  cross_phase_refs?: Array<Record<string, unknown>>;
  metadata?: {
    scenario_id?: string | null;
    project_id?: string | null;
    ssdlc_stage?: string | null;
    ssdlc_phase?: string | null;
    skill_id?: string | null;
    model_used?: string | null;
    completed_at?: string | null;
  } | null;
  format: "json" | "markdown";
}

export interface AssessmentTask {
  task_id: string;
  status: TaskStatus;
  report?: AssessmentReport | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
  version: number;
  assignee?: string | null;
  comments: Array<Record<string, unknown>>;
}

export interface ActivityEntry {
  type: string;
  at?: string;
  message?: string;
  action?: string;
  comment?: string;
  assignee?: string;
  status?: string;
  owner?: string;
  external_ticket?: string;
  remediation_id?: string;
  preview?: string;
}

export interface RemediationTracking {
  remediation_id: string;
  status: "open" | "in_progress" | "resolved" | "verified" | "closed";
  owner?: string | null;
  due_at?: string | null;
  external_ticket?: string | null;
  notes?: string | null;
  evidence_refs: string[];
  updated_at?: string | null;
}

export interface TrackedRemediation {
  remediation: Remediation;
  tracking: RemediationTracking;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  risk_focus: string[];
  compliance_frameworks: string[];
  is_builtin: boolean;
}

export interface KBChunk {
  content: string;
  metadata: Record<string, unknown>;
}

export interface LLMConfig {
  provider: string;
  model: string;
  base_url?: string;
  api_key_set?: boolean;
  api_key_preview?: string | null;
  providers?: Array<{
    id: string;
    label: string;
    default_model: string;
    default_base_url: string;
    requires_api_key: boolean;
  }>;
}
