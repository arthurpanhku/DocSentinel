"""Lightweight token-bucket rate limiting for high-cost LLM entry points."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from threading import Lock
from typing import Any, Protocol

from app.core.config import settings

ASGIApp = Callable[
    [dict[str, Any], Callable[[], Awaitable[dict]], Callable[[dict], Awaitable[None]]],
    Awaitable[None],
]


class RateLimiter(Protocol):
    async def allow(
        self,
        key: str,
        *,
        capacity: int,
        refill_per_second: float,
    ) -> bool: ...

    def reset(self) -> None: ...


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class InMemoryTokenBucketRateLimiter:
    """Token bucket fallback used when Redis is not configured or unavailable."""

    def __init__(self) -> None:
        self._buckets: dict[str, _Bucket] = {}
        self._lock = Lock()

    async def allow(
        self,
        key: str,
        *,
        capacity: int,
        refill_per_second: float,
    ) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _Bucket(tokens=float(capacity), updated_at=now)
            elapsed = max(0.0, now - bucket.updated_at)
            tokens = min(float(capacity), bucket.tokens + elapsed * refill_per_second)
            allowed = tokens >= 1.0
            if allowed:
                tokens -= 1.0
            self._buckets[key] = _Bucket(tokens=tokens, updated_at=now)
            return allowed

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


class RedisTokenBucketRateLimiter:
    """Redis-backed token bucket with memory fallback for local installs."""

    _SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])
local current = redis.call("HMGET", key, "tokens", "updated_at")
local tokens = tonumber(current[1])
local updated_at = tonumber(current[2])
if tokens == nil then
  tokens = capacity
  updated_at = now
end
local elapsed = math.max(0, now - updated_at)
tokens = math.min(capacity, tokens + elapsed * refill)
local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end
redis.call("HMSET", key, "tokens", tokens, "updated_at", now)
redis.call("EXPIRE", key, ttl)
return allowed
"""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client = None
        self._fallback = InMemoryTokenBucketRateLimiter()

    async def allow(
        self,
        key: str,
        *,
        capacity: int,
        refill_per_second: float,
    ) -> bool:
        client = await self._get_client()
        if client is None:
            return await self._fallback.allow(
                key,
                capacity=capacity,
                refill_per_second=refill_per_second,
            )
        ttl = max(60, int((capacity / max(refill_per_second, 0.001)) * 2))
        redis_key = "docsentinel:ratelimit:" + hashlib.sha256(
            key.encode("utf-8")
        ).hexdigest()
        try:
            allowed = await client.eval(
                self._SCRIPT,
                1,
                redis_key,
                str(time.time()),
                str(capacity),
                str(refill_per_second),
                str(ttl),
            )
        except Exception:
            return await self._fallback.allow(
                key,
                capacity=capacity,
                refill_per_second=refill_per_second,
            )
        return bool(allowed)

    async def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import redis.asyncio as redis
        except ImportError:
            return None
        self._client = redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    def reset(self) -> None:
        self._fallback.reset()


def build_rate_limiter() -> RateLimiter:
    if settings.REDIS_URL:
        return RedisTokenBucketRateLimiter(settings.REDIS_URL)
    return InMemoryTokenBucketRateLimiter()


class RateLimitMiddleware:
    """Limit only endpoints that can trigger LLM or agent work."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter) -> None:
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send) -> None:
        if not _should_limit(scope):
            await self.app(scope, receive, send)
            return
        capacity = max(1, int(settings.LLM_RATE_LIMIT_BURST))
        per_minute = max(1, int(settings.LLM_RATE_LIMIT_REQUESTS_PER_MINUTE))
        allowed = await self.limiter.allow(
            _rate_limit_key(scope),
            capacity=capacity,
            refill_per_second=per_minute / 60,
        )
        if not allowed:
            await _json_response(
                send,
                429,
                {"detail": "Rate limit exceeded"},
                headers=[(b"retry-after", b"60")],
            )
            return
        await self.app(scope, receive, send)


def _should_limit(scope: dict[str, Any]) -> bool:
    if not settings.RATE_LIMIT_ENABLED:
        return False
    if scope.get("type") != "http" or scope.get("method") != "POST":
        return False
    path = scope.get("path", "").rstrip("/") or "/"
    return path in {
        f"{settings.API_PREFIX}/assessments",
        f"{settings.API_PREFIX}/kb/query",
        "/a2a",
    } or path.startswith("/mcp")


def _rate_limit_key(scope: dict[str, Any]) -> str:
    token = _bearer_token(scope)
    if token:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"bearer:{digest}"
    client = scope.get("client")
    host = client[0] if client else "unknown"
    return f"ip:{host}"


def _bearer_token(scope: dict[str, Any]) -> str | None:
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    authorization = headers.get(b"authorization", b"").decode("latin-1")
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


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
