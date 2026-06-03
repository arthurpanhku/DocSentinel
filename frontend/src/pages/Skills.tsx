import { Edit3, Plus, RefreshCw, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge, Button, Card, CardHeader, EmptyState, ErrorNote, Field, Input, Textarea } from "../components/ui";
import { createSkill, deleteSkill, listSkills, updateSkill } from "../lib/api";
import { splitLines } from "../lib/utils";
import type { Skill } from "../types";

const blankSkill: Omit<Skill, "is_builtin"> = {
  id: "",
  name: "",
  description: "",
  system_prompt: "",
  risk_focus: [],
  compliance_frameworks: []
};

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [draft, setDraft] = useState<Omit<Skill, "is_builtin">>(blankSkill);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setError(null);
    try {
      const result = await listSkills();
      setSkills(result);
      if (!selectedId && result[0]) setSelectedId(result[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load skills.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const selected = useMemo(() => skills.find((skill) => skill.id === selectedId), [selectedId, skills]);

  useEffect(() => {
    if (selected) {
      setDraft({
        id: selected.id,
        name: selected.name,
        description: selected.description,
        system_prompt: selected.system_prompt,
        risk_focus: selected.risk_focus,
        compliance_frameworks: selected.compliance_frameworks
      });
    } else {
      setDraft(blankSkill);
    }
  }, [selected]);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const next = {
      id: String(form.get("id") || "").trim(),
      name: String(form.get("name") || "").trim(),
      description: String(form.get("description") || "").trim(),
      system_prompt: String(form.get("system_prompt") || "").trim(),
      risk_focus: splitLines(String(form.get("risk_focus") || "")),
      compliance_frameworks: splitLines(String(form.get("compliance_frameworks") || ""))
    };
    if (!next.id || !next.name || !next.description || !next.system_prompt) {
      setError("ID, name, description, and system prompt are required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (selected && !selected.is_builtin) {
        await updateSkill(selected.id, next);
      } else {
        await createSkill(next);
      }
      setSelectedId(next.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save skill.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!selected || selected.is_builtin) return;
    setBusy(true);
    setError(null);
    try {
      await deleteSkill(selected.id);
      setSelectedId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete skill.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold text-text">Skills</h1>
          <p className="mt-1 text-sm text-muted">Personas and SSDLC stage prompts used during assessment.</p>
        </div>
        <ErrorNote message={error} />
        <Card>
          <CardHeader
            title="Registry"
            action={<Button variant="quiet" onClick={() => void load()}><RefreshCw className="h-4 w-4" /></Button>}
          />
          <div className="divide-y divide-line">
            {skills.map((skill) => (
              <button
                key={skill.id}
                onClick={() => setSelectedId(skill.id)}
                className={`w-full px-4 py-3 text-left transition hover:bg-panel2 ${selectedId === skill.id ? "bg-panel2" : ""}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-text">{skill.name}</div>
                    <div className="mt-1 truncate text-xs text-muted">{skill.id}</div>
                  </div>
                  <Badge tone={skill.is_builtin ? "accent" : "good"}>{skill.is_builtin ? "built-in" : "custom"}</Badge>
                </div>
              </button>
            ))}
            {!skills.length ? <EmptyState title="No skills loaded." /> : null}
          </div>
        </Card>
        <Button variant="quiet" onClick={() => { setSelectedId(""); setDraft(blankSkill); }} className="w-full">
          <Plus className="h-4 w-4" />
          New custom skill
        </Button>
      </div>

      <Card>
        <CardHeader
          title={selected ? selected.name : "New Skill"}
          meta={selected?.is_builtin ? "Built-in skills are read-only." : "Custom skill editor."}
          action={selected && !selected.is_builtin ? (
            <Button variant="danger" onClick={handleDelete} disabled={busy}>
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          ) : null}
        />
        <form onSubmit={handleSave} className="space-y-4 p-4">
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="ID">
              <Input name="id" value={draft.id} disabled={Boolean(selected)} onChange={(event) => setDraft({ ...draft, id: event.target.value })} />
            </Field>
            <Field label="Name">
              <Input name="name" value={draft.name} disabled={selected?.is_builtin} onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
            </Field>
          </div>
          <Field label="Description">
            <Textarea name="description" value={draft.description} disabled={selected?.is_builtin} onChange={(event) => setDraft({ ...draft, description: event.target.value })} />
          </Field>
          <Field label="System prompt">
            <Textarea name="system_prompt" className="min-h-40 font-mono text-xs" value={draft.system_prompt} disabled={selected?.is_builtin} onChange={(event) => setDraft({ ...draft, system_prompt: event.target.value })} />
          </Field>
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Risk focus, one per line">
              <Textarea name="risk_focus" value={draft.risk_focus.join("\n")} disabled={selected?.is_builtin} onChange={(event) => setDraft({ ...draft, risk_focus: splitLines(event.target.value) })} />
            </Field>
            <Field label="Compliance frameworks, one per line">
              <Textarea name="compliance_frameworks" value={draft.compliance_frameworks.join("\n")} disabled={selected?.is_builtin} onChange={(event) => setDraft({ ...draft, compliance_frameworks: splitLines(event.target.value) })} />
            </Field>
          </div>
          <Button disabled={busy || selected?.is_builtin}>
            <Edit3 className="h-4 w-4" />
            {selected && !selected.is_builtin ? "Save changes" : "Create custom skill"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
