"""Firestore service for persisting analysis sessions."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from google.cloud import firestore

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "analysis_sessions"


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
    """Save an analysis session to Firestore."""
    try:
        db = _get_client()
        doc_ref = db.collection(COLLECTION_NAME).document(session_id)
        await doc_ref.set({
            "session_id": session_id,
            "intake": intake_data,
            "action_plan": action_plan,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Saved session {session_id} to Firestore")
    except Exception as e:
        logger.error(f"Failed to save session to Firestore: {e}")
        # Don't fail the request if Firestore is down
        pass


async def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Retrieve a session from Firestore."""
    try:
        db = _get_client()
        doc = await db.collection(COLLECTION_NAME).document(session_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Failed to get session from Firestore: {e}")
        return None
