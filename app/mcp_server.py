"""DocSentinel MCP server for stdio and Streamable HTTP transports."""

import json

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.agent.orchestrator import run_assessment
from app.agent_gateway.service import agent_gateway
from app.core.config import settings

mcp = FastMCP(
    "DocSentinel",
    instructions=(
        "Security assessment tools. Document paths must be inside configured "
        "MCP_DOCUMENT_ROOTS and all agent submissions require human review."
    ),
    json_response=True,
    stateless_http=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=settings.agent_gateway_allowed_hosts,
        allowed_origins=settings.agent_gateway_allowed_origins,
    ),
)


@mcp.tool()
async def submit_document_assessment(
    file_path: str,
    scenario_id: str = "default",
    project_id: str = "",
    phase: str = "auto",
    skill_id: str = "",
) -> str:
    """Submit an approved local document for an asynchronous security assessment."""
    try:
        result = await agent_gateway.submit_document(
            file_path,
            scenario_id=scenario_id or None,
            project_id=project_id or None,
            phase=phase,
            skill_id=skill_id or None,
            runner=run_assessment,
            source="mcp",
        )
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def get_assessment_status(task_id: str) -> str:
    """Get the current state and available report for an assessment task."""
    try:
        return json.dumps(agent_gateway.get_assessment(task_id))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def assess_document(file_path: str, scenario_id: str = "default") -> str:
    """Compatibility tool that waits for the submitted assessment draft."""
    try:
        created = await agent_gateway.submit_document(
            file_path,
            scenario_id=scenario_id or None,
            runner=run_assessment,
            source="mcp",
        )
        result = await agent_gateway.wait_for_assessment(created["task_id"])
        if result.get("report"):
            return json.dumps(result["report"], indent=2)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def query_knowledge_base(query: str, top_k: int = 3) -> str:
    """Query approved chunks in the internal security knowledge base."""
    try:
        return json.dumps(
            await agent_gateway.query_knowledge_base(query, top_k),
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def get_agent_gateway_status() -> str:
    """Return enabled protocols, access mode, and exposed capabilities."""
    return agent_gateway.status().model_dump_json(indent=2)


@mcp.resource("kb://stats")
def get_kb_stats() -> str:
    """Get non-sensitive knowledge-base runtime information."""
    return json.dumps({"status": "active", "backend": "chroma"})


if __name__ == "__main__":
    mcp.run()
