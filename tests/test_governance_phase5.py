from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.core.db import get_session
from app.kb.service import KnowledgeBaseService
from app.main import app
from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.services import graphify_kb, light_rag


def _override_session(engine):
    def _override():
        with Session(engine) as session:
            yield session

    return _override


def test_policy_packs_endpoint_returns_base_and_eight_overlays(client):
    response = client.get("/api/v1/policy-packs")

    assert response.status_code == 200
    data = response.json()["data"]
    overlay_ids = {item["id"] for item in data["overlays"]}
    all_ids = {item["id"] for item in data["all"]}
    assert data["active"]["id"] == "generic-ssdlc"
    assert "generic-ssdlc" in all_ids
    assert overlay_ids == {
        "nist-ssdf",
        "singapore-mas-trm",
        "iso-27001-2022",
        "eu-ai-act",
        "iso-42001",
        "china-mlps2",
        "owasp-samm",
        "eu-cra",
    }


@pytest.mark.asyncio
async def test_kb_ingest_single_entry_writes_graphify_and_graph_rag(
    monkeypatch,
    tmp_path,
):
    root = tmp_path / "kbroot"
    upload_root = root / "knowledge_base" / "uploads"
    monkeypatch.setattr(graphify_kb, "_ROOT", root)
    monkeypatch.setattr(graphify_kb, "_UPLOAD_ROOT", upload_root)
    monkeypatch.setattr(graphify_kb, "RAW_DIR", upload_root / "raw")
    monkeypatch.setattr(
        graphify_kb,
        "DISTILLED_DIR",
        upload_root / "distilled",
    )
    monkeypatch.setattr(
        graphify_kb,
        "GRAPH_DIR",
        upload_root / "graphs",
    )
    monkeypatch.setattr(light_rag, "_ROOT", root)
    light_rag._build_index.cache_clear()

    parsed = ParsedDocument(
        content="UNIQUEPHASE5CONTROL evidence must be retained for release.",
        metadata=ParsedDocumentMetadata(
            filename="phase5.md",
            type="md",
            parser_engine="legacy",
        ),
    )

    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = str(tmp_path / "chroma")
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = True
        with patch("app.kb.service.Chroma"), patch("app.kb.service._get_embeddings"):
            kb = KnowledgeBaseService()
            with patch.object(kb, "_insert_to_graph", new_callable=AsyncMock) as graph:
                result = await kb.ingest(parsed, document_id="phase5-doc")

    assert result["stores"] == {
        "chroma": True,
        "graph_rag": True,
        "light_rag": True,
    }
    graph.assert_awaited_once()
    chunks = light_rag.search_knowledge("UNIQUEPHASE5CONTROL", top_k=1)
    assert chunks
    assert "UNIQUEPHASE5CONTROL" in chunks[0].content


def test_pallas_lens_scores_project_with_evidence(client, tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'phase5.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    app.dependency_overrides[get_session] = _override_session(engine)
    try:
        created = client.post(
            "/api/v1/projects",
            json={
                "name": "Release Radar",
                "risk_tier": "high",
                "compliance_frameworks": ["nist-ssdf"],
            },
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        controls = client.get(f"/api/v1/projects/{project_id}/controls")
        assert controls.status_code == 200
        assert controls.json()["meta"]["count"] > 0
        control_id = controls.json()["data"][0]["control_id"]

        evidence = client.post(
            f"/api/v1/projects/{project_id}/controls/{control_id}/evidence",
            json={"content": "Control evidence attached for review."},
        )
        assert evidence.status_code == 200

        lens = client.get(f"/api/v1/projects/{project_id}/pallas-lens")
        assert lens.status_code == 200
        data = lens.json()["data"]
    finally:
        app.dependency_overrides.clear()

    assert data["readiness_score"] >= 0
    assert data["control_totals"]["evidence_items"] == 1
    assert data["next_actions"]
