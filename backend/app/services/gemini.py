"""Gemini AI service — single-call architecture for speed.

Provides two analysis modes:
- analyze(): Single structured output call (~10s)
- analyze_with_grounding(): Google Search verification (~25s)
"""

import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings
from app.models.actions import ActionPlan

logger = logging.getLogger(__name__)

# Vertex AI client with explicit endpoint to bypass SDK routing issues
client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_location,
    http_options=types.HttpOptions(
        api_version="v1",
        base_url=f"https://{settings.gcp_location}-aiplatform.googleapis.com",
    ),
)

MAX_RETRIES: int = 3
RETRY_DELAY_SECONDS: int = 6


async def _call(**kwargs: Any) -> types.GenerateContentResponse:
    """Call Gemini API with automatic retry on rate-limit (429) errors.

    Args:
        **kwargs: Arguments passed to generate_content.

    Returns:
        The Gemini API response.

    Raises:
        ClientError: If the API call fails after all retries.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except ClientError as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SECONDS * (attempt + 1)
                logger.warning(
                    "Rate limited, retry in %ds (attempt %d/%d)",
                    wait, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(wait)
            else:
                raise
    raise ClientError(429, "Max retries exceeded")


SYSTEM_PROMPT: str = """You are CrisisLens, an AI emergency medicine triage system.

Given ANY input (text, images of medications/injuries, audio), you must:

1. ASSESS the situation: identify people, medications, symptoms, severity
2. TRIAGE using START protocol: RED (immediate), YELLOW (delayed), GREEN (minor)
3. Produce EXACTLY 5 prioritized actions a layperson can follow RIGHT NOW
4. Flag what NOT to do (3-4 items)
5. Cite medical sources for each action

Rules:
- Each action gets a unique priority 1-5
- Keep actions concise (1-2 sentences)
- Always err on the side of caution
- If life-threatening → call_emergency = true
- Confidence scores: 0.0 to 1.0"""


async def analyze(content_parts: list[types.Part]) -> ActionPlan:
    """Analyze input with a single Gemini call returning structured JSON.

    This is the primary fast path (~8-12s). Takes multimodal content parts
    (text, images, audio) and returns a complete ActionPlan.

    Args:
        content_parts: List of Gemini content parts (text/image/audio).

    Returns:
        A validated ActionPlan with triage level, actions, and sources.

    Raises:
        ClientError: If the Gemini API call fails.
        ValidationError: If the response doesn't match the ActionPlan schema.
    """
    logger.info("Analyzing with single-shot structured output")

    response = await _call(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=SYSTEM_PROMPT)] + content_parts,
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActionPlan,
            temperature=0.1,
        ),
    )

    result = ActionPlan.model_validate_json(response.text)
    logger.info(
        "Done: triage=%s, actions=%d, confidence=%.2f",
        result.triage_level, len(result.verified_actions), result.confidence_overall,
    )
    return result


async def analyze_with_grounding(content_parts: list[types.Part]) -> ActionPlan:
    """Analyze with Google Search Grounding for verified recommendations.

    Two-call path (~20-25s): first grounds analysis via web search,
    then structures into ActionPlan JSON.

    Args:
        content_parts: List of Gemini content parts (text/image/audio).

    Returns:
        A validated ActionPlan verified against medical guidelines.

    Raises:
        ClientError: If either Gemini API call fails.
        ValidationError: If the response doesn't match the ActionPlan schema.
    """
    logger.info("Analyzing with Google Search Grounding")

    grounded = await _call(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(
                    text="You are an emergency medicine AI. Analyze this situation and "
                         "verify your recommendations against current medical guidelines "
                         "using web search. Be concise."
                )] + content_parts,
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    response = await _call(
        model="gemini-2.5-flash",
        contents=[f"""{SYSTEM_PROMPT}

## Verified Medical Analysis:
{grounded.text}

Convert the above into the structured JSON action plan."""],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActionPlan,
            temperature=0.1,
        ),
    )

    result = ActionPlan.model_validate_json(response.text)
    logger.info(
        "Done (grounded): triage=%s, actions=%d, confidence=%.2f",
        result.triage_level, len(result.verified_actions), result.confidence_overall,
    )
    return result
