"""Unit tests for the application health check endpoint."""

from fastapi.testclient import TestClient

from src.presentation.api.main import app


def test_healthcheck_endpoint_returns_ok() -> None:
    """
    Verify GET /health returns HTTP 200 OK with status string.

    :returns: None
    """
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == 'OK'
