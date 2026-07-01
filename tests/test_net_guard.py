import socket

import pytest

from app.core.config import settings
from app.core.net_guard import assert_safe_url


def test_net_guard_rejects_private_address():
    with pytest.raises(ValueError, match="unsafe address"):
        assert_safe_url("http://10.0.0.5:8000/v1")


def test_net_guard_rejects_dns_to_private_address(monkeypatch):
    def fake_getaddrinfo(*args, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("192.168.1.10", 443),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(ValueError, match="unsafe address"):
        assert_safe_url("https://llm.example.com/v1")


def test_net_guard_allowlist_permits_local_llm(monkeypatch):
    monkeypatch.setattr(
        settings,
        "LLM_BASE_URL_ALLOWLIST",
        "http://localhost:11434,http://127.0.0.1:1234/v1",
    )

    assert assert_safe_url("http://localhost:11434") == "http://localhost:11434"
    assert (
        assert_safe_url("http://127.0.0.1:1234/v1")
        == "http://127.0.0.1:1234/v1"
    )
