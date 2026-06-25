"""A2A 1.0 adapter for the DocSentinel assessment agent."""

import json

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    a2a_pb2,
)
from a2a.types.a2a_pb2 import TaskState

from app.agent_gateway.service import agent_gateway
from app.core.config import settings


class DocSentinelAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        if not context.current_task:
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("DocSentinel is validating the request."),
        )
        try:
            text = get_message_text(context.message)
            if not text:
                raise ValueError("A JSON request is required")
            result = await agent_gateway.handle_a2a_request(text)
            await updater.add_artifact(
                parts=[
                    new_text_part(
                        text=json.dumps(result, indent=2),
                        media_type="application/json",
                    )
                ]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_COMPLETED,
                message=new_text_message("DocSentinel request completed."),
            )
        except Exception as exc:
            await updater.add_artifact(
                parts=[
                    new_text_part(
                        text=json.dumps({"error": str(exc)}),
                        media_type="application/json",
                    )
                ]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message("DocSentinel rejected the request."),
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported")


def build_agent_card() -> AgentCard:
    base_url = settings.AGENT_GATEWAY_PUBLIC_URL.rstrip("/")
    card = AgentCard(
        name="DocSentinel Security Assessment Agent",
        description=(
            "Evidence-aware security document assessment with mandatory human review."
        ),
        version="5.0.0-phase1",
        documentation_url=f"{base_url}/docs/06-agent-integration.md",
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=f"{base_url}/a2a",
            )
        ],
        skills=[
            AgentSkill(
                id="assess_security_document",
                name="Assess Security Document",
                description=(
                    "Submit a document inside an approved local root for "
                    "evidence-aware security assessment."
                ),
                tags=["security", "assessment", "iso-27001", "pci-dss", "nist"],
                examples=[
                    json.dumps(
                        {
                            "operation": "assess_document",
                            "file_path": "./examples/design.md",
                            "phase": "design",
                        }
                    )
                ],
                input_modes=["application/json", "text/plain"],
                output_modes=["application/json"],
            ),
            AgentSkill(
                id="get_security_assessment",
                name="Get Security Assessment",
                description=(
                    "Retrieve task status and its evidence-backed draft report."
                ),
                tags=["security", "assessment", "status"],
                examples=[
                    json.dumps(
                        {"operation": "get_assessment", "task_id": "<task-id>"}
                    )
                ],
                input_modes=["application/json", "text/plain"],
                output_modes=["application/json"],
            ),
            AgentSkill(
                id="query_security_knowledge",
                name="Query Security Knowledge",
                description="Query approved security and compliance knowledge chunks.",
                tags=["security", "rag", "compliance"],
                examples=[
                    json.dumps(
                        {
                            "operation": "query_knowledge_base",
                            "query": "privileged access requirements",
                        }
                    )
                ],
                input_modes=["application/json", "text/plain"],
                output_modes=["application/json"],
            ),
        ],
    )
    if settings.AGENT_GATEWAY_TOKEN:
        card.security_schemes["bearer"].CopyFrom(
            a2a_pb2.SecurityScheme(
                http_auth_security_scheme=a2a_pb2.HTTPAuthSecurityScheme(
                    description="DocSentinel agent gateway bearer token",
                    scheme="bearer",
                )
            )
        )
        card.security_requirements.add(schemes={"bearer": a2a_pb2.StringList()})
    return card


agent_card = build_agent_card()
request_handler = DefaultRequestHandler(
    agent_executor=DocSentinelAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)
a2a_routes = [
    *create_agent_card_routes(agent_card),
    *create_jsonrpc_routes(request_handler, "/a2a"),
]
