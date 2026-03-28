"""Analysis endpoint — single Gemini call with SSE and caching."""

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
from app.services.gemini import analyze as gemini_analyze
from app.services.firestore import save_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

# In-memory response cache
_cache: dict[str, dict] = {}

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/webm", "audio/ogg",
    "application/pdf",
}


def _validate_file(file: UploadFile) -> None:
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported.",
        )


def _cache_key(text: str, sizes: list[int]) -> str:
    return hashlib.sha256(f"{text}|{'|'.join(map(str, sizes))}".encode()).hexdigest()[:16]


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _read_parts(
    text: Optional[str], files: Optional[list[UploadFile]]
) -> tuple[list[types.Part], list[int]]:
    """Validate and read all input into Gemini content parts."""
    has_text = text and text.strip()
    has_files = files and len(files) > 0
    if not has_text and not has_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input required.")

    parts: list[types.Part] = []
    sizes: list[int] = []

    if has_text:
        parts.append(types.Part.from_text(text=text.strip()))
    if has_files:
        for f in files:
            _validate_file(f)
            data = await f.read()
            if len(data) > settings.max_file_size_bytes:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                    detail=f"File too large (max {settings.max_file_size_mb}MB).")
            sizes.append(len(data))
            parts.append(types.Part.from_bytes(data=data, mime_type=f.content_type or "application/octet-stream"))

    return parts, sizes


@router.post("/analyze/stream")
async def analyze_stream(
    text: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> StreamingResponse:
    """SSE endpoint — single Gemini call, streamed status updates."""
    parts, sizes = await _read_parts(text, files)
    key = _cache_key(text or "", sizes)

    # Cache hit → instant
    if key in _cache:
        async def cached():
            yield _sse("status", {"stage": "cached", "message": "Loaded from cache"})
            yield _sse("result", _cache[key])
            yield _sse("done", {"session_id": _cache[key]["session_id"]})
        return StreamingResponse(cached(), media_type="text/event-stream")

    async def stream():
        try:
            yield _sse("status", {"stage": "analyzing", "message": "Analyzing with Gemini AI..."})

            # ONE Gemini call → full ActionPlan
            action_plan = await gemini_analyze(parts)

            session_id = str(uuid4())
            result = {
                "session_id": session_id,
                "action_plan": action_plan.model_dump(),
            }

            _cache[key] = result

            # Fire-and-forget Firestore save
            asyncio.create_task(save_session(
                session_id=session_id,
                intake_data={},
                action_plan=action_plan.model_dump(),
            ))

            yield _sse("result", result)
            yield _sse("done", {"session_id": session_id})

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            yield _sse("error", {"message": "Analysis failed. Please try again."})

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/analyze")
async def analyze_sync(
    text: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(None),
) -> dict:
    """Non-streaming fallback."""
    parts, sizes = await _read_parts(text, files)
    key = _cache_key(text or "", sizes)

    if key in _cache:
        return _cache[key]

    try:
        action_plan = await gemini_analyze(parts)
        session_id = str(uuid4())
        result = {"session_id": session_id, "action_plan": action_plan.model_dump()}
        _cache[key] = result
        await save_session(session_id=session_id, intake_data={}, action_plan=action_plan.model_dump())
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")
