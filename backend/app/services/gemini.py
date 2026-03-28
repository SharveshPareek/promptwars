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
# Supports both Vertex AI (GCP auth) and API key modes
if settings.google_api_key:
    client = genai.Client(api_key=settings.google_api_key)
else:
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_location,
    )

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 6


async def _generate_with_retry(**kwargs):
    """Call Gemini with automatic retry on rate limit (429) errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return await _generate_with_retry(**kwargs)
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

REASONING_SYSTEM_PROMPT = """You are an emergency medicine specialist AI. Given structured intake
data about a medical situation, you must:

1. Analyze the situation against established medical protocols (START Triage, ATLS, BLS/ACLS)
2. Identify risk factors and potential complications
3. Recommend specific actions in priority order
4. Flag contraindications (what NOT to do)
5. Reference the specific protocols you are applying

For medication interactions: reference FDA drug interaction databases.
For injuries: reference ATLS (Advanced Trauma Life Support) protocols.
For cardiac events: reference AHA ACLS guidelines.
For poisoning: reference Poison Control protocols.

CRITICAL: Always err on the side of caution. When uncertain, recommend calling emergency services."""

VERIFICATION_PROMPT = """You are a medical verification specialist. Your job is to take a
proposed action plan and VERIFY each action against current medical guidelines using web search.

For each action:
1. Verify it aligns with current medical best practices
2. Assign a confidence score (0.0-1.0)
3. Cite the source/guideline
4. Flag any action that could be harmful

Use Google Search to verify against real medical protocols and guidelines.
The final output must be a verified action plan that a layperson can safely follow."""


async def parse_intake(content_parts: list[types.Part]) -> IntakeResult:
    """Pipeline 1: Parse multimodal input into structured intake data.

    Uses Gemini Flash for speed with structured JSON output.
    """
    logger.info("Pipeline 1: Starting intake parsing")

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
    logger.info(f"Pipeline 1 complete: {result.situation_type} / {result.severity}")
    return result


async def reason(intake: IntakeResult) -> ReasoningResult:
    """Pipeline 2: Deep reasoning against medical protocols.

    Uses Gemini Flash with thinking enabled for thorough analysis.
    Falls back from Pro to Flash due to free-tier quota limits.
    """
    logger.info("Pipeline 2: Starting deep reasoning")

    prompt = f"""{REASONING_SYSTEM_PROMPT}

## Intake Data:
{intake.model_dump_json(indent=2)}

Think step-by-step through established medical protocols and provide your detailed assessment."""

    response = await _generate_with_retry(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReasoningResult,
            temperature=0.2,
        ),
    )

    result = ReasoningResult.model_validate_json(response.text)
    logger.info(f"Pipeline 2 complete: {len(result.recommended_actions)} actions recommended")
    return result


async def verify_actions(
    intake: IntakeResult,
    reasoning: ReasoningResult,
) -> ActionPlan:
    """Pipeline 3: Verify actions with Google Search Grounding.

    Uses Gemini Flash + Google Search for verification.
    """
    logger.info("Pipeline 3: Starting verification with Search Grounding")

    prompt = f"""{VERIFICATION_PROMPT}

## Situation:
{intake.model_dump_json(indent=2)}

## Proposed Actions:
{reasoning.model_dump_json(indent=2)}

Verify each action and produce the final verified action plan."""

    # Step 1: Use Google Search Grounding to verify (no structured output)
    grounded_response = await _generate_with_retry(
        model="gemini-2.5-flash",
        contents=[prompt + "\n\nSearch the web to verify these medical recommendations."],
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    grounded_text = grounded_response.text
    logger.info("Pipeline 3a: Search grounding complete")

    # Step 2: Structure the grounded response into ActionPlan JSON
    structure_prompt = f"""Convert this verified medical analysis into the required JSON format.

## Verified Analysis:
{grounded_text}

## Original Situation:
{intake.model_dump_json(indent=2)}

Output a JSON action plan with: situation_summary, triage_level (RED/YELLOW/GREEN/BLACK),
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
        f"Pipeline 3 complete: triage={result.triage_level}, "
        f"actions={len(result.verified_actions)}, "
        f"confidence={result.confidence_overall}"
    )
    return result
