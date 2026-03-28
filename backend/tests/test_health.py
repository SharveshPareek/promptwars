"""Tests for health check endpoints (/health/ready and /health/live)."""

import pytest


# ---------------------------------------------------------------------------
# /health/ready
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_ready_returns_200(client):
    """Readiness probe must return HTTP 200."""
    response = await client.get("/health/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_ready_response_format(client):
    """Readiness probe must return JSON with 'status' key equal to 'ready'."""
    response = await client.get("/health/ready")
    body = response.json()
    assert "status" in body
    assert body["status"] == "ready"


@pytest.mark.asyncio
async def test_health_ready_content_type(client):
    """Readiness probe must return application/json content type."""
    response = await client.get("/health/ready")
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_health_ready_no_extra_keys(client):
    """Readiness probe response should only contain the 'status' key."""
    response = await client.get("/health/ready")
    body = response.json()
    assert list(body.keys()) == ["status"]


# ---------------------------------------------------------------------------
# /health/live
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_live_returns_200(client):
    """Liveness probe must return HTTP 200."""
    response = await client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_live_response_format(client):
    """Liveness probe must return JSON with 'status' key equal to 'alive'."""
    response = await client.get("/health/live")
    body = response.json()
    assert "status" in body
    assert body["status"] == "alive"


@pytest.mark.asyncio
async def test_health_live_content_type(client):
    """Liveness probe must return application/json content type."""
    response = await client.get("/health/live")
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_health_live_no_extra_keys(client):
    """Liveness probe response should only contain the 'status' key."""
    response = await client.get("/health/live")
    body = response.json()
    assert list(body.keys()) == ["status"]
