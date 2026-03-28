"""Application configuration using Pydantic Settings."""

from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Load configuration from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # GCP
    gcp_project_id: str = "coral-balancer-491605-i0"
    gcp_location: str = "us-central1"
    google_api_key: Optional[str] = None

    # Application
    environment: str = "development"
    port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Cloud Storage
    gcs_bucket_name: str = "crisislens-uploads"

    # Limits
    max_file_size_mb: int = 50
    rate_limit: str = "10/minute"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


settings: Settings = Settings()
