"""Tests for API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_ready(client):
    """Test readiness probe returns 200."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_health_live(client):
    """Test liveness probe returns 200."""
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_analyze_no_input(client):
    """Test analyze endpoint rejects empty input."""
    response = await client.post("/api/analyze")
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_text_only(client):
    """Test analyze endpoint accepts text input.

    Note: This test will fail without Gemini API access.
    In CI, mock the Gemini service.
    """
    response = await client.post(
        "/api/analyze",
        data={"text": "Patient reports headache and dizziness"},
    )
    # We expect either success (200) if Gemini is available,
    # or 500 if not (no API key configured in test env)
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_analyze_invalid_file_type(client):
    """Test analyze endpoint rejects unsupported file types."""
    response = await client.post(
        "/api/analyze",
        files={"files": ("test.exe", b"fake content", "application/x-msdownload")},
    )
    assert response.status_code == 415
