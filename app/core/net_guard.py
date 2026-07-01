"""Network egress guards for user-configurable upstream URLs."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import settings


def assert_safe_url(url: str | None) -> str:
    """Validate that a URL does not resolve to local or private networks."""
    clean_url = (url or "").strip()
    if not clean_url:
        return ""
    if _is_allowlisted(clean_url):
        return clean_url

    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("LLM base_url must be an absolute HTTP(S) URL.")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or _default_port(parsed.scheme),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError("LLM base_url host could not be resolved.") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if _is_blocked_ip(ip):
            raise ValueError(
                "LLM base_url resolves to a private, loopback, link-local, "
                "or otherwise unsafe address."
            )
    return clean_url


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_unspecified
        or ip.is_multicast
        or ip.is_reserved
    )


def _is_allowlisted(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.hostname:
        return False
    normalized = url.rstrip("/")
    host_port = parsed.hostname
    if parsed.port:
        host_port = f"{parsed.hostname}:{parsed.port}"

    for item in settings.llm_base_url_allowlist:
        allow = item.rstrip("/")
        if "://" in allow:
            if normalized == allow or normalized.startswith(f"{allow}/"):
                return True
            continue
        if allow in {parsed.hostname, host_port}:
            return True
    return False


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80
