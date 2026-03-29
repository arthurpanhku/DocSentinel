"""
Graph-based RAG service using LightRAG.

Builds a knowledge graph from ingested documents, enabling entity-relationship
aware retrieval. Particularly valuable for cybersecurity documents where
controls, frameworks, vulnerabilities, and policies form a connected graph
(e.g., "ISO 27001 A.9.4.1" → "access control" → "password policy").

Supports four query modes:
  - naive: vector similarity only (like traditional RAG)
  - local: entity-centric graph traversal
  - global: community-level summaries
  - hybrid: combines all modes for best results
"""

import asyncio
import logging
from pathlib import Path

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy singleton to avoid repeated initialization
_instance: "GraphRAGService | None" = None
_instance_lock = asyncio.Lock()


async def get_graph_rag_service() -> "GraphRAGService":
    """Get or create the singleton GraphRAGService (with async init)."""
    global _instance
    if _instance is not None:
        return _instance
    async with _instance_lock:
        if _instance is not None:
            return _instance
        svc = GraphRAGService()
        await svc.initialize()
        _instance = svc
        return _instance


class GraphRAGService:
    """Wrapper around LightRAG for graph-based knowledge retrieval."""

    def __init__(self) -> None:
        self._rag = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize LightRAG instance with project LLM and embedding config."""
        if self._initialized:
            return

        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc

        working_dir = Path(settings.LIGHTRAG_WORKING_DIR)
        working_dir.mkdir(parents=True, exist_ok=True)

        self._rag = LightRAG(
            working_dir=str(working_dir),
            llm_model_func=self._llm_adapter,
            llm_model_name=self._get_model_name(),
            embedding_func=EmbeddingFunc(
                embedding_dim=384,  # all-MiniLM-L6-v2 outputs 384-dim vectors
                max_token_size=512,
                func=self._embedding_adapter,
            ),
            chunk_token_size=1200,
            chunk_overlap_token_size=100,
        )
        await self._rag.initialize_storages()
        self._initialized = True
        logger.info("GraphRAG initialized at %s", working_dir)

    def _get_model_name(self) -> str:
        if settings.LLM_PROVIDER == "openai":
            return settings.OPENAI_MODEL
        return settings.OLLAMA_MODEL

    async def _llm_adapter(
        self,
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list | None = None,
        keyword_extraction: bool = False,
        **kwargs,
    ) -> str:
        """Adapt project LLM to LightRAG's expected function signature."""
        from app.llm.base import invoke_llm

        sys_prompt = system_prompt or "You are a helpful assistant."
        return await invoke_llm(sys_prompt, prompt)

    async def _embedding_adapter(
        self, texts: list[str], **kwargs
    ) -> np.ndarray:
        """Adapt project embedding model to LightRAG's expected signature."""
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )
        vectors = embeddings.embed_documents(texts)
        return np.array(vectors)

    async def insert(self, text: str, metadata: dict | None = None) -> None:
        """Insert document text into the knowledge graph."""
        if not self._initialized or not self._rag:
            await self.initialize()
        try:
            await self._rag.ainsert(text)
            source = (metadata or {}).get("source", "unknown")
            logger.info("GraphRAG: inserted document from %s", source)
        except Exception as e:
            logger.error("GraphRAG insert failed: %s", e)

    async def query(
        self,
        query: str,
        mode: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Query the knowledge graph.

        Returns list of dicts with keys: content, metadata.
        """
        if not self._initialized or not self._rag:
            await self.initialize()

        from lightrag import QueryParam

        query_mode = mode or settings.GRAPH_RAG_QUERY_MODE

        try:
            result = await self._rag.aquery(
                query,
                param=QueryParam(
                    mode=query_mode,
                    only_need_context=True,
                    top_k=top_k,
                ),
            )

            if not result:
                return []

            # LightRAG returns a string when only_need_context=True;
            # split into meaningful chunks for downstream consumption
            chunks = self._split_graph_context(result, query_mode)
            return chunks

        except Exception as e:
            logger.error("GraphRAG query failed: %s", e)
            return []

    def _split_graph_context(
        self, context: str, mode: str
    ) -> list[dict]:
        """Split LightRAG context string into structured chunk dicts."""
        if not context or not context.strip():
            return []

        # Split by double newlines to get logical sections
        sections = [s.strip() for s in context.split("\n\n") if s.strip()]

        chunks = []
        for i, section in enumerate(sections):
            if len(section) < 20:  # skip trivially short fragments
                continue
            chunks.append(
                {
                    "content": section,
                    "metadata": {
                        "source": "graph_rag",
                        "source_type": "graph",
                        "graph_mode": mode,
                        "chunk_index": i,
                    },
                }
            )
        return chunks

    async def finalize(self) -> None:
        """Clean up LightRAG resources."""
        if self._rag and self._initialized:
            await self._rag.finalize_storages()
            self._initialized = False
            logger.info("GraphRAG finalized")
