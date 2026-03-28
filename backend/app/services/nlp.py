"""Google Cloud NLP services -- Translation and Natural Language analysis."""

import logging
from typing import Optional

from google.api_core.exceptions import GoogleAPIError
from google.cloud import language_v2
from google.cloud import translate_v2 as translate

logger: logging.Logger = logging.getLogger(__name__)

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


def translate_text(text: str, target_language: str = "es") -> dict[str, str]:
    """Translate text using Cloud Translation API.

    Args:
        text: Text to translate.
        target_language: ISO 639-1 language code (e.g., 'es', 'hi', 'fr').

    Returns:
        Dict with translated text and detected source language.

    Raises:
        GoogleAPIError: If the Cloud Translation API call fails.
    """
    try:
        client: translate.Client = _get_translate_client()
        result: dict = client.translate(text, target_language=target_language)
        logger.info(
            "Translated to %s: %s", target_language, result["detectedSourceLanguage"]
        )
        return {
            "translated_text": result["translatedText"],
            "source_language": result["detectedSourceLanguage"],
            "target_language": target_language,
        }
    except (GoogleAPIError, KeyError, ValueError) as e:
        logger.error("Translation failed: %s", e)
        raise


async def analyze_entities(text: str) -> list[dict[str, str]]:
    """Extract entities from text using Cloud Natural Language API.

    Returns:
        List of entities with name and type fields.

    Raises:
        GoogleAPIError: If the Cloud Natural Language API call fails.
    """
    try:
        client: language_v2.LanguageServiceAsyncClient = _get_language_client()
        document: language_v2.Document = language_v2.Document(
            content=text,
            type_=language_v2.Document.Type.PLAIN_TEXT,
        )
        response = await client.analyze_entities(
            request={"document": document}
        )
        entities: list[dict[str, str]] = [
            {
                "name": entity.name,
                "type": language_v2.Entity.Type(entity.type_).name,
            }
            for entity in response.entities
        ]
        logger.info("Extracted %d entities via Cloud NLP", len(entities))
        return entities
    except (GoogleAPIError, ValueError) as e:
        logger.error("Entity analysis failed: %s", e)
        raise
