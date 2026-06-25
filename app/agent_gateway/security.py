"""Access control for remote agent protocol endpoints."""

import hmac
import ipaddress
import json
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import settings

ASGIApp = Callable[
    [dict[str, Any], Callable[[], Awaitable[dict]], Callable[[dict], Awaitable[None]]],
    Awaitable[None],
]


class AgentGatewayAuthMiddleware:
    """Require a bearer token, or confine tokenless development to loopback."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not _is_protected_path(scope.get("path", "")):
            await self.app(scope, receive, send)
            return
        if not settings.AGENT_GATEWAY_ENABLED:
            await _json_response(send, 404, {"detail": "Agent gateway disabled"})
            return
        if settings.AGENT_GATEWAY_TOKEN:
            token = _bearer_token(scope)
            if not token or not hmac.compare_digest(
                token,
                settings.AGENT_GATEWAY_TOKEN,
            ):
                await _json_response(
                    send,
                    401,
                    {"detail": "Invalid agent gateway token"},
                    headers=[(b"www-authenticate", b"Bearer")],
                )
                return
        elif not _is_loopback(scope):
            await _json_response(
                send,
                403,
                {"detail": "Tokenless agent gateway access is loopback-only"},
            )
            return
        await self.app(scope, receive, send)


def _is_protected_path(path: str) -> bool:
    return path == "/a2a" or path.startswith("/mcp")


def _bearer_token(scope: dict[str, Any]) -> str | None:
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    authorization = headers.get(b"authorization", b"").decode("latin-1")
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def _is_loopback(scope: dict[str, Any]) -> bool:
    client = scope.get("client")
    if not client:
        return False
    host = client[0]
    if host in {"localhost", "testclient"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


async def _json_response(
    send,
    status: int,
    payload: dict[str, Any],
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> None:
    body = json.dumps(payload).encode("utf-8")
    response_headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
        *(headers or []),
    ]
    await send(
        {"type": "http.response.start", "status": status, "headers": response_headers}
    )
    await send({"type": "http.response.body", "body": body})
