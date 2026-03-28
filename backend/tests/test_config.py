"""Tests for application configuration (app.config.Settings)."""

from app.config import Settings


class TestSettingsDefaults:
    """Verify default values produced by Settings when no env vars are set."""

    def test_settings_defaults(self):
        """Core default values should match what the Settings class declares."""
        s = Settings()
        assert s.gcp_project_id == "coral-balancer-491605-i0"
        assert s.gcp_location == "us-central1"
        assert s.environment == "development"
        assert s.port == 8000
        assert s.gcs_bucket_name == "crisislens-uploads"
        assert s.max_file_size_mb == 50
        assert s.rate_limit == "10/minute"
        # google_api_key defaults to None but may be set via .env / environment
        assert s.google_api_key is None or isinstance(s.google_api_key, str)

    def test_default_allowed_origins_string(self):
        """The raw allowed_origins string should contain localhost origins."""
        s = Settings()
        assert "localhost:3000" in s.allowed_origins
        assert "localhost:5173" in s.allowed_origins


class TestAllowedOriginsList:
    """Verify comma-separated origin parsing."""

    def test_allowed_origins_list_default(self):
        """Default origins should parse into a two-element list."""
        s = Settings()
        origins = s.allowed_origins_list
        assert isinstance(origins, list)
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins

    def test_allowed_origins_list_custom(self):
        """Custom comma-separated string should parse correctly."""
        s = Settings(allowed_origins="https://a.com, https://b.com, https://c.com")
        origins = s.allowed_origins_list
        assert len(origins) == 3
        assert "https://a.com" in origins
        assert "https://b.com" in origins
        assert "https://c.com" in origins

    def test_allowed_origins_list_strips_whitespace(self):
        """Extra whitespace around origins should be stripped."""
        s = Settings(allowed_origins="  https://x.com  ,  https://y.com  ")
        origins = s.allowed_origins_list
        assert origins == ["https://x.com", "https://y.com"]

    def test_allowed_origins_single_origin(self):
        """A single origin (no comma) should produce a one-element list."""
        s = Settings(allowed_origins="https://only.com")
        assert s.allowed_origins_list == ["https://only.com"]


class TestMaxFileSizeBytes:
    """Verify MB-to-bytes conversion property."""

    def test_max_file_size_bytes_default(self):
        """Default 50 MB should equal 50 * 1024 * 1024 bytes."""
        s = Settings()
        assert s.max_file_size_bytes == 50 * 1024 * 1024

    def test_max_file_size_bytes_custom(self):
        """Setting a custom MB value should convert correctly."""
        s = Settings(max_file_size_mb=10)
        assert s.max_file_size_bytes == 10 * 1024 * 1024

    def test_max_file_size_bytes_one_mb(self):
        """1 MB edge case."""
        s = Settings(max_file_size_mb=1)
        assert s.max_file_size_bytes == 1_048_576
