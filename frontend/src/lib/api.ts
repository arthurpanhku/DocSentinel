import type {
  ActivityEntry,
  AssessmentPhase,
  AssessmentTask,
  KBChunk,
  LLMConfig,
  RemediationTracking,
  Skill,
  TrackedRemediation
} from "../types";

const trimSlash = (value: string) => value.replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as T;
  }
  return response.json() as Promise<T>;
}

export async function getHealth() {
  return request<{ status: string }>("/health");
}

export async function getLLMConfig() {
  return request<LLMConfig>("/config/llm");
}

export async function updateLLMConfig(input: {
  provider: string;
  model?: string;
  base_url?: string;
  api_key?: string;
}) {
  return request<LLMConfig & { status: string; message?: string }>("/config/llm", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function listAssessments(params: {
  status?: string;
  assignee?: string;
  limit?: number;
} = {}) {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.assignee) query.set("assignee", params.assignee);
  query.set("limit", String(params.limit ?? 200));
  return request<AssessmentTask[]>(`/api/v1/assessments?${query.toString()}`);
}

export async function getAssessment(taskId: string) {
  return request<AssessmentTask>(`/api/v1/assessments/${taskId}`);
}

export async function getActivity(taskId: string) {
  return request<ActivityEntry[]>(`/api/v1/assessments/${taskId}/activity`);
}

export async function getRemediations(taskId: string) {
  return request<TrackedRemediation[]>(`/api/v1/assessments/${taskId}/remediations`);
}

export async function submitAssessment(input: {
  files: File[];
  scenarioId?: string;
  projectId?: string;
  phase: AssessmentPhase;
  skillId?: string;
  collaborativeMode: boolean;
}) {
  const form = new FormData();
  input.files.forEach((file) => form.append("files", file));
  if (input.scenarioId) form.append("scenario_id", input.scenarioId);
  if (input.projectId) form.append("project_id", input.projectId);
  form.append("phase", input.phase);
  if (input.skillId) form.append("skill_id", input.skillId);
  form.append("collaborative_mode", String(input.collaborativeMode));
  return request<{ task_id: string; status: string; message?: string }>("/api/v1/assessments", {
    method: "POST",
    body: form
  });
}

export async function reviewAssessment(taskId: string, input: {
  action: "approve" | "reject" | "comment" | "escalate";
  comment?: string;
  assignee?: string;
}) {
  return request<{ status: string; task_id: string }>(`/api/v1/assessments/${taskId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function addComment(taskId: string, content: string, userId = "console") {
  return request<{ message: string }>(`/api/v1/assessments/${taskId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, user_id: userId })
  });
}

export async function updateRemediation(taskId: string, remediationId: string, input: Partial<RemediationTracking>) {
  return request<RemediationTracking>(
    `/api/v1/assessments/${taskId}/remediations/${remediationId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input)
    }
  );
}

export async function uploadKbDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ document_id: string }>("/api/v1/kb/documents", {
    method: "POST",
    body: form
  });
}

export async function queryKb(queryText: string, topK: number) {
  return request<{ chunks: KBChunk[] }>("/api/v1/kb/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText, top_k: topK })
  });
}

export async function reindexKb(directory: string) {
  return request<Record<string, unknown>>("/api/v1/kb/reindex", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ directory: trimSlash(directory) })
  });
}

export async function listSkills() {
  return request<Skill[]>("/api/v1/skills/");
}

export async function createSkill(skill: Omit<Skill, "is_builtin">) {
  return request<Skill>("/api/v1/skills/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(skill)
  });
}

export async function updateSkill(skillId: string, skill: Partial<Omit<Skill, "id" | "is_builtin">>) {
  return request<Skill>(`/api/v1/skills/${skillId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(skill)
  });
}

export async function deleteSkill(skillId: string) {
  return request<{ message: string }>(`/api/v1/skills/${skillId}`, {
    method: "DELETE"
  });
}
