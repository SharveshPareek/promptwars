"""Tests for caching logic."""

from app.routers.analyze import _cache_key, _cache_set, _cache, MAX_CACHE_SIZE


class TestCacheKey:
    """Test cache key generation."""

    def test_same_input_same_key(self):
        key1 = _cache_key("headache", [1024])
        key2 = _cache_key("headache", [1024])
        assert key1 == key2

    def test_different_text_different_key(self):
        key1 = _cache_key("headache", [])
        key2 = _cache_key("stomachache", [])
        assert key1 != key2

    def test_different_files_different_key(self):
        key1 = _cache_key("test", [1024])
        key2 = _cache_key("test", [2048])
        assert key1 != key2

    def test_key_is_16_chars(self):
        key = _cache_key("test input", [100, 200])
        assert len(key) == 16


class TestCacheEviction:
    """Test LRU cache eviction."""

    def test_cache_set_and_get(self):
        _cache.clear()
        _cache_set("test_key", {"data": "value"})
        assert "test_key" in _cache
        assert _cache["test_key"]["data"] == "value"

    def test_cache_eviction_at_max_size(self):
        _cache.clear()
        for i in range(MAX_CACHE_SIZE + 10):
            _cache_set(f"key_{i}", {"i": i})
        assert len(_cache) == MAX_CACHE_SIZE
        # Oldest keys should be evicted
        assert "key_0" not in _cache
        # Newest keys should remain
        assert f"key_{MAX_CACHE_SIZE + 9}" in _cache
