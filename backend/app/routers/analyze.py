"""Main analysis endpoint - runs all 3 pipelines."""

import logging
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from google.genai import types

from app.config import settings
from app.models.actions import ActionPlan
from app.services.gemini import parse_intake, reason, verify_actions
from app.services.firestore import save_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

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


@router.post("/analyze", response_model=dict)
async def analyze(
    text: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> dict:
    """Analyze multimodal input through the 3-pipeline CrisisLens engine.

    Accepts any combination of:
    - text: Free-form text description
    - files: Images (jpg/png/webp), audio (mp3/wav/webm), or PDFs

    Returns a verified, structured action plan.
    """
    # Validate we have at least some input
    has_text = text and text.strip()
    has_files = files and len(files) > 0
    if not has_text and not has_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one input is required (text or files).",
        )

    # Build multimodal content parts for Gemini
    content_parts: list[types.Part] = []

    if has_text:
        content_parts.append(types.Part.from_text(text=text.strip()))

    if has_files:
        for file in files:
            _validate_file(file)
            file_bytes = await file.read()

            # Validate file size
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
        # Pipeline 1: Intake parsing (Gemini Flash - fast)
        intake_result = await parse_intake(content_parts)

        # Pipeline 2: Deep reasoning (Gemini Pro - thorough)
        reasoning_result = await reason(intake_result)

        # Pipeline 3: Verification (Gemini Flash + Google Search)
        action_plan = await verify_actions(intake_result, reasoning_result)

        # Save to Firestore (non-blocking, don't fail on error)
        session_id = str(uuid4())
        await save_session(
            session_id=session_id,
            intake_data=intake_result.model_dump(),
            action_plan=action_plan.model_dump(),
        )

        return {
            "session_id": session_id,
            "intake": intake_result.model_dump(),
            "action_plan": action_plan.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again.",
        )
