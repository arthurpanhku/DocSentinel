import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { SourceCitation, ThreatModel } from "../types";
import { ThreatEvidencePanel } from "./ThreatEvidencePanel";

const evidenceId = "DOC-1-L8-L10-abcdef";

const threatModel: ThreatModel = {
  methodology: "STRIDE",
  verification_summary: {
    status: "completed",
    verifier: "ollama:inference",
    supported: 1,
    contradicted: 0,
    insufficient_evidence: 1,
    total: 2
  },
  threats: [
    {
      id: "T1",
      category: "Tampering",
      description: "Unsigned webhook payloads can be modified.",
      affected_component: "Payment webhook",
      mitigations: ["Implement HMAC verification."],
      confidence: 0.94,
      citation_ids: [evidenceId],
      verification: {
        status: "supported",
        support_score: 0.94,
        rationale: "The design explicitly says HMAC validation is not implemented.",
        evidence_ids: [evidenceId],
        counterevidence_ids: [],
        requires_human_review: true
      }
    },
    {
      id: "T2",
      category: "Repudiation",
      description: "Administrators may deny privileged actions.",
      mitigations: [],
      citation_ids: [],
      verification: {
        status: "insufficient_evidence",
        support_score: 0.2,
        rationale: "The design does not describe audit logging.",
        evidence_ids: [],
        counterevidence_ids: [],
        requires_human_review: true
      }
    }
  ]
};

const sources: SourceCitation[] = [
  {
    id: evidenceId,
    file: "checkout-architecture.md",
    excerpt: "HMAC signature validation is planned but is not implemented.",
    locator: "L8-L10",
    document_hash: "abcdef",
    source_kind: "current_document"
  }
];

describe("ThreatEvidencePanel", () => {
  it("shows critic status, exact evidence, and the human-review gate", () => {
    render(
      <ThreatEvidencePanel threatModel={threatModel} sources={sources} />
    );

    expect(
      screen.getByRole("heading", { name: "Threat Evidence Critic" })
    ).toBeInTheDocument();
    expect(screen.getByText("Verification complete")).toBeInTheDocument();
    expect(screen.getAllByText("Supported")).toHaveLength(2);
    expect(screen.getByText("Insufficient evidence")).toBeInTheDocument();
    expect(
      screen.getByText("checkout-architecture.md#L8-L10")
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Human review is required before approval.")
    ).toHaveLength(2);
  });
});
