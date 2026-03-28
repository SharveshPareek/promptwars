"""Gemini AI service - handles all 3 pipelines via google-genai SDK."""

import asyncio
import json
import logging
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings
from app.models.intake import IntakeResult
from app.models.actions import ActionPlan, ReasoningResult

logger = logging.getLogger(__name__)

# Initialize Gemini client
# Strictly force Vertex AI mode with explicit aiplatform base URL
# Works around google-genai SDK bug routing to generativelanguage by mistake
client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_location,
    http_options=types.HttpOptions(
        api_version="v1",
        base_url=f"https://{settings.gcp_location}-aiplatform.googleapis.com",
    )
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 6


async def _generate_with_retry(**kwargs):
    """Call Gemini with automatic retry on rate limit (429) errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except ClientError as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SECONDS * (attempt + 1)
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
            else:
                raise


# --- System Prompts ---

INTAKE_SYSTEM_PROMPT = """You are a medical emergency intake analyst. Your job is to parse
ANY input (text descriptions, images of medications/injuries, audio transcriptions) and extract
structured emergency information.

Be thorough: identify all medications visible in photos, all symptoms mentioned, and any
contextual clues about severity. When in doubt, err on the side of higher severity.

Focus on medical emergencies: drug interactions, allergic reactions, cardiac events, injuries,
poisoning, breathing difficulties."""

REASON_AND_VERIFY_PROMPT = """You are an emergency medicine specialist AI. Your job is to analyze the provided emergency situation (text/images/audio) and VERIFY your recommended actions against current medical guidelines using web search.

1. Analyze the situation against established medical protocols (START Triage, ATLS, BLS/ACLS)
2. Identify risk factors and potential complications
3. Recommend specific actions in priority order, verifying each against current medical protocols
4. For each action, assign a confidence score and cite the source/guideline
5. Flag any action that could be harmful (contraindications)

Use Google Search to verify against real medical protocols.
The final output must be a highly detailed medical analysis that will be parsed into an action plan.
CRITICAL: Always err on the side of caution. When uncertain, recommend calling emergency services."""

async def parse_intake(content_parts: list[types.Part]) -> IntakeResult:
    """Pipeline 1a: Parse multimodal input into structured intake data.

    Uses Gemini Flash for speed with structured JSON output.
    """
    logger.info("Pipeline 1a: Starting intake parsing")

    response = await _generate_with_retry(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=INTAKE_SYSTEM_PROMPT)] + content_parts,
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=IntakeResult,
            temperature=0.1,
        ),
    )

    result = IntakeResult.model_validate_json(response.text)
    logger.info(f"Pipeline 1a complete: {result.situation_type} / {result.severity}")
    return result


async def reason_and_verify(content_parts: list[types.Part]) -> str:
    """Pipeline 1b: Deep reasoning AND verification in a single pass.

    Uses Gemini Flash with Google Search Grounding to generate verified analysis text.
    Runs concurrently with Pipeline 1a.
    """
    logger.info("Pipeline 1b: Starting deep reasoning and search verification")

    response = await _generate_with_retry(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=REASON_AND_VERIFY_PROMPT)] + content_parts,
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    logger.info("Pipeline 1b complete")
    return response.text


async def structure_action_plan(
    grounded_text: str,
    intake: IntakeResult,
) -> ActionPlan:
    """Pipeline 2: Structure the grounded analysis into the final ActionPlan JSON.
    """
    logger.info("Pipeline 2: Structuring final action plan")

    structure_prompt = f"""Convert this verified medical analysis into a concise JSON action plan.

## Verified Analysis:
{grounded_text}

## Original Situation Context:
{intake.model_dump_json(indent=2)}

IMPORTANT RULES:
- Output EXACTLY 5 verified_actions (the 5 most critical, in order)
- Each action MUST have a UNIQUE priority number: 1, 2, 3, 4, 5
- Keep each action concise (1-2 sentences max)
- Output 3-4 items in what_not_to_do
- Output 3-5 items in verification_sources

Output JSON with: situation_summary, triage_level (RED/YELLOW/GREEN/BLACK),
verified_actions (list of priority/action/reasoning/confidence/source/do_not),
what_not_to_do (list), call_emergency (bool), emergency_number, verification_sources (list),
confidence_overall (float 0-1)."""

    response = await _generate_with_retry(
        model="gemini-2.5-flash",
        contents=[structure_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActionPlan,
            temperature=0.1,
        ),
    )

    result = ActionPlan.model_validate_json(response.text)
    logger.info(
        f"Pipeline 2 complete: triage={result.triage_level}, "
        f"actions={len(result.verified_actions)}, "
        f"confidence={result.confidence_overall}"
    )
    return result
