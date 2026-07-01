from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agent.orchestrator import (
    _build_chunk_lookup,
    _evidence_agent_keyword_fallback,
    _extract_query_seed,
    _resolve_citations_from_llm,
    _split_text_with_overlap,
    run_assessment,
)
from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.models.skill import Skill


def _make_skill(**kwargs) -> Skill:
    defaults = dict(
        id="test-skill",
        name="Test Skill",
        description="A test skill",
        system_prompt="YOU ARE A TEST SKILL",
        risk_focus=["Testing"],
        compliance_frameworks=["TEST-101"],
    )
    defaults.update(kwargs)
    return Skill(**defaults)


def _make_doc(
    content: str = "Test document content.", filename: str = "test.md"
) -> ParsedDocument:
    return ParsedDocument(
        content=content,
        metadata=ParsedDocumentMetadata(filename=filename, type="md"),
    )


def _patch_deps(skill, llm_response='{"summary": "Test", "risk_items": []}'):
    """Return a context manager that patches skill service, LLM, and KB."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with patch("app.agent.orchestrator.get_skill_service") as mock_svc:
            mock_svc_instance = MagicMock()
            mock_svc_instance.get_skill.return_value = skill
            mock_svc_instance.list_skills.return_value = [skill]
            mock_svc.return_value = mock_svc_instance

            with patch(
                "app.agent.orchestrator.invoke_llm", new_callable=AsyncMock
            ) as mock_llm:
                mock_llm.return_value = llm_response

                with patch("app.agent.orchestrator.get_kb_service") as mock_kb_svc:
                    mock_kb = MagicMock()
                    mock_kb.query = AsyncMock(return_value=[])
                    mock_kb.query_history_responses.return_value = []
                    mock_kb_svc.return_value = mock_kb

                    yield mock_llm

    return _ctx()


# ---------------------------------------------------------------------------
# Existing test — skill prompt injection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_orchestrator_uses_skill_prompt():
    skill = _make_skill()
    with _patch_deps(skill) as mock_invoke:
        await run_assessment(uuid4(), [_make_doc()], skill_id="test-skill")

        calls = mock_invoke.call_args_list
        found = any("YOU ARE A TEST SKILL" in call.args[0] for call in calls)
        assert found, "Skill system prompt was not injected into LLM calls"


# ---------------------------------------------------------------------------
# P1: semantic query seed
# ---------------------------------------------------------------------------


def test_extract_query_seed_short_text_returned_unchanged():
    text = "Short text."
    assert _extract_query_seed(text, max_chars=2000) == text


def test_extract_query_seed_no_focus_returns_head():
    text = "A" * 3000
    seed = _extract_query_seed(text, skill_focus=None, max_chars=2000)
    assert len(seed) <= 2000
    assert seed == text[:2000]


def test_extract_query_seed_prefers_paragraphs_with_focus_terms():
    irrelevant = "The weather is nice today.\n\n" * 20
    relevant = "Access control and encryption are critical security controls."
    text = irrelevant + "\n\n" + relevant
    seed = _extract_query_seed(
        text,
        skill_focus=["Access Control", "Encryption"],
        max_chars=300,
    )
    assert "Access control" in seed or "encryption" in seed.lower()


def test_extract_query_seed_respects_max_chars():
    text = "\n\n".join(["paragraph " + str(i) for i in range(100)])
    seed = _extract_query_seed(text, skill_focus=["paragraph"], max_chars=500)
    assert len(seed) <= 500


# ---------------------------------------------------------------------------
# P0: evidence agent
# ---------------------------------------------------------------------------


def test_evidence_agent_keyword_fallback_finds_matches():
    doc = _make_doc("The password must be at least 12 characters.\nUnrelated line.")
    result = _evidence_agent_keyword_fallback([doc], skill_focus=["Authentication"])
    assert "password" in result.lower()
    assert "test.md#L" in result


def test_evidence_agent_keyword_fallback_empty_doc():
    doc = _make_doc("No relevant content here.", filename="empty.md")
    result = _evidence_agent_keyword_fallback([doc], skill_focus=[])
    # Falls through to the no-match message
    assert result  # must return something (not crash)


def test_evidence_agent_keyword_fallback_skill_focus_expands_keywords():
    doc = _make_doc("Data residency requirement: EU only.\nOther line.")
    result = _evidence_agent_keyword_fallback([doc], skill_focus=["data residency"])
    assert "data residency" in result.lower() or "residency" in result.lower()


@pytest.mark.asyncio
async def test_evidence_agent_uses_llm_extraction():
    skill = _make_skill()
    with _patch_deps(
        skill, llm_response="test.md#L1: The password must be rotated"
    ) as mock_llm:
        await run_assessment(uuid4(), [_make_doc()], skill_id="test-skill")
    # LLM should have been called at least once for evidence extraction
    assert mock_llm.call_count >= 1


@pytest.mark.asyncio
async def test_evidence_agent_falls_back_when_llm_raises():
    """Evidence extraction falls back instead of propagating LLM errors."""
    skill = _make_skill()

    call_count = 0

    async def selective_llm(system_prompt: str, user_prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        # Fail only the evidence extraction call (identified by its system prompt).
        if "evidence extractor" in system_prompt:
            raise RuntimeError("LLM unavailable")
        return '{"summary": "ok", "risk_items": []}'

    with patch("app.agent.orchestrator.get_skill_service") as mock_svc:
        inst = MagicMock()
        inst.get_skill.return_value = skill
        inst.list_skills.return_value = [skill]
        mock_svc.return_value = inst

        with patch("app.agent.orchestrator.invoke_llm", side_effect=selective_llm):
            with patch("app.agent.orchestrator.get_kb_service") as mock_kb_svc:
                mock_kb = MagicMock()
                mock_kb.query = AsyncMock(return_value=[])
                mock_kb.query_history_responses.return_value = []
                mock_kb_svc.return_value = mock_kb

                # Should complete without raising, using keyword fallback for evidence.
                report = await run_assessment(
                    uuid4(),
                    [_make_doc("The token must be stored securely.")],
                    skill_id="test-skill",
                )
    assert report.summary.startswith("Rule engine decision:")
    assert "LLM advisory summary: ok" in report.summary


# ---------------------------------------------------------------------------
# P0: citation traceability
# ---------------------------------------------------------------------------


def test_build_chunk_lookup_maps_pol_and_his_ids():
    from langchain_core.documents import Document

    pol = [Document(page_content="policy text", metadata={"source": "pol.pdf"})]
    his = [Document(page_content="history text", metadata={"source": "his.json"})]
    lookup = _build_chunk_lookup(pol, his)
    assert "POL-1" in lookup
    assert "HIS-1" in lookup
    assert lookup["POL-1"].page_content == "policy text"


def test_resolve_citations_uses_declared_chunk_ids():
    from langchain_core.documents import Document

    pol = Document(
        page_content="Encryption must use AES-256.",
        metadata={"source": "policy.pdf", "document_id": "abc123", "page": 3},
    )
    lookup = {"POL-1": pol}

    llm_sources = [
        {"chunk_id": "POL-1", "quote": "Encryption must use AES-256."},
    ]
    citations = _resolve_citations_from_llm(llm_sources, lookup)
    assert len(citations) == 1
    assert citations[0].file == "policy.pdf"
    assert citations[0].excerpt == "Encryption must use AES-256."
    assert citations[0].page == 3


def test_resolve_citations_skips_unknown_chunk_ids():
    from langchain_core.documents import Document

    pol = Document(page_content="policy text", metadata={"source": "p.pdf"})
    lookup = {"POL-1": pol}
    llm_sources = [{"chunk_id": "POL-99", "quote": "nonexistent"}]
    citations = _resolve_citations_from_llm(llm_sources, lookup)
    assert citations == []


def test_resolve_citations_deduplicates_chunk_ids():
    from langchain_core.documents import Document

    pol = Document(page_content="policy text", metadata={"source": "p.pdf"})
    lookup = {"POL-1": pol}
    llm_sources = [
        {"chunk_id": "POL-1", "quote": "first"},
        {"chunk_id": "POL-1", "quote": "duplicate"},
    ]
    citations = _resolve_citations_from_llm(llm_sources, lookup)
    assert len(citations) == 1


def test_resolve_citations_history_prefix_in_evidence_link():
    from langchain_core.documents import Document

    his = Document(
        page_content="old finding",
        metadata={"source": "history/t1/v1.json", "document_id": "d1"},
    )
    lookup = {"HIS-1": his}
    llm_sources = [{"chunk_id": "HIS-1", "quote": "old finding"}]
    citations = _resolve_citations_from_llm(llm_sources, lookup)
    assert citations[0].evidence_link.startswith("history://")


def test_graph_registry_exports_assessment_mermaid():
    from app.agent.graph.graph_topology import GRAPH_REGISTRY

    assert "docsentinel_assessment" in GRAPH_REGISTRY
    compiled = GRAPH_REGISTRY["docsentinel_assessment"][1]()
    mermaid = compiled.get_graph(xray=True).draw_mermaid()
    assert "draft_assessment" in mermaid
    assert "persist_gate3_control_evidence" in mermaid


@pytest.mark.asyncio
async def test_citations_from_reviewer_output_used_over_fallback():
    """Reviewer chunk_id sources become the report citations."""
    from langchain_core.documents import Document

    skill = _make_skill()
    pol_doc = Document(
        page_content="Access tokens must expire within 1 hour.",
        metadata={"source": "policy.pdf", "document_id": "pol001", "page": 5},
    )

    reviewer_response = (
        '{"summary":"ok","confidence":0.9,"risk_items":[],'
        '"compliance_gaps":[],"remediations":[],'
        '"sources":[{"chunk_id":"POL-1",'
        '"quote":"Access tokens must expire within 1 hour."}]}'
    )

    call_num = 0

    async def mock_llm(system_prompt, user_prompt):
        nonlocal call_num
        call_num += 1
        # Drafter and evidence calls get a generic response; reviewer gets
        # the citation-rich one.
        if "Reviewer" in system_prompt or "Validate" in system_prompt:
            return reviewer_response
        return '{"summary":"draft","risk_items":[]}'

    with patch("app.agent.orchestrator.get_skill_service") as mock_svc:
        inst = MagicMock()
        inst.get_skill.return_value = skill
        inst.list_skills.return_value = [skill]
        mock_svc.return_value = inst

        with patch("app.agent.orchestrator.invoke_llm", side_effect=mock_llm):
            with patch("app.agent.orchestrator.get_kb_service") as mock_kb_svc:
                mock_kb = MagicMock()
                mock_kb.query = AsyncMock(return_value=[pol_doc])
                mock_kb.query_history_responses.return_value = []
                mock_kb_svc.return_value = mock_kb

                report = await run_assessment(
                    uuid4(), [_make_doc()], skill_id="test-skill"
                )

    assert len(report.sources) == 1
    assert report.sources[0].file == "policy.pdf"
    assert report.sources[0].excerpt == "Access tokens must expire within 1 hour."


@pytest.mark.asyncio
async def test_langgraph_assessment_persists_gate3_control_evidence(
    monkeypatch,
    tmp_path,
):
    from sqlmodel import Session, SQLModel, create_engine, select

    from app.agent.graph import assessment_graph
    from app.models.governance import ControlEvidenceItem, ControlInstance, Project

    engine = create_engine(
        f"sqlite:///{tmp_path / 'graph.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    project_id = uuid4()
    with Session(engine) as session:
        session.add(Project(id=project_id, name="Graph project"))
        session.commit()

    monkeypatch.setattr(assessment_graph, "_session_factory", lambda: Session(engine))

    skill = _make_skill()
    reviewer_response = """
    {
      "summary": "Gate 3 evidence generated",
      "confidence": 0.82,
      "risk_items": [],
      "compliance_gaps": [
        {
          "control_or_clause": "SCD-001",
          "gap_description": "Threat model evidence is incomplete.",
          "evidence_suggestion": "Attach approved threat model.",
          "framework": "generic-ssdlc",
          "confidence": 0.8
        }
      ],
      "remediations": []
    }
    """

    with _patch_deps(skill, llm_response=reviewer_response):
        report = await run_assessment(
            uuid4(),
            [_make_doc("Threat model is pending review.")],
            project_id=str(project_id),
            phase="design",
            skill_id="test-skill",
        )

    with Session(engine) as session:
        controls = session.exec(select(ControlInstance)).all()
        evidence_items = session.exec(select(ControlEvidenceItem)).all()

    assert report.summary.startswith("Rule engine decision:")
    assert "LLM advisory summary: Gate 3 evidence generated" in report.summary
    assert len(controls) == 1
    assert controls[0].control_id == "SCD-001"
    assert controls[0].status == "evidence_submitted"
    assert len(evidence_items) == 1
    assert evidence_items[0].control_instance_id == controls[0].id


# ---------------------------------------------------------------------------
# P1: large-document map-reduce
# ---------------------------------------------------------------------------


def test_split_text_with_overlap_small_text_unchanged():
    text = "short text"
    chunks = _split_text_with_overlap(text, chunk_size=100, overlap=10)
    assert chunks == [text]


def test_split_text_with_overlap_produces_multiple_chunks():
    text = ("word " * 500).strip()  # ~2500 chars
    chunks = _split_text_with_overlap(text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 2


def test_split_text_with_overlap_chunks_cover_full_document():
    text = ("abc " * 1000).strip()
    chunks = _split_text_with_overlap(text, chunk_size=500, overlap=50)
    # Every character in the original should appear in at least one chunk.
    combined = "".join(chunks)
    # The combined length >= original (overlap means repetition)
    assert len(combined) >= len(text)


@pytest.mark.asyncio
async def test_large_document_triggers_map_reduce():
    """Documents exceeding _LARGE_DOC_THRESHOLD must invoke MergeAgent."""
    from app.agent.orchestrator import _LARGE_DOC_THRESHOLD

    skill = _make_skill()
    large_content = "Security controls are critical. " * (
        (_LARGE_DOC_THRESHOLD // 30) + 10
    )

    merge_called = False

    async def mock_llm(system_prompt, user_prompt):
        nonlocal merge_called
        if "MergeAgent" in system_prompt:
            merge_called = True
        return '{"summary":"merged","risk_items":[]}'

    with patch("app.agent.orchestrator.get_skill_service") as mock_svc:
        inst = MagicMock()
        inst.get_skill.return_value = skill
        inst.list_skills.return_value = [skill]
        mock_svc.return_value = inst

        with patch("app.agent.orchestrator.invoke_llm", side_effect=mock_llm):
            with patch("app.agent.orchestrator.get_kb_service") as mock_kb_svc:
                mock_kb = MagicMock()
                mock_kb.query = AsyncMock(return_value=[])
                mock_kb.query_history_responses.return_value = []
                mock_kb_svc.return_value = mock_kb

                await run_assessment(
                    uuid4(),
                    [_make_doc(content=large_content)],
                    skill_id="test-skill",
                )

    assert merge_called, "MergeAgent was not invoked for a large document"
