"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.assessment_service import assessment_service


@pytest.fixture(autouse=True)
def clear_assessment_tasks():
    assessment_service.clear()
    yield
    assessment_service.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
