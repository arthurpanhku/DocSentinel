import json
from unittest.mock import AsyncMock

import httpx
import pytest
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest, TaskState
from fastapi.testclient import TestClient
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.agent_gateway.service import agent_gateway
from app.core.config import settings
from app.main import app
from app.models.assessment import AssessmentReport, ReportMetadata


def _report(task_id) -> AssessmentReport:
    return AssessmentReport(
        task_id=str(task_id),
        status="completed",
        summary="Agent-submitted draft",
        confidence=0.8,
        metadata=ReportMetadata(),
    )


@pytest.mark.asyncio
async def test_agent_submission_uses_shared_task_and_requires_review(
    monkeypatch,
    tmp_path,
):
    approved = tmp_path / "approved"
    approved.mkdir()
    document = approved / "design.txt"
    document.write_text("System architecture with privileged access.", encoding="utf-8")
    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(approved))
    runner = AsyncMock(side_effect=lambda task_id, *args, **kwargs: _report(task_id))

    created = await agent_gateway.submit_document(
        str(document),
        phase="design",
        runner=runner,
        source="test-agent",
    )
    result = await agent_gateway.wait_for_assessment(created["task_id"])

    assert created["review_required"] is True
    assert result["status"] == "review_pending"
    assert result["report"]["phase"] == "design"
    runner.assert_awaited_once()


def test_agent_gateway_status_and_token_boundary(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_GATEWAY_TOKEN", "gateway-secret")
    client = TestClient(app, base_url="http://localhost")

    status = client.get("/api/v1/integrations/agents/status")
    assert status.status_code == 200
    assert status.json()["access_mode"] == "bearer_token"
    assert client.get("/.well-known/agent-card.json").status_code == 200

    unauthenticated = client.post("/a2a", json={})
    assert unauthenticated.status_code == 401
    authenticated = client.post(
        "/a2a",
        headers={"Authorization": "Bearer gateway-secret"},
        json={},
    )
    assert authenticated.status_code != 401


@pytest.mark.asyncio
async def test_tokenless_agent_gateway_rejects_non_loopback_client():
    transport = httpx.ASGITransport(app=app, client=("10.10.0.8", 43125))
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://docsentinel.internal",
    ) as client:
        response = await client.post("/a2a", json={})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_a2a_status_round_trip():
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 43123))
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost:8000",
    ) as http_client:
        card = await A2ACardResolver(
            httpx_client=http_client,
            base_url="http://localhost:8000",
        ).get_agent_card()
        client = await create_client(
            agent=card,
            client_config=ClientConfig(
                streaming=False,
                httpx_client=http_client,
            ),
        )
        request = SendMessageRequest(
            message=new_text_message(
                json.dumps({"operation": "status"}),
                role=Role.ROLE_USER,
            )
        )
        responses = [item async for item in client.send_message(request)]
        await client.close()

    assert len(responses) == 1
    task = responses[0].task
    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    payload = json.loads(task.artifacts[0].parts[0].text)
    assert payload["enabled"] is True
    assert {item["protocol"] for item in payload["protocols"]} == {"mcp", "a2a"}
    assert "assess_document" in payload["mcp_tools"]


@pytest.mark.asyncio
async def test_streamable_http_mcp_lists_governed_tools():
    def http_client_factory(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            auth=auth,
            transport=httpx.ASGITransport(
                app=app,
                client=("127.0.0.1", 43124),
            ),
        )

    async with app.router.lifespan_context(app):
        async with streamablehttp_client(
            "http://localhost:8000/mcp/",
            httpx_client_factory=http_client_factory,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=app,
                client=("127.0.0.1", 43125),
            ),
            base_url="http://localhost:8000",
        ) as client:
            untrusted_host = await client.post(
                "/mcp/",
                headers={"Host": "attacker.example"},
                json={},
            )

    names = {tool.name for tool in tools.tools}
    assert "submit_document_assessment" in names
    assert "get_assessment_status" in names
    assert "query_knowledge_base" in names
    assert "review_assessment" not in names
    assert untrusted_host.status_code == 421
