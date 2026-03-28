"""Tests for API endpoints."""

import io
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.models.actions import ActionItem, ActionPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_action_plan(**overrides) -> ActionPlan:
    """Build a valid ActionPlan for use in mocks."""
    defaults = dict(
        situation_summary="Patient experiencing drug interaction symptoms",
        triage_level="YELLOW",
        verified_actions=[
            ActionItem(
                priority=1,
                action="Discontinue medications",
                reasoning="Potential interaction between drugs",
                confidence=0.9,
                source="FDA Drug Interactions DB",
                do_not="Do not administer more medication",
            ),
        ],
        what_not_to_do=["Do not give additional medication"],
        call_emergency=False,
        emergency_number="108",
        verification_sources=["FDA", "WebMD"],
        confidence_overall=0.85,
    )
    defaults.update(overrides)
    return ActionPlan(**defaults)


# ---------------------------------------------------------------------------
# Health / basic endpoint tests (kept from original file)
# ---------------------------------------------------------------------------

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
async def test_analyze_invalid_file_type(client):
    """Test analyze endpoint rejects unsupported file types."""
    response = await client.post(
        "/api/analyze",
        files={"files": ("test.exe", b"fake content", "application/x-msdownload")},
    )
    assert response.status_code == 415


# ---------------------------------------------------------------------------
# Mocked Gemini tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_with_mocked_gemini(client):
    """Test /api/analyze returns 200 with a valid ActionPlan when Gemini is mocked."""
    plan = _make_action_plan()

    with patch("app.routers.analyze.gemini_analyze", new_callable=AsyncMock, return_value=plan) as mock_gem, \
         patch("app.routers.analyze.save_session", new_callable=AsyncMock):
        # Clear the analyze module's internal cache so we don't hit stale data
        from app.routers.analyze import _cache
        _cache.clear()

        response = await client.post(
            "/api/analyze",
            data={"text": "Patient reports headache and dizziness"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "action_plan" in body
        assert body["action_plan"]["triage_level"] == "YELLOW"
        assert body["action_plan"]["confidence_overall"] == 0.85
        assert len(body["action_plan"]["verified_actions"]) == 1
        assert "session_id" in body
        mock_gem.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_stream_endpoint(client):
    """Test /api/analyze/stream returns SSE events when Gemini is mocked."""
    plan = _make_action_plan()

    with patch("app.routers.analyze.gemini_analyze", new_callable=AsyncMock, return_value=plan), \
         patch("app.routers.analyze.save_session", new_callable=AsyncMock):
        from app.routers.analyze import _cache
        _cache.clear()

        response = await client.post(
            "/api/analyze/stream",
            data={"text": "Patient fell and hit their head"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        body_text = response.text
        # The SSE stream should contain status, result, and done events
        assert "event: status" in body_text
        assert "event: result" in body_text
        assert "event: done" in body_text
        assert "analyzing" in body_text.lower() or "Analyzing" in body_text


@pytest.mark.asyncio
async def test_analyze_cache_hit(client):
    """Test that a second call with the same input is served from cache."""
    plan = _make_action_plan()

    with patch("app.routers.analyze.gemini_analyze", new_callable=AsyncMock, return_value=plan) as mock_gem, \
         patch("app.routers.analyze.save_session", new_callable=AsyncMock):
        from app.routers.analyze import _cache
        _cache.clear()

        payload = {"text": "Unique cache test input 12345"}

        # First call -- should invoke Gemini
        resp1 = await client.post("/api/analyze", data=payload)
        assert resp1.status_code == 200
        assert mock_gem.await_count == 1

        # Second call -- should hit the cache, Gemini NOT called again
        resp2 = await client.post("/api/analyze", data=payload)
        assert resp2.status_code == 200
        assert mock_gem.await_count == 1  # still 1

        # Both responses must match
        assert resp1.json()["action_plan"] == resp2.json()["action_plan"]


@pytest.mark.asyncio
async def test_analyze_whitespace_only_input(client):
    """Test that whitespace-only text with no files is rejected as 400."""
    response = await client.post(
        "/api/analyze",
        data={"text": "   "},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_file_too_large(client):
    """Test that a file exceeding max_file_size_mb triggers 413."""
    from app.config import settings

    # Create a fake file that is just over the limit
    oversized_data = b"x" * (settings.max_file_size_bytes + 1)

    response = await client.post(
        "/api/analyze",
        files={"files": ("big.pdf", io.BytesIO(oversized_data), "application/pdf")},
    )
    assert response.status_code == 413
