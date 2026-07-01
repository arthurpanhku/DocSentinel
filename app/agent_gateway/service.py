"""Protocol-neutral boundary for agent-triggered DocSentinel operations."""

import json
from typing import Any

from app.agent.orchestrator import run_assessment
from app.core.config import settings
from app.core.document_access import document_roots, resolve_document_path
from app.core.guardrails import sanitize_input
from app.kb.service import get_kb_service
from app.models.integration import (
    AgentIntegrationStatus,
    AgentProtocolEndpoint,
)
from app.parser import parse_file
from app.services.assessment_service import AssessmentRunner, assessment_service

ALLOWED_PHASES = {
    "auto",
    "requirements",
    "design",
    "development",
    "testing",
    "deployment",
    "operations",
    "full_ssdlc",
}
MCP_TOOLS = [
    "submit_document_assessment",
    "get_assessment_status",
    "assess_document",
    "query_knowledge_base",
    "get_agent_gateway_status",
]
A2A_SKILLS = [
    "assess_security_document",
    "get_security_assessment",
    "query_security_knowledge",
]


class AgentGateway:
    def status(self) -> AgentIntegrationStatus:
        if not settings.AGENT_GATEWAY_ENABLED:
            access_mode = "disabled"
        elif settings.AGENT_GATEWAY_TOKEN:
            access_mode = "bearer_token"
        else:
            access_mode = "loopback_only"
        return AgentIntegrationStatus(
            enabled=settings.AGENT_GATEWAY_ENABLED,
            access_mode=access_mode,
            protocols=[
                AgentProtocolEndpoint(
                    protocol="mcp",
                    transport="streamable-http",
                    endpoint="/mcp/",
                    enabled=settings.AGENT_GATEWAY_ENABLED,
                ),
                AgentProtocolEndpoint(
                    protocol="a2a",
                    transport="json-rpc",
                    endpoint="/a2a",
                    enabled=settings.AGENT_GATEWAY_ENABLED,
                ),
            ],
            mcp_tools=MCP_TOOLS,
            a2a_skills=A2A_SKILLS,
            document_roots_configured=len(document_roots()),
        )

    async def submit_document(
        self,
        file_path: str,
        *,
        scenario_id: str | None = None,
        project_id: str | None = None,
        phase: str = "auto",
        skill_id: str | None = None,
        runner: AssessmentRunner = run_assessment,
        source: str,
    ) -> dict[str, Any]:
        if phase not in ALLOWED_PHASES:
            raise ValueError(f"Unsupported phase: {phase}")
        document_path = resolve_document_path(file_path)
        if document_path.stat().st_size > settings.upload_max_bytes:
            raise ValueError(f"File exceeds {settings.UPLOAD_MAX_FILE_SIZE_MB}MB limit")
        parsed = parse_file(document_path.read_bytes(), document_path.name)
        parsed.metadata.scenario_id = scenario_id
        parsed.metadata.ssdlc_phase_hint = phase
        sanitize_input(parsed.content if isinstance(parsed.content, str) else "")
        created = await assessment_service.submit(
            [parsed],
            scenario_id=scenario_id,
            project_id=project_id,
            phase=phase,
            skill_id=skill_id,
            collaborative_mode=True,
            runner=runner,
            source=source,
        )
        return {
            "task_id": str(created.task_id),
            "status": created.status,
            "review_required": True,
            "status_url": f"/api/v1/assessments/{created.task_id}",
        }

    def get_assessment(self, task_id: str) -> dict[str, Any]:
        return assessment_service.get(task_id).model_dump(mode="json")

    async def wait_for_assessment(
        self,
        task_id: str,
        *,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        result = await assessment_service.wait_for_terminal(
            task_id,
            timeout_seconds or settings.AGENT_GATEWAY_TASK_TIMEOUT_SECONDS,
        )
        return result.model_dump(mode="json")

    async def query_knowledge_base(self, query: str, top_k: int = 3) -> dict[str, Any]:
        sanitized = sanitize_input(query)
        bounded_top_k = max(1, min(top_k, 10))
        results = await get_kb_service().query(sanitized, bounded_top_k)
        return {
            "chunks": [
                {"content": item.page_content, "metadata": item.metadata}
                for item in results
            ]
        }

    async def handle_a2a_request(self, text: str) -> dict[str, Any]:
        try:
            request = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("A2A input must be a JSON object") from exc
        if not isinstance(request, dict):
            raise ValueError("A2A input must be a JSON object")
        operation = request.get("operation")
        if operation == "assess_document":
            file_path = request.get("file_path")
            if not isinstance(file_path, str) or not file_path:
                raise ValueError("assess_document requires file_path")
            return await self.submit_document(
                file_path,
                scenario_id=_optional_string(request, "scenario_id"),
                project_id=_optional_string(request, "project_id"),
                phase=str(request.get("phase", "auto")),
                skill_id=_optional_string(request, "skill_id"),
                source="a2a",
            )
        if operation == "get_assessment":
            task_id = request.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise ValueError("get_assessment requires task_id")
            return self.get_assessment(task_id)
        if operation == "query_knowledge_base":
            query = request.get("query")
            if not isinstance(query, str) or not query:
                raise ValueError("query_knowledge_base requires query")
            return await self.query_knowledge_base(
                query,
                int(request.get("top_k", 3)),
            )
        if operation == "status":
            return self.status().model_dump(mode="json")
        raise ValueError(f"Unsupported operation: {operation}")


def _optional_string(value: dict[str, Any], key: str) -> str | None:
    item = value.get(key)
    return item if isinstance(item, str) and item else None


agent_gateway = AgentGateway()
