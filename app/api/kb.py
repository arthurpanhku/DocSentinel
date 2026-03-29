"""Knowledge base API: upload document, query (hybrid RAG)."""

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.kb.service import KnowledgeBaseService
from app.parser import parse_file

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


class KBQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class KBReindexRequest(BaseModel):
    directory: str


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):  # noqa: B008
    """Upload a document to the knowledge base (vector + graph RAG)."""
    from app.core.config import settings

    content = await file.read()
    if len(content) > settings.upload_max_bytes:
        raise HTTPException(413, f"File exceeds {settings.UPLOAD_MAX_FILE_SIZE_MB}MB")
    try:
        parsed = parse_file(content, file.filename or "unknown")
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    kb = KnowledgeBaseService()
    doc_id = await kb.add_document(parsed)
    return {"document_id": doc_id}


@router.post("/query")
async def query_kb(body: KBQueryRequest):
    """Hybrid RAG query: vector similarity + graph retrieval."""
    kb = KnowledgeBaseService()
    docs = await kb.query(body.query, top_k=body.top_k)
    return {
        "chunks": [{"content": d.page_content, "metadata": d.metadata} for d in docs]
    }


@router.post("/reindex")
async def reindex_kb(body: KBReindexRequest):
    kb = KnowledgeBaseService()
    return await kb.reindex_directory(body.directory)
