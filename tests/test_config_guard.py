import pytest

from app.core.config import Settings


def test_production_rejects_default_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(ENV="production", SECRET_KEY="change-me-in-production")


def test_development_allows_local_defaults():
    settings = Settings(ENV="development")

    assert settings.SECRET_KEY == "change-me-in-production"
    assert settings.AGENT_GATEWAY_ENABLED is True


def test_production_allows_strong_secret_and_gateway_token():
    settings = Settings(
        ENV="prod",
        SECRET_KEY="x" * 32,
        AGENT_GATEWAY_ENABLED=True,
        AGENT_GATEWAY_TOKEN="gateway-token",
    )

    assert settings.ENV == "prod"
    assert settings.SECRET_KEY == "x" * 32
