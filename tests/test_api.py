"""Tests for the health endpoint and API routes."""

from fastapi.testclient import TestClient

# Import the FastAPI app
from app.v1.__main__ import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint returns expected data."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Image Annotator Backend"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """Test the root endpoint returns service info."""
    response = client.get("/v1/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Image Annotator Backend"
    assert data["status"] == "running"
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/v1/health"
    assert data["endpoints"]["translate"] == "/v1/translate/"
    assert data["endpoints"]["annotate"] == "/v1/image/annotate/"


def test_v1_redirect():
    """Test that redirect_slashes=False prevents slash-based redirects."""
    response = client.get("/v1/health/")
    # With redirect_slashes=False, should not redirect
    assert response.status_code != 307


def test_unknown_route_returns_404():
    """Test that unknown routes return 404."""
    response = client.get("/v1/nonexistent")
    assert response.status_code == 404
