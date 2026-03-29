import json
import os
import uuid

from mcp.server.fastmcp import FastMCP

from app.agent.orchestrator import run_assessment
from app.kb.service import get_kb_service
from app.parser import parse_file

mcp = FastMCP("DocSentinel")


@mcp.tool()
async def assess_document(file_path: str, scenario_id: str = "default") -> str:
    """
    Assess a security document (PDF, Word, etc.) and return a risk report.

    Args:
        file_path: Absolute path to the file to be assessed.
        scenario_id: The assessment scenario ID (default: "default").

    Returns:
        JSON string containing the assessment report (risks, gaps, remediations).
    """
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        with open(file_path, "rb") as f:
            raw_content = f.read()
        parsed_doc = parse_file(raw_content, os.path.basename(file_path))
    except Exception as e:
        return json.dumps({"error": f"Failed to parse file: {str(e)}"})

    try:
        task_id = uuid.uuid4()

        report = await run_assessment(
            task_id=task_id, parsed_documents=[parsed_doc], scenario_id=scenario_id
        )

        return report.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": f"Assessment failed: {str(e)}"})


@mcp.tool()
async def query_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Query the internal security knowledge base (policies, standards).

    Args:
        query: The search query (e.g., "password complexity requirements").
        top_k: Number of results to return.

    Returns:
        JSON string with retrieved document chunks.
    """
    kb = get_kb_service()
    results = await kb.query(query, top_k)

    serialized_results = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in results
    ]

    return json.dumps(serialized_results, indent=2)


@mcp.resource("kb://stats")
def get_kb_stats() -> str:
    """Get statistics about the knowledge base (document count, etc.)"""
    return json.dumps({"status": "active", "backend": "chroma"})


if __name__ == "__main__":
    mcp.run()
