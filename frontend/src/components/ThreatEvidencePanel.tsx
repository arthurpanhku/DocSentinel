import {
  Bot,
  CircleHelp,
  Quote,
  ShieldAlert,
  ShieldCheck
} from "lucide-react";

import type { SourceCitation, ThreatModel } from "../types";
import { Badge, Card, CardHeader, EmptyState } from "./ui";

type VerificationStatus =
  | "supported"
  | "contradicted"
  | "insufficient_evidence";

const statusView: Record<
  VerificationStatus,
  {
    label: string;
    tone: "good" | "bad" | "warn";
    icon: typeof ShieldCheck;
  }
> = {
  supported: {
    label: "Supported",
    tone: "good",
    icon: ShieldCheck
  },
  contradicted: {
    label: "Contradicted",
    tone: "bad",
    icon: ShieldAlert
  },
  insufficient_evidence: {
    label: "Insufficient evidence",
    tone: "warn",
    icon: CircleHelp
  }
};

export function ThreatEvidencePanel({
  threatModel,
  sources
}: {
  threatModel: ThreatModel;
  sources: SourceCitation[];
}) {
  const threats = threatModel.threats ?? [];
  const summary = threatModel.verification_summary;
  const sourcesById = new Map(sources.map((source) => [source.id, source]));

  return (
    <Card>
      <CardHeader
        title="Threat Evidence Critic"
        meta={
          summary
            ? `${summary.verifier} · inference-time verification`
            : "Threats are awaiting inference-time verification."
        }
        action={
          summary ? (
            <Badge tone={summary.status === "completed" ? "accent" : "warn"}>
              {summary.status === "completed" ? "Verification complete" : "Safe fallback"}
            </Badge>
          ) : null
        }
      />
      {summary ? (
        <div className="grid gap-3 border-b border-line p-4 sm:grid-cols-4">
          <SummaryMetric label="Supported" value={summary.supported} tone="good" />
          <SummaryMetric label="Contradicted" value={summary.contradicted} tone="bad" />
          <SummaryMetric
            label="Insufficient"
            value={summary.insufficient_evidence}
            tone="warn"
          />
          <SummaryMetric label="Total threats" value={summary.total} tone="neutral" />
        </div>
      ) : null}

      {threats.length ? (
        <div className="divide-y divide-line">
          {threats.map((threat) => {
            const verification = threat.verification;
            const status = verification?.status;
            const view = status ? statusView[status] : null;
            const Icon = view?.icon ?? Bot;
            const evidence = (verification?.evidence_ids ?? [])
              .map((id) => sourcesById.get(id))
              .filter((source): source is SourceCitation => Boolean(source));
            const counterevidence = (verification?.counterevidence_ids ?? [])
              .map((id) => sourcesById.get(id))
              .filter((source): source is SourceCitation => Boolean(source));

            return (
              <article key={threat.id} className="space-y-3 px-4 py-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Icon
                        aria-hidden="true"
                        className="h-4 w-4 text-muted"
                      />
                      <h3 className="text-sm font-medium text-text">
                        {threat.id} · {threat.category}
                      </h3>
                      {threat.affected_component ? (
                        <Badge>{threat.affected_component}</Badge>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted">
                      {threat.description}
                    </p>
                  </div>
                  {view ? (
                    <Badge tone={view.tone}>{view.label}</Badge>
                  ) : (
                    <Badge>Not verified</Badge>
                  )}
                </div>

                {verification ? (
                  <div className="rounded-md border border-line bg-panel2 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-xs font-medium text-text">
                        Critic rationale
                      </div>
                      <Badge>
                        support {(verification.support_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-muted">
                      {verification.rationale}
                    </p>
                    {verification.requires_human_review ? (
                      <p className="mt-2 text-xs text-warn">
                        Human review is required before approval.
                      </p>
                    ) : null}
                  </div>
                ) : null}

                {evidence.map((source) => (
                  <EvidenceQuote
                    key={source.id}
                    source={source}
                    label="Supporting evidence"
                    tone="good"
                  />
                ))}
                {counterevidence.map((source) => (
                  <EvidenceQuote
                    key={source.id}
                    source={source}
                    label="Counterevidence"
                    tone="bad"
                  />
                ))}
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState title="No threats were generated for this design." />
      )}
    </Card>
  );
}

function SummaryMetric({
  label,
  value,
  tone
}: {
  label: string;
  value: number;
  tone: "good" | "bad" | "warn" | "neutral";
}) {
  const colors = {
    good: "text-good",
    bad: "text-bad",
    warn: "text-warn",
    neutral: "text-text"
  };
  return (
    <div className="rounded-md border border-line bg-panel2 p-3">
      <div className={`text-xl font-semibold ${colors[tone]}`}>{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </div>
  );
}

function EvidenceQuote({
  source,
  label,
  tone
}: {
  source: SourceCitation;
  label: string;
  tone: "good" | "bad";
}) {
  return (
    <blockquote
      className={`rounded-md border-l-2 bg-panel2 px-3 py-2 ${
        tone === "good" ? "border-good" : "border-bad"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-text">
        <Quote aria-hidden="true" className="h-3.5 w-3.5" />
        <span>{label}</span>
        <span className="text-muted">
          {source.file}
          {source.locator ? `#${source.locator}` : ""}
        </span>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-muted">
        {source.excerpt}
      </p>
    </blockquote>
  );
}
