"""Tests for KB history storage granularity (P2 fix)."""

from unittest.mock import MagicMock


def _make_kb():
    """Return a KnowledgeBaseService with an in-memory Chroma stub."""
    from app.kb.service import KnowledgeBaseService

    kb = object.__new__(KnowledgeBaseService)
    kb._initialized = False

    # Stub the history store with a real in-memory list so we can inspect docs.
    stored_docs: list = []
    stored_ids: list = []

    mock_store = MagicMock()

    def fake_add_documents(docs, ids=None):
        stored_docs.extend(docs)
        if ids:
            stored_ids.extend(ids)

    mock_store.add_documents.side_effect = fake_add_documents
    kb._history_store = mock_store
    kb._stored_docs = stored_docs
    kb._stored_ids = stored_ids
    return kb


def test_history_stores_summary_as_separate_doc():
    kb = _make_kb()
    kb.add_history_response(
        task_id="t1",
        version=1,
        scenario_id=None,
        report_json={
            "summary": "All controls passed.",
            "risk_items": [],
            "compliance_gaps": [],
        },
    )
    texts = [d.page_content for d in kb._stored_docs]
    assert any("All controls passed." in t for t in texts)


def test_history_stores_each_risk_item_separately():
    kb = _make_kb()
    report = {
        "summary": "Two risks found.",
        "risk_items": [
            {"title": "Weak Auth", "severity": "high", "description": "No MFA."},
            {
                "title": "Open Port",
                "severity": "medium",
                "description": "Port 22 exposed.",
            },
        ],
        "compliance_gaps": [],
    }
    kb.add_history_response("t2", 1, None, report)
    texts = [d.page_content for d in kb._stored_docs]

    assert any("Weak Auth" in t for t in texts)
    assert any("Open Port" in t for t in texts)
    # Each risk item is its own document — not merged into one blob.
    weak_auth_docs = [t for t in texts if "Weak Auth" in t]
    open_port_docs = [t for t in texts if "Open Port" in t]
    assert len(weak_auth_docs) == 1
    assert len(open_port_docs) == 1


def test_history_stores_each_compliance_gap_separately():
    kb = _make_kb()
    report = {
        "summary": "Gap found.",
        "risk_items": [],
        "compliance_gaps": [
            {
                "control_or_clause": "A.9.1",
                "gap_description": "No access review process.",
                "framework": "ISO 27001",
            },
            {
                "control_or_clause": "Art. 32",
                "gap_description": "Encryption not documented.",
                "framework": "GDPR",
            },
        ],
    }
    kb.add_history_response("t3", 1, None, report)
    texts = [d.page_content for d in kb._stored_docs]

    assert any("A.9.1" in t for t in texts)
    assert any("Art. 32" in t for t in texts)


def test_history_doc_count_equals_summary_plus_findings():
    kb = _make_kb()
    report = {
        "summary": "Summary text.",
        "risk_items": [
            {"title": "R1", "severity": "low", "description": "d1"},
            {"title": "R2", "severity": "high", "description": "d2"},
        ],
        "compliance_gaps": [
            {"control_or_clause": "G1", "gap_description": "g1", "framework": "ISO"},
        ],
    }
    kb.add_history_response("t4", 1, "s1", report)
    # 1 summary + 2 risk_items + 1 compliance_gap = 4 docs
    assert len(kb._stored_docs) == 4


def test_history_each_doc_has_unique_chunk_id():
    kb = _make_kb()
    report = {
        "summary": "s",
        "risk_items": [{"title": "R", "severity": "low", "description": "d"}],
        "compliance_gaps": [],
    }
    kb.add_history_response("t5", 1, None, report)
    ids = kb._stored_ids
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs detected"


def test_history_metadata_carries_task_and_version():
    kb = _make_kb()
    report = {"summary": "ok", "risk_items": [], "compliance_gaps": []}
    kb.add_history_response("task-xyz", 3, "scene-1", report)
    for doc in kb._stored_docs:
        assert doc.metadata["task_id"] == "task-xyz"
        assert doc.metadata["version"] == 3
        assert doc.metadata["scenario_id"] == "scene-1"


def test_history_severity_included_in_risk_item_content():
    kb = _make_kb()
    report = {
        "summary": "s",
        "risk_items": [
            {
                "title": "SQL Injection",
                "severity": "critical",
                "description": "Unsanitized input.",
            }
        ],
        "compliance_gaps": [],
    }
    kb.add_history_response("t6", 1, None, report)
    texts = [d.page_content for d in kb._stored_docs]
    risk_texts = [t for t in texts if "SQL Injection" in t]
    assert len(risk_texts) == 1
    assert "CRITICAL" in risk_texts[0]
