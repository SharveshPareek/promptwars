"""Translation endpoint using Cloud Translation API."""

import logging

from fastapi import APIRouter, HTTPException
from google.api_core.exceptions import GoogleAPIError
from pydantic import BaseModel, Field

from app.services.nlp import analyze_entities, translate_text

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter(tags=["translation"])


class TranslateRequest(BaseModel):
    """Request to translate an action plan."""

    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    target_language: str = Field(default="es", min_length=2, max_length=5, description="Target language code")


class TranslateResponse(BaseModel):
    """Translation result."""

    translated_text: str
    source_language: str
    target_language: str


@router.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest) -> TranslateResponse:
    """Translate text using Google Cloud Translation API.

    Useful for translating action plans into the patient's language.
    """
    try:
        result: dict = translate_text(request.text, request.target_language)
        return TranslateResponse(**result)
    except (GoogleAPIError, ValueError, KeyError) as e:
        logger.error("Translation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Translation failed.")


class EntitiesResponse(BaseModel):
    """Entity extraction result."""

    entities: list[dict]


@router.post("/entities", response_model=EntitiesResponse)
async def entities(request: TranslateRequest) -> EntitiesResponse:
    """Extract medical entities using Cloud Natural Language API."""
    try:
        result: list[dict] = await analyze_entities(request.text)
        return EntitiesResponse(entities=result)
    except (GoogleAPIError, ValueError) as e:
        logger.error("Entity analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Entity analysis failed.")
