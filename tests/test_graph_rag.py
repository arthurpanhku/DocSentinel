"""Tests for graph RAG service and hybrid KB retrieval."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.kb.service import KnowledgeBaseService
from app.models.parser import ParsedDocument, ParsedDocumentMetadata


@pytest.fixture
def parsed_doc():
    return ParsedDocument(
        content="Password must be 12+ chars per ISO 27001.",
        metadata=ParsedDocumentMetadata(
            filename="policy.md", type="md", parser_engine="legacy"
        ),
    )


@pytest.mark.asyncio
async def test_add_document_inserts_to_graph_when_enabled(parsed_doc):
    """When ENABLE_GRAPH_RAG=True, add_document also inserts into graph."""
    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = "/tmp/test_chroma"
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = True

        with patch("app.kb.service.Chroma"):
            with patch("app.kb.service._get_embeddings"):
                kb = KnowledgeBaseService()

                with patch.object(
                    kb, "_insert_to_graph", new_callable=AsyncMock
                ) as mock_graph:
                    await kb.add_document(parsed_doc)
                    mock_graph.assert_called_once()


@pytest.mark.asyncio
async def test_add_document_skips_graph_when_disabled(parsed_doc):
    """When ENABLE_GRAPH_RAG=False, graph insert is skipped."""
    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = "/tmp/test_chroma"
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = False

        with patch("app.kb.service.Chroma"):
            with patch("app.kb.service._get_embeddings"):
                kb = KnowledgeBaseService()

                with patch.object(
                    kb, "_insert_to_graph", new_callable=AsyncMock
                ) as mock_graph:
                    await kb.add_document(parsed_doc)
                    mock_graph.assert_not_called()


@pytest.mark.asyncio
async def test_query_hybrid_merges_vector_and_graph():
    """Hybrid query returns merged results from vector + graph."""
    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = "/tmp/test_chroma"
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = True

        with patch("app.kb.service.Chroma") as mock_chroma_cls:
            with patch("app.kb.service._get_embeddings"):
                # Mock vector store results
                mock_vector_doc = MagicMock()
                mock_vector_doc.page_content = "Vector result about encryption"
                mock_vector_doc.metadata = {
                    "source": "policy.pdf",
                    "source_type": "vector",
                }

                mock_chroma_inst = MagicMock()
                mock_chroma_inst.similarity_search.return_value = [mock_vector_doc]
                mock_chroma_cls.return_value = mock_chroma_inst

                kb = KnowledgeBaseService()

                # Mock graph results
                mock_graph_doc = MagicMock()
                mock_graph_doc.page_content = "Graph: encryption → AES-256"
                mock_graph_doc.metadata = {
                    "source": "graph_rag",
                    "source_type": "graph",
                }

                with patch.object(
                    kb,
                    "_query_graph",
                    new_callable=AsyncMock,
                    return_value=[mock_graph_doc],
                ):
                    results = await kb.query("encryption standards", top_k=5)

                    # Should have both vector and graph results
                    assert len(results) == 2
                    contents = [r.page_content for r in results]
                    assert any("Vector" in c for c in contents)
                    assert any("Graph" in c for c in contents)


@pytest.mark.asyncio
async def test_query_vector_only_when_graph_disabled():
    """When graph RAG is disabled, query returns vector-only results."""
    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = "/tmp/test_chroma"
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = False

        with patch("app.kb.service.Chroma") as mock_chroma_cls:
            with patch("app.kb.service._get_embeddings"):
                mock_doc = MagicMock()
                mock_doc.page_content = "Vector only"
                mock_doc.metadata = {}

                mock_inst = MagicMock()
                mock_inst.similarity_search.return_value = [mock_doc]
                mock_chroma_cls.return_value = mock_inst

                kb = KnowledgeBaseService()
                results = await kb.query("test", top_k=5)

                assert len(results) == 1
                assert results[0].page_content == "Vector only"


def test_merge_deduplicates_by_content():
    """Merge results deduplicates documents with same content prefix."""
    with patch("app.kb.service.settings") as mock_settings:
        mock_settings.CHROMA_PERSIST_DIR = "/tmp/test_chroma"
        mock_settings.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_settings.ENABLE_GRAPH_RAG = True

        with patch("app.kb.service.Chroma"):
            with patch("app.kb.service._get_embeddings"):
                kb = KnowledgeBaseService()

                # Create two docs with same content
                doc1 = MagicMock()
                doc1.page_content = "Same content about access control"
                doc1.metadata = {"source_type": "vector"}

                doc2 = MagicMock()
                doc2.page_content = "Same content about access control"
                doc2.metadata = {"source_type": "graph"}

                doc3 = MagicMock()
                doc3.page_content = "Different content about encryption"
                doc3.metadata = {"source_type": "graph"}

                merged = kb._merge_results([doc1], [doc2, doc3], top_k=5)

                # doc2 should be deduplicated (same content prefix as doc1)
                assert len(merged) == 2
