"""Gemini AI service — single-call architecture for speed."""

import asyncio
import logging

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings
from app.models.actions import ActionPlan

logger = logging.getLogger(__name__)

# Vertex AI client with explicit endpoint
client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_location,
    http_options=types.HttpOptions(
        api_version="v1",
        base_url=f"https://{settings.gcp_location}-aiplatform.googleapis.com",
    ),
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 6


async def _call(**kwargs):
    """Gemini call with retry on 429."""
    for attempt in range(MAX_RETRIES):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except ClientError as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SECONDS * (attempt + 1)
                logger.warning(f"Rate limited, retry in {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
            else:
                raise


# ── Single-shot prompt ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are CrisisLens, an AI emergency medicine triage system.

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
    """Single Gemini call: input → structured ActionPlan. ~8-12s."""
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
        f"Done: triage={result.triage_level}, "
        f"actions={len(result.verified_actions)}, "
        f"confidence={result.confidence_overall}"
    )
    return result


async def analyze_with_grounding(content_parts: list[types.Part]) -> ActionPlan:
    """Two-call path: Search Grounding → structured output. ~20-25s.

    Used when deeper verification is requested.
    """
    logger.info("Analyzing with Google Search Grounding")

    # Call 1: Grounded analysis (unstructured)
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

    # Call 2: Structure into JSON (fast)
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
        f"Done (grounded): triage={result.triage_level}, "
        f"actions={len(result.verified_actions)}, "
        f"confidence={result.confidence_overall}"
    )
    return result
