"""
DocSentinel — FastAPI application.
PRD §5; docs/01-architecture-and-tech-stack.md.
"""

import asyncio
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.agent_gateway.a2a import a2a_routes
from app.agent_gateway.security import AgentGatewayAuthMiddleware
from app.api import assessments, governance, health, integrations, kb, skills
from app.core.config import settings
from app.kb.service import get_kb_service
from app.mcp_server import mcp


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = None
    async with AsyncExitStack() as stack:
        from app.core.db import check_migrations_current
        from app.services.llm_config_store import load_and_apply

        load_and_apply()
        check_migrations_current()
        if settings.AGENT_GATEWAY_ENABLED:
            await stack.enter_async_context(mcp.session_manager.run())
        if settings.KB_AUTO_SYNC_INTERVAL_SECONDS > 0:
            sync_task = asyncio.create_task(_kb_auto_sync_loop())
        yield
        if sync_task:
            sync_task.cancel()
            with suppress(asyncio.CancelledError):
                await sync_task


async def _kb_auto_sync_loop():
    while True:
        kb_service = get_kb_service()
        await kb_service.reindex_directory(settings.KB_AUTO_SYNC_DIR)
        await asyncio.sleep(settings.KB_AUTO_SYNC_INTERVAL_SECONDS)


app = FastAPI(
    title="DocSentinel API",
    version="4.2.0",
    description="Automated Security Assessment with LLMs & RAG",
    lifespan=lifespan,
    docs_url="/api-docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

def _configure_optional_infrastructure(application: FastAPI) -> None:
    if settings.REDIS_URL:
        application.state.redis_url = settings.REDIS_URL
    if settings.ENABLE_METRICS:
        with suppress(ImportError):
            from prometheus_fastapi_instrumentator import Instrumentator

            Instrumentator().instrument(application).expose(application)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)
app.add_middleware(AgentGatewayAuthMiddleware)
_configure_optional_infrastructure(app)

app.include_router(health.router)
app.include_router(assessments.router, prefix=settings.API_PREFIX)
app.include_router(kb.router, prefix=settings.API_PREFIX)
app.include_router(integrations.router, prefix=settings.API_PREFIX)
app.include_router(
    skills.router, prefix=f"{settings.API_PREFIX}/skills", tags=["skills"]
)
app.include_router(governance.router, prefix=settings.API_PREFIX)
app.router.routes.extend(a2a_routes)
app.mount("/mcp", mcp.streamable_http_app(), name="mcp")

# Mount docs directory for demo purposes
if Path("docs").exists():
    app.mount("/docs", StaticFiles(directory="docs", html=True), name="docs")

console_dist = Path("frontend/dist")
if console_dist.exists():
    app.mount(
        "/console",
        SPAStaticFiles(directory=str(console_dist), html=True),
        name="console",
    )


@app.get("/")
async def root():
    return {
        "service": "DocSentinel",
        "console": "/console",
        "api_docs": "/api-docs",
        "mcp": "/mcp/",
        "a2a_agent_card": "/.well-known/agent-card.json",
        "demo": "/docs/demo.html",
        "health": "/health",
    }
