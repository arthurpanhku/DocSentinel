"""Agent interoperability status endpoints."""

from fastapi import APIRouter

from app.agent_gateway.service import agent_gateway
from app.models.integration import AgentIntegrationStatus

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/agents/status", response_model=AgentIntegrationStatus)
async def get_agent_integration_status():
    return agent_gateway.status()
