"""Google Cloud NLP services — Translation and Natural Language analysis."""

import logging
from typing import Optional

from google.cloud import translate_v2 as translate
from google.cloud import language_v2

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized clients
_translate_client: Optional[translate.Client] = None
_language_client: Optional[language_v2.LanguageServiceAsyncClient] = None


def _get_translate_client() -> translate.Client:
    """Get Cloud Translation client (singleton)."""
    global _translate_client
    if _translate_client is None:
        _translate_client = translate.Client()
        logger.info("Initialized Cloud Translation client")
    return _translate_client


def _get_language_client() -> language_v2.LanguageServiceAsyncClient:
    """Get Cloud Natural Language client (singleton)."""
    global _language_client
    if _language_client is None:
        _language_client = language_v2.LanguageServiceAsyncClient()
        logger.info("Initialized Cloud Natural Language client")
    return _language_client


def translate_text(text: str, target_language: str = "es") -> dict:
    """Translate text using Cloud Translation API.

    Args:
        text: Text to translate.
        target_language: ISO 639-1 language code (e.g., 'es', 'hi', 'fr').

    Returns:
        Dict with translated text and detected source language.
    """
    try:
        client = _get_translate_client()
        result = client.translate(text, target_language=target_language)
        logger.info(f"Translated to {target_language}: {result['detectedSourceLanguage']}")
        return {
            "translated_text": result["translatedText"],
            "source_language": result["detectedSourceLanguage"],
            "target_language": target_language,
        }
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise


async def analyze_entities(text: str) -> list[dict]:
    """Extract entities from text using Cloud Natural Language API.

    Returns list of entities with name, type, and salience score.
    """
    try:
        client = _get_language_client()
        document = language_v2.Document(
            content=text,
            type_=language_v2.Document.Type.PLAIN_TEXT,
        )
        response = await client.analyze_entities(
            request={"document": document}
        )
        entities = [
            {
                "name": entity.name,
                "type": language_v2.Entity.Type(entity.type_).name,
            }
            for entity in response.entities
        ]
        logger.info(f"Extracted {len(entities)} entities via Cloud NLP")
        return entities
    except Exception as e:
        logger.error(f"Entity analysis failed: {e}")
        raise
