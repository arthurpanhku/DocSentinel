"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.assessment_service import assessment_service


@pytest.fixture(autouse=True)
def disable_rest_auth_for_existing_tests(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)


@pytest.fixture(autouse=True)
def clear_assessment_tasks():
    if hasattr(app.state, "rate_limiter"):
        app.state.rate_limiter.reset()
    assessment_service.clear()
    yield
    if hasattr(app.state, "rate_limiter"):
        app.state.rate_limiter.reset()
    assessment_service.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
