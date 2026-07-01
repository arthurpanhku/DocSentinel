from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    success: bool
    output: Any
    citations: list[dict]
    confidence: float
    requires_human_review: bool
    metadata: dict = field(default_factory=dict)
    disclaimer: str | None = None


class BaseAgent(ABC):
    def __init__(self, config: dict) -> None:
        self.config = config
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def process(self, input_data: dict) -> AgentResult:
        """Execute the agent's primary task and return a structured result."""

    async def validate_output(self, result: AgentResult) -> AgentResult:
        return result

    def _make_failure(
        self,
        error: Exception | str,
        *,
        requires_human_review: bool = True,
        metadata: dict | None = None,
    ) -> AgentResult:
        msg = str(error)
        self.log.error("agent_error: %s", msg)
        return AgentResult(
            success=False,
            output=None,
            citations=[],
            confidence=0.0,
            requires_human_review=requires_human_review,
            metadata={"error": msg, **(metadata or {})},
        )
