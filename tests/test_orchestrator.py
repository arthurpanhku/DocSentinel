
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agent.orchestrator import run_assessment
from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.models.skill import Skill


@pytest.mark.asyncio
async def test_orchestrator_uses_skill_prompt():
    """Verify that providing a skill_id injects the skill prompt into LLM calls."""

    # Mock dependencies
    mock_skill = Skill(
        id="test-skill",
        name="Test Skill",
        description="A test skill",
        system_prompt="YOU ARE A TEST SKILL",
        risk_focus=["Testing"],
        compliance_frameworks=["TEST-101"]
    )

    # Mock Skill Service
    with patch("app.agent.orchestrator.get_skill_service") as mock_get_service:
        mock_service_instance = MagicMock()
        mock_service_instance.get_skill.return_value = mock_skill
        mock_get_service.return_value = mock_service_instance

        # Mock LLM
        with patch("app.agent.orchestrator.invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = '{"summary": "Test", "risk_items": []}'

            # Mock KB (to avoid actual DB calls)
            with patch("app.agent.orchestrator.get_kb_service") as mock_get_kb:
                mock_kb = MagicMock()
                mock_kb.query = AsyncMock(return_value=[])
                mock_kb.query_history_responses.return_value = []
                mock_get_kb.return_value = mock_kb

                # Input
                parsed_docs = [
                    ParsedDocument(
                        content="This is a test doc.",
                        metadata=ParsedDocumentMetadata(filename="test.md", type="md")
                    )
                ]

                # Run
                await run_assessment(uuid4(), parsed_docs, skill_id="test-skill")

                # Verify
                # Check that invoke_llm was called with the skill prompt
                calls = mock_invoke.call_args_list

                # We expect calls for Drafter, Reviewer, (maybe Confidence)
                # Let's check if "YOU ARE A TEST SKILL" is in any of the system prompts (first arg)
                found_skill_prompt = False
                for call in calls:
                    system_prompt = call.args[0]
                    if "YOU ARE A TEST SKILL" in system_prompt:
                        found_skill_prompt = True
                        break

                assert found_skill_prompt, "Skill system prompt was not injected into LLM calls"
