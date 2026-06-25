import type { components } from "./api/schema";

type Schemas = components["schemas"];
type SubmitAssessmentBody =
  Schemas["Body_submit_assessment_api_v1_assessments_post"];

export type AssessmentPhase = SubmitAssessmentBody["phase"];
export type TaskStatus = Schemas["AssessmentTaskResult"]["status"];
export type Severity = Schemas["RiskItem"]["severity"];

export type RiskItem = Schemas["RiskItem"];
export type ComplianceGap = Schemas["ComplianceGap"];
export type Remediation = Schemas["Remediation"];
export type SourceCitation = Schemas["SourceCitation"];
export type ThreatModel = Schemas["ThreatModel"];
export type Vulnerability = Schemas["Vulnerability"];
export type CrossPhaseRef = Schemas["CrossPhaseRef"];

type ApiAssessmentReport = Schemas["AssessmentReport"];

export interface AssessmentReport
  extends Omit<
    ApiAssessmentReport,
    | "risk_items"
    | "compliance_gaps"
    | "remediations"
    | "sources"
    | "vulnerabilities"
    | "cross_phase_refs"
  > {
  risk_items: RiskItem[];
  compliance_gaps: ComplianceGap[];
  remediations: Remediation[];
  sources: SourceCitation[];
  vulnerabilities: Vulnerability[];
  cross_phase_refs: CrossPhaseRef[];
}

type ApiAssessmentTask = Schemas["AssessmentTaskResult"];

export interface AssessmentTask
  extends Omit<ApiAssessmentTask, "report" | "comments"> {
  report?: AssessmentReport | null;
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

type ApiRemediationTracking = Schemas["RemediationTracking"];

export interface RemediationTracking
  extends Omit<ApiRemediationTracking, "evidence_refs"> {
  evidence_refs: string[];
}

export interface TrackedRemediation
  extends Omit<Schemas["TrackedRemediation"], "tracking"> {
  tracking: RemediationTracking;
}

type ApiSkill = Schemas["Skill"];

export interface Skill
  extends Omit<ApiSkill, "risk_focus" | "compliance_frameworks"> {
  risk_focus: string[];
  compliance_frameworks: string[];
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
