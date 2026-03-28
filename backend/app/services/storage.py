"""Google Cloud Storage service for file uploads."""

import logging

from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage

from app.config import settings

logger: logging.Logger = logging.getLogger(__name__)


def _get_client() -> storage.Client:
    """Get GCS client (singleton)."""
    if not hasattr(_get_client, "_instance"):
        _get_client._instance = storage.Client(project=settings.gcp_project_id)
        logger.info("Initialized GCS client")
    return _get_client._instance


def upload_file(
    file_content: bytes,
    destination_path: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload a file to GCS and return the GCS URI.

    Args:
        file_content: Raw file bytes.
        destination_path: Path within the bucket.
        content_type: MIME type of the file.

    Returns:
        GCS URI string (gs://bucket/path).

    Raises:
        GoogleAPIError: If the upload to GCS fails.
    """
    try:
        client: storage.Client = _get_client()
        bucket = client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(destination_path)
        blob.upload_from_string(file_content, content_type=content_type)

        gcs_uri: str = f"gs://{settings.gcs_bucket_name}/{destination_path}"
        logger.info("Uploaded file to %s", gcs_uri)
        return gcs_uri
    except (GoogleAPIError, OSError) as e:
        logger.error("Failed to upload to GCS: %s", e)
        raise
