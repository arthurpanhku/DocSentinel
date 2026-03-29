"""
Knowledge base: chunk, embed, store in Chroma; optional graph RAG via LightRAG.
Hybrid retrieval merges vector similarity + entity-relationship graph.
"""

import hashlib
import json
import logging
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.parser import ParsedDocument

logger = logging.getLogger(__name__)


def _get_embeddings():
    if not hasattr(_get_embeddings, "_emb"):
        _get_embeddings._emb = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )
    return _get_embeddings._emb


class KnowledgeBaseService:
    """Hybrid KB: ChromaDB (vector) + LightRAG (graph) for enriched retrieval.

    Use get_kb_service() to obtain the shared singleton instance.
    """

    CHUNK_SIZE = 1024
    CHUNK_OVERLAP = 128
    COLLECTION_NAME = "security_agent_kb"
    HISTORY_COLLECTION_NAME = "security_agent_history"

    _instance: "KnowledgeBaseService | None" = None

    def __new__(cls) -> "KnowledgeBaseService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._vectorstore = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            persist_directory=str(persist_dir),
        )
        self._history_store = Chroma(
            collection_name=self.HISTORY_COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            persist_directory=str(persist_dir),
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", " ", ""],
        )
        self._graph_rag_enabled = settings.ENABLE_GRAPH_RAG

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    async def add_document(
        self, parsed: ParsedDocument, document_id: str | None = None
    ) -> str:
        """Ingest one parsed document into vector store + graph RAG."""
        content = (
            parsed.content if isinstance(parsed.content, str) else str(parsed.content)
        )
        doc_id = document_id or hashlib.sha256(content.encode()).hexdigest()[:16]

        # --- Vector store (Chroma) ---
        chunks = self._splitter.split_text(content)
        if chunks:
            docs = [
                Document(
                    page_content=c,
                    metadata={
                        "source": parsed.metadata.filename,
                        "document_id": doc_id,
                        "type": parsed.metadata.type,
                        "parser_engine": parsed.metadata.parser_engine,
                    },
                )
                for c in chunks
            ]
            self._vectorstore.add_documents(
                docs, ids=[f"{doc_id}_{i}" for i in range(len(docs))]
            )

        # --- Graph RAG (LightRAG) ---
        if self._graph_rag_enabled:
            await self._insert_to_graph(content, parsed, doc_id)

        return doc_id

    def add_document_sync(
        self, parsed: ParsedDocument, document_id: str | None = None
    ) -> str:
        """Synchronous wrapper for add_document (for non-async callers)."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in an async context — schedule as task
            # Fall back to vector-only for sync callers in async context
            return self._add_document_vector_only(parsed, document_id)

        return asyncio.run(self.add_document(parsed, document_id))

    def _add_document_vector_only(
        self, parsed: ParsedDocument, document_id: str | None = None
    ) -> str:
        """Vector-store-only ingest (no graph RAG)."""
        content = (
            parsed.content if isinstance(parsed.content, str) else str(parsed.content)
        )
        doc_id = document_id or hashlib.sha256(content.encode()).hexdigest()[:16]
        chunks = self._splitter.split_text(content)
        if not chunks:
            return doc_id
        docs = [
            Document(
                page_content=c,
                metadata={
                    "source": parsed.metadata.filename,
                    "document_id": doc_id,
                    "type": parsed.metadata.type,
                    "parser_engine": parsed.metadata.parser_engine,
                },
            )
            for c in chunks
        ]
        self._vectorstore.add_documents(
            docs, ids=[f"{doc_id}_{i}" for i in range(len(docs))]
        )
        return doc_id

    async def _insert_to_graph(
        self, content: str, parsed: ParsedDocument, doc_id: str
    ) -> None:
        """Insert document text into LightRAG knowledge graph."""
        try:
            from app.kb.graph_rag import get_graph_rag_service

            graph_svc = await get_graph_rag_service()
            await graph_svc.insert(
                content,
                metadata={
                    "source": parsed.metadata.filename,
                    "document_id": doc_id,
                    "type": parsed.metadata.type,
                },
            )
        except Exception as e:
            logger.warning("Graph RAG insert failed (non-blocking): %s", e)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def query(self, query: str, top_k: int = 5) -> list[Document]:
        """
        Hybrid RAG query: merge vector similarity + graph retrieval.

        When graph RAG is disabled, falls back to vector-only (original behavior).
        """
        # Vector search (always)
        vector_docs = self._vectorstore.similarity_search(query, k=top_k)

        # Graph search (when enabled)
        if self._graph_rag_enabled:
            graph_docs = await self._query_graph(query, top_k=top_k)
            return self._merge_results(vector_docs, graph_docs, top_k)

        return vector_docs

    def query_sync(self, query: str, top_k: int = 5) -> list[Document]:
        """Synchronous vector-only query (backward compatible)."""
        return self._vectorstore.similarity_search(query, k=top_k)

    async def _query_graph(self, query: str, top_k: int = 5) -> list[Document]:
        """Query LightRAG and convert results to Document objects."""
        try:
            from app.kb.graph_rag import get_graph_rag_service

            graph_svc = await get_graph_rag_service()
            raw_chunks = await graph_svc.query(query, top_k=top_k)

            return [
                Document(
                    page_content=chunk["content"],
                    metadata=chunk.get("metadata", {}),
                )
                for chunk in raw_chunks
            ]
        except Exception as e:
            logger.warning("Graph RAG query failed (non-blocking): %s", e)
            return []

    def _merge_results(
        self,
        vector_docs: list[Document],
        graph_docs: list[Document],
        top_k: int,
    ) -> list[Document]:
        """
        Merge and deduplicate results from vector and graph retrieval.

        Strategy: interleave vector and graph results, deduplicate by content,
        prefer vector results for duplicates (they have richer metadata).
        """
        seen_content: set[str] = set()
        merged: list[Document] = []

        # Interleave: vector first for each position, then graph
        v_iter = iter(vector_docs)
        g_iter = iter(graph_docs)

        while len(merged) < top_k * 2:  # allow up to 2x for richer context
            # Take from vector
            v_doc = next(v_iter, None)
            if v_doc:
                key = v_doc.page_content[:200]
                if key not in seen_content:
                    seen_content.add(key)
                    merged.append(v_doc)

            # Take from graph
            g_doc = next(g_iter, None)
            if g_doc:
                key = g_doc.page_content[:200]
                if key not in seen_content:
                    seen_content.add(key)
                    merged.append(g_doc)

            # Both exhausted
            if v_doc is None and g_doc is None:
                break

        return merged

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def add_history_response(
        self,
        task_id: str,
        version: int,
        scenario_id: str | None,
        report_json: dict,
    ) -> str:
        content = (
            f"task_id={task_id}\nversion={version}\nscenario_id={scenario_id}\n"
            f"{json.dumps(report_json, ensure_ascii=False)}"
        )
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        chunks = self._splitter.split_text(content)
        docs = [
            Document(
                page_content=c,
                metadata={
                    "source": f"history/{task_id}/v{version}.json",
                    "document_id": doc_id,
                    "type": "history_response",
                    "task_id": task_id,
                    "version": version,
                    "scenario_id": scenario_id,
                    "chunk_id": f"{doc_id}_{i}",
                },
            )
            for i, c in enumerate(chunks)
        ]
        if docs:
            self._history_store.add_documents(
                docs, ids=[f"{doc_id}_{i}" for i in range(len(docs))]
            )
        return doc_id

    def query_history_responses(self, query: str, top_k: int = 3) -> list[Document]:
        return self._history_store.similarity_search(query, k=top_k)

    # ------------------------------------------------------------------
    # Reindex
    # ------------------------------------------------------------------

    async def reindex_directory(self, directory: str) -> dict:
        from app.parser import parse_file

        root = Path(directory)
        if not root.exists():
            return {
                "directory": directory,
                "indexed": 0,
                "errors": ["directory_not_found"],
            }
        indexed = 0
        errors: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"}:
                continue
            try:
                parsed = parse_file(path.read_bytes(), path.name)
                await self.add_document(parsed)
                indexed += 1
            except Exception as e:
                errors.append(f"{path.name}: {e!s}")
        return {"directory": str(root), "indexed": indexed, "errors": errors}

    def reindex_directory_sync(self, directory: str) -> dict:
        """Synchronous reindex (vector-only, for non-async callers)."""
        from app.parser import parse_file

        root = Path(directory)
        if not root.exists():
            return {
                "directory": directory,
                "indexed": 0,
                "errors": ["directory_not_found"],
            }
        indexed = 0
        errors: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"}:
                continue
            try:
                parsed = parse_file(path.read_bytes(), path.name)
                self._add_document_vector_only(parsed)
                indexed += 1
            except Exception as e:
                errors.append(f"{path.name}: {e!s}")
        return {"directory": str(root), "indexed": indexed, "errors": errors}


def get_kb_service() -> KnowledgeBaseService:
    """Return the shared singleton KnowledgeBaseService instance."""
    return KnowledgeBaseService()
