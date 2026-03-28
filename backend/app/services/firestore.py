"""Firestore service for persisting analysis sessions."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from google.api_core.exceptions import GoogleAPIError
from google.cloud import firestore

from app.config import settings

logger: logging.Logger = logging.getLogger(__name__)

COLLECTION_NAME: str = "analysis_sessions"


def _get_client() -> firestore.AsyncClient:
    """Get Firestore async client (singleton)."""
    if not hasattr(_get_client, "_instance"):
        _get_client._instance = firestore.AsyncClient(
            project=settings.gcp_project_id
        )
        logger.info("Initialized Firestore async client")
    return _get_client._instance


async def save_session(
    session_id: str,
    intake_data: dict[str, Any],
    action_plan: dict[str, Any],
) -> None:
    """Save an analysis session to Firestore.

    Args:
        session_id: Unique session identifier.
        intake_data: Raw intake data from the request.
        action_plan: Generated action plan from Gemini analysis.
    """
    try:
        db: firestore.AsyncClient = _get_client()
        doc_ref = db.collection(COLLECTION_NAME).document(session_id)
        await doc_ref.set({
            "session_id": session_id,
            "intake": intake_data,
            "action_plan": action_plan,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Saved session %s to Firestore", session_id)
    except (GoogleAPIError, OSError) as e:
        logger.error("Failed to save session to Firestore: %s", e)
        # Don't fail the request if Firestore is down


async def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a session from Firestore.

    Args:
        session_id: Unique session identifier to look up.

    Returns:
        Session data dictionary if found, None otherwise.
    """
    try:
        db: firestore.AsyncClient = _get_client()
        doc = await db.collection(COLLECTION_NAME).document(session_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except (GoogleAPIError, OSError) as e:
        logger.error("Failed to get session from Firestore: %s", e)
        return None
