"""Tests for translation and NLP endpoints."""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_translate_endpoint(client):
    """Test translation endpoint with mocked Cloud Translation."""
    mock_result = {
        "translatedText": "Llame al 911 inmediatamente",
        "detectedSourceLanguage": "en",
    }
    with patch("app.services.nlp.translate_text", return_value={
        "translated_text": mock_result["translatedText"],
        "source_language": "en",
        "target_language": "es",
    }):
        response = await client.post(
            "/api/translate",
            json={"text": "Call 911 immediately", "target_language": "es"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_language"] == "es"
        assert "Llame" in data["translated_text"]


@pytest.mark.asyncio
async def test_translate_missing_text(client):
    """Test translation rejects empty text."""
    response = await client.post(
        "/api/translate",
        json={"text": "", "target_language": "es"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_entities_endpoint(client):
    """Test entity extraction with mocked Cloud NLP."""
    mock_entities = [
        {"name": "aspirin", "type": "OTHER"},
        {"name": "ibuprofen", "type": "OTHER"},
    ]
    with patch("app.routers.translate.analyze_entities", new_callable=AsyncMock, return_value=mock_entities):
        response = await client.post(
            "/api/entities",
            json={"text": "Patient took aspirin and ibuprofen"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 2
        assert data["entities"][0]["name"] == "aspirin"
