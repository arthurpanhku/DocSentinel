"""Inference-time evidence verification for design-phase threat models."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass, replace
from typing import Any

from app.core.config import settings
from app.core.guardrails import UNTRUSTED_CONTENT_INSTRUCTION, wrap_untrusted_content
from app.llm.base import invoke_llm
from app.models.assessment import (
    AssessmentReport,
    EvidenceCriticSummary,
    EvidenceVerification,
    SourceCitation,
    Threat,
)
from app.models.parser import ParsedDocument

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}")
_STOPWORDS = {
    "about",
    "after",
    "against",
    "also",
    "because",
    "before",
    "being",
    "could",
    "from",
    "into",
    "might",
    "must",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "under",
    "using",
    "when",
    "where",
    "which",
    "with",
    "would",
}
_STRIDE_TERMS = {
    "Spoofing": {
        "authentication",
        "credential",
        "identity",
        "impersonation",
        "login",
        "oidc",
        "spoof",
        "token",
    },
    "Tampering": {
        "change",
        "integrity",
        "modify",
        "signature",
        "tamper",
        "validation",
        "webhook",
    },
    "Repudiation": {
        "audit",
        "evidence",
        "log",
        "nonrepudiation",
        "repudiation",
        "trace",
    },
    "InformationDisclosure": {
        "confidential",
        "data",
        "disclosure",
        "encrypt",
        "exposure",
        "pii",
        "secret",
        "tls",
    },
    "DenialOfService": {
        "availability",
        "capacity",
        "denial",
        "dos",
        "limit",
        "quota",
        "rate",
        "resource",
    },
    "ElevationOfPrivilege": {
        "admin",
        "authorization",
        "permission",
        "privilege",
        "role",
        "service",
    },
}


@dataclass(frozen=True)
class EvidencePassage:
    id: str
    file: str
    document_hash: str
    locator: str
    excerpt: str
    start_line: int
    end_line: int
    score: float = 0.0


def _document_hash(document: ParsedDocument) -> str:
    if document.metadata.file_hash:
        return document.metadata.file_hash
    content = (
        document.content if isinstance(document.content, str) else str(document.content)
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _flush_passage(
    passages: list[EvidencePassage],
    *,
    document: ParsedDocument,
    document_index: int,
    document_hash: str,
    buffer: list[str],
    start_line: int,
    end_line: int,
) -> None:
    excerpt = "\n".join(buffer).strip()
    if not excerpt:
        return
    short_hash = document_hash[:10]
    passages.append(
        EvidencePassage(
            id=f"DOC-{document_index}-L{start_line}-L{end_line}-{short_hash}",
            file=document.metadata.filename,
            document_hash=document_hash,
            locator=f"L{start_line}-L{end_line}",
            excerpt=excerpt[:900],
            start_line=start_line,
            end_line=end_line,
        )
    )


def build_document_passages(
    parsed_documents: list[ParsedDocument],
) -> list[EvidencePassage]:
    """Create stable, line-addressable passages from current-project documents."""
    passages: list[EvidencePassage] = []
    for document_index, document in enumerate(parsed_documents, start=1):
        content = (
            document.content
            if isinstance(document.content, str)
            else str(document.content)
        )
        document_hash = _document_hash(document)
        lines = content.splitlines() or [content]
        buffer: list[str] = []
        start_line = 1

        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                if buffer:
                    _flush_passage(
                        passages,
                        document=document,
                        document_index=document_index,
                        document_hash=document_hash,
                        buffer=buffer,
                        start_line=start_line,
                        end_line=line_number - 1,
                    )
                    buffer = []
                continue

            if not buffer:
                start_line = line_number
            buffer.append(line)
            if len(buffer) >= 6 or sum(len(part) for part in buffer) >= 850:
                _flush_passage(
                    passages,
                    document=document,
                    document_index=document_index,
                    document_hash=document_hash,
                    buffer=buffer,
                    start_line=start_line,
                    end_line=line_number,
                )
                buffer = []

        if buffer:
            _flush_passage(
                passages,
                document=document,
                document_index=document_index,
                document_hash=document_hash,
                buffer=buffer,
                start_line=start_line,
                end_line=len(lines),
            )
    return passages


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(value.casefold())
        if token not in _STOPWORDS
    }


def _rank_passages(
    threat: Threat,
    passages: list[EvidencePassage],
    *,
    limit: int,
) -> list[EvidencePassage]:
    query = " ".join(
        part
        for part in [
            threat.category,
            threat.affected_component or "",
            threat.description,
        ]
        if part
    )
    query_tokens = _tokens(query) | _STRIDE_TERMS.get(threat.category, set())
    component = (threat.affected_component or "").casefold().strip()
    ranked: list[EvidencePassage] = []

    for passage in passages:
        passage_tokens = _tokens(passage.excerpt)
        overlap = len(query_tokens & passage_tokens)
        denominator = math.sqrt(max(len(query_tokens), 1) * max(len(passage_tokens), 1))
        score = overlap / denominator
        if component and component in passage.excerpt.casefold():
            score += 0.35
        if passage.excerpt.lstrip().startswith("#"):
            score += 0.02
        ranked.append(replace(passage, score=round(score, 4)))

    ranked.sort(
        key=lambda passage: (
            passage.score,
            -passage.start_line,
            passage.file,
        ),
        reverse=True,
    )
    positive = [passage for passage in ranked if passage.score > 0]
    if positive:
        return positive[:limit]
    return ranked[: min(2, limit)]


def _critic_prompt(
    threats: list[Threat],
    candidates: dict[str, list[EvidencePassage]],
) -> tuple[str, str]:
    system_prompt = (
        "You are EvidenceCriticAgent, an independent threat-model evidence verifier. "
        f"{UNTRUSTED_CONTENT_INSTRUCTION} "
        "For each STRIDE threat, decide whether the current design documents contain "
        "facts that support the architectural preconditions of the threat, explicitly "
        "contradict it, or provide insufficient evidence. Do not treat the absence "
        "of a mitigation as proof that a threat is supported. Do not use outside "
        "knowledge "
        "as evidence. Use only the candidate evidence IDs allowed for that threat. "
        "Return JSON only with a `verdicts` array. Each verdict must contain: "
        "`threat_id`, `status` (`supported`, `contradicted`, or "
        "`insufficient_evidence`), `support_score` from 0 to 1, `evidence_ids`, "
        "`counterevidence_ids`, and a concise `rationale`. A supported verdict "
        "requires "
        "at least one evidence ID. A contradicted verdict requires at least one "
        "counterevidence ID. Prefer insufficient_evidence over guessing."
    )

    sections: list[str] = []
    for threat in threats:
        allowed = candidates.get(threat.id, [])
        threat_payload = {
            "id": threat.id,
            "category": threat.category,
            "description": threat.description,
            "affected_component": threat.affected_component,
            "mitigations": threat.mitigations,
            "allowed_evidence_ids": [passage.id for passage in allowed],
        }
        evidence = "\n".join(
            f"[{passage.id}] {passage.file}#{passage.locator} "
            f"(retrieval_score={passage.score})\n"
            f"{wrap_untrusted_content(passage.id, passage.excerpt)}"
            for passage in allowed
        )
        sections.append(
            f"## Threat\n{json.dumps(threat_payload, ensure_ascii=False)}\n"
            f"## Candidate evidence\n{evidence or '(none)'}"
        )
    return system_prompt, "\n\n---\n\n".join(sections)


def _json_object(raw: str) -> dict[str, Any]:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end < start:
        raise ValueError("Evidence critic returned no JSON object")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Evidence critic response must be a JSON object")
    return value


def _score(value: Any) -> float:
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return 0.0
        return min(1.0, max(0.0, parsed))
    except (TypeError, ValueError):
        return 0.0


def _fallback_verification(reason: str) -> EvidenceVerification:
    return EvidenceVerification(
        status="insufficient_evidence",
        support_score=0.0,
        rationale=reason,
        requires_human_review=True,
    )


def _valid_ids(value: Any, allowed_ids: set[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    valid: list[str] = []
    seen: set[str] = set()
    for item in value:
        evidence_id = str(item)
        if evidence_id in allowed_ids and evidence_id not in seen:
            valid.append(evidence_id)
            seen.add(evidence_id)
    return valid


def _apply_verdicts(
    report: AssessmentReport,
    candidates: dict[str, list[EvidencePassage]],
    payload: dict[str, Any] | None,
    *,
    fallback_reason: str | None = None,
) -> AssessmentReport:
    updated = report.model_copy(deep=True)
    assert updated.threat_model is not None

    by_threat: dict[str, dict[str, Any]] = {}
    if payload is not None:
        verdicts = payload.get("verdicts", [])
        if isinstance(verdicts, list):
            for verdict in verdicts:
                if isinstance(verdict, dict) and verdict.get("threat_id"):
                    by_threat.setdefault(str(verdict["threat_id"]), verdict)

    passages_by_id = {
        passage.id: passage for allowed in candidates.values() for passage in allowed
    }
    referenced: set[str] = set()
    counts = {
        "supported": 0,
        "contradicted": 0,
        "insufficient_evidence": 0,
    }

    for threat in updated.threat_model.threats:
        allowed_ids = {passage.id for passage in candidates.get(threat.id, [])}
        verdict = by_threat.get(threat.id)
        if verdict is None:
            verification = _fallback_verification(
                fallback_reason or "The verifier returned no verdict for this threat."
            )
        else:
            status = str(verdict.get("status", "insufficient_evidence"))
            if status not in counts:
                status = "insufficient_evidence"
            evidence_ids = _valid_ids(verdict.get("evidence_ids"), allowed_ids)
            counterevidence_ids = _valid_ids(
                verdict.get("counterevidence_ids"),
                allowed_ids,
            )
            rationale = str(verdict.get("rationale") or "").strip()[:700]
            support_score = _score(verdict.get("support_score"))

            if status == "supported" and not evidence_ids:
                status = "insufficient_evidence"
                rationale = (
                    "The verifier did not provide a valid current-document citation. "
                    + rationale
                ).strip()
            elif status == "contradicted" and not counterevidence_ids:
                if evidence_ids:
                    counterevidence_ids = evidence_ids
                    evidence_ids = []
                else:
                    status = "insufficient_evidence"
                    rationale = (
                        "The verifier did not provide valid counterevidence. "
                        + rationale
                    ).strip()

            if status == "insufficient_evidence":
                evidence_ids = []
                counterevidence_ids = []
            verification = EvidenceVerification(
                status=status,
                support_score=support_score,
                rationale=rationale or "No verifier rationale was provided.",
                evidence_ids=evidence_ids,
                counterevidence_ids=counterevidence_ids,
                requires_human_review=True,
            )

        threat.verification = verification
        threat.confidence = verification.support_score
        threat.citation_ids = (
            verification.evidence_ids + verification.counterevidence_ids
        )
        referenced.update(threat.citation_ids)
        counts[verification.status] += 1

    existing_ids = {source.id for source in updated.sources}
    for evidence_id in sorted(referenced):
        if evidence_id in existing_ids:
            continue
        passage = passages_by_id[evidence_id]
        updated.sources.append(
            SourceCitation(
                id=passage.id,
                file=passage.file,
                paragraph_id=passage.locator,
                excerpt=passage.excerpt,
                evidence_link=(f"document://{passage.document_hash}#{passage.locator}"),
                score=passage.score,
                document_hash=passage.document_hash,
                locator=passage.locator,
                source_kind="current_document",
            )
        )

    status = "fallback" if fallback_reason else "completed"
    updated.threat_model.verification_summary = EvidenceCriticSummary(
        status=status,
        verifier=(
            "safe-fallback" if fallback_reason else f"{settings.LLM_PROVIDER}:inference"
        ),
        supported=counts["supported"],
        contradicted=counts["contradicted"],
        insufficient_evidence=counts["insufficient_evidence"],
        total=len(updated.threat_model.threats),
    )
    return updated


async def verify_threat_model_evidence(
    report: AssessmentReport,
    parsed_documents: list[ParsedDocument],
) -> AssessmentReport:
    """Verify all threats in one inference-time pass against current documents."""
    design_selected = report.phase == "design" or (
        report.metadata is not None and report.metadata.skill_id == "ssdlc-design"
    )
    if (
        not settings.EVIDENCE_CRITIC_ENABLED
        or not design_selected
        or report.threat_model is None
        or not report.threat_model.threats
    ):
        return report

    max_threats = max(1, settings.EVIDENCE_CRITIC_MAX_THREATS)
    max_candidates = max(1, settings.EVIDENCE_CRITIC_MAX_CANDIDATES)
    threats = report.threat_model.threats[:max_threats]
    passages = build_document_passages(parsed_documents)
    candidates = {
        threat.id: _rank_passages(
            threat,
            passages,
            limit=max_candidates,
        )
        for threat in threats
    }

    if not passages:
        return _apply_verdicts(
            report,
            candidates,
            None,
            fallback_reason="No current-document evidence passages were available.",
        )

    system_prompt, user_prompt = _critic_prompt(threats, candidates)
    try:
        raw = await invoke_llm(system_prompt, user_prompt)
        payload = _json_object(raw)
    except Exception as exc:
        logger.warning("Evidence critic failed safely: %s", exc)
        return _apply_verdicts(
            report,
            candidates,
            None,
            fallback_reason=(
                "Evidence verification was unavailable; human review is required."
            ),
        )

    return _apply_verdicts(report, candidates, payload)
