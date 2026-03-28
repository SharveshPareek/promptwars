"""Main analysis endpoint with SSE streaming and response caching."""

import asyncio
import hashlib
import json
import logging
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from google.genai import types

from app.config import settings
from app.models.actions import ActionPlan
from app.services.gemini import parse_intake, reason_and_verify, structure_action_plan
from app.services.firestore import save_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

# In-memory response cache (keyed by input hash)
_response_cache: dict[str, dict] = {}

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/webm", "audio/ogg",
    "application/pdf",
}


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. "
                   f"Allowed: images, audio, PDF.",
        )


def _compute_cache_key(text: str, file_sizes: list[int]) -> str:
    """Create a hash key from input text and file sizes."""
    raw = f"{text}|{'|'.join(str(s) for s in file_sizes)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/analyze/stream")
async def analyze_stream(
    text: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> StreamingResponse:
    """SSE streaming endpoint — sends progressive results as pipelines complete."""

    has_text = text and text.strip()
    has_files = files and len(files) > 0
    if not has_text and not has_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one input is required (text or files).",
        )

    # Read file bytes upfront
    content_parts: list[types.Part] = []
    file_sizes: list[int] = []

    if has_text:
        content_parts.append(types.Part.from_text(text=text.strip()))

    if has_files:
        for file in files:
            _validate_file(file)
            file_bytes = await file.read()
            if len(file_bytes) > settings.max_file_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File '{file.filename}' exceeds {settings.max_file_size_mb}MB limit.",
                )
            file_sizes.append(len(file_bytes))
            content_parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file.content_type or "application/octet-stream",
                )
            )

    # Check cache
    cache_key = _compute_cache_key(text or "", file_sizes)
    if cache_key in _response_cache:
        logger.info(f"Cache hit for key {cache_key}")
        cached = _response_cache[cache_key]

        async def cached_stream():
            yield _sse_event("status", {"stage": "cached", "message": "Loading cached result..."})
            yield _sse_event("intake", cached["intake"])
            yield _sse_event("result", cached)
            yield _sse_event("done", {"session_id": cached["session_id"]})

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    async def event_stream():
        try:
            # Stage 1: Starting
            yield _sse_event("status", {"stage": "intake", "message": "Parsing your input..."})

            # Run Pipeline 1a + 1b concurrently
            intake_task = parse_intake(content_parts)
            analysis_task = reason_and_verify(content_parts)

            intake_result, grounded_analysis = await asyncio.gather(
                intake_task, analysis_task
            )

            # Send intake result immediately
            yield _sse_event("intake", intake_result.model_dump())
            yield _sse_event("status", {"stage": "structuring", "message": "Building verified action plan..."})

            # Stage 2: Structure
            action_plan = await structure_action_plan(
                grounded_text=grounded_analysis,
                intake=intake_result,
            )

            # Build final response
            session_id = str(uuid4())
            response_data = {
                "session_id": session_id,
                "intake": intake_result.model_dump(),
                "action_plan": action_plan.model_dump(),
            }

            # Cache it
            _response_cache[cache_key] = response_data

            # Save to Firestore (fire and forget)
            asyncio.create_task(save_session(
                session_id=session_id,
                intake_data=intake_result.model_dump(),
                action_plan=action_plan.model_dump(),
            ))

            yield _sse_event("result", response_data)
            yield _sse_event("done", {"session_id": session_id})

        except Exception as e:
            logger.error(f"SSE pipeline failed: {e}", exc_info=True)
            yield _sse_event("error", {"message": "Analysis failed. Please try again."})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/analyze", response_model=dict)
async def analyze(
    text: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> dict:
    """Non-streaming fallback endpoint."""
    has_text = text and text.strip()
    has_files = files and len(files) > 0
    if not has_text and not has_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one input is required (text or files).",
        )

    content_parts: list[types.Part] = []
    if has_text:
        content_parts.append(types.Part.from_text(text=text.strip()))
    if has_files:
        for file in files:
            _validate_file(file)
            file_bytes = await file.read()
            if len(file_bytes) > settings.max_file_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File '{file.filename}' exceeds {settings.max_file_size_mb}MB limit.",
                )
            content_parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file.content_type or "application/octet-stream",
                )
            )

    try:
        intake_task = parse_intake(content_parts)
        analysis_task = reason_and_verify(content_parts)
        intake_result, grounded_analysis = await asyncio.gather(intake_task, analysis_task)
        action_plan = await structure_action_plan(grounded_text=grounded_analysis, intake=intake_result)

        session_id = str(uuid4())
        await save_session(session_id=session_id, intake_data=intake_result.model_dump(), action_plan=action_plan.model_dump())

        return {"session_id": session_id, "intake": intake_result.model_dump(), "action_plan": action_plan.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis failed. Please try again.")
