"""Public models for agent interoperability status."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentProtocolEndpoint(BaseModel):
    protocol: Literal["mcp", "a2a"]
    transport: str
    endpoint: str
    enabled: bool


class AgentIntegrationStatus(BaseModel):
    enabled: bool
    access_mode: Literal["loopback_only", "bearer_token", "disabled"]
    protocols: list[AgentProtocolEndpoint] = Field(default_factory=list)
    mcp_tools: list[str] = Field(default_factory=list)
    a2a_skills: list[str] = Field(default_factory=list)
    document_roots_configured: int = 0
    data_boundary: str = (
        "Agent protocols do not return raw documents. Configured LLM data policy "
        "still applies."
    )
