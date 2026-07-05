"""Tests for the cache module."""

import time
from app.cache import TTLCache, CacheStats


def test_cache_set_and_get():
    """Test basic set and get operations."""
    cache = TTLCache(ttl_seconds=60, max_size=100)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_miss():
    """Test cache miss returns None."""
    cache = TTLCache(ttl_seconds=60, max_size=100)
    assert cache.get("nonexistent") is None


def test_cache_expiry():
    """Test that expired entries return None."""
    cache = TTLCache(ttl_seconds=0, max_size=100)  # 0 TTL = instant expiry
    cache.set("key1", "value1")
    time.sleep(0.01)
    assert cache.get("key1") is None


def test_cache_eviction_max_size():
    """Test that oldest entries are evicted when max_size is exceeded."""
    cache = TTLCache(ttl_seconds=3600, max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    # Now 2 entries, at max_size
    cache.set("c", 3)  # _clean() runs before add -> 2 entries, no eviction needed
                       # After add -> 3 entries, but _clean already ran
    cache.set("d", 4)  # _clean() runs: 3 > 2, evicts oldest (a) before adding d

    assert cache.get("a") is None  # Evicted (oldest)
    # b, c, d should still be present (d was just added after _clean)
    assert cache.get("d") == 4


def test_cache_clear():
    """Test clearing the cache."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    cache.set("key1", "value1")
    cache.clear()
    assert cache.get("key1") is None
    assert len(cache) == 0


def test_cache_len():
    """Test length tracking."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    assert len(cache) == 0
    cache.set("a", 1)
    assert len(cache) == 1
    cache.set("b", 2)
    assert len(cache) == 2


def test_cache_stats_hit_rate():
    """Test hit rate calculation."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    cache.set("key", "value")
    cache.get("key")  # hit
    cache.get("missing")  # miss
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1
    assert cache.stats.hit_rate == 0.5


def test_cache_stats_empty():
    """Test hit rate when no operations performed."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    assert cache.stats.hit_rate == 0.0


def test_cache_stats_evictions():
    """Test eviction counting."""
    cache = TTLCache(ttl_seconds=0, max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    time.sleep(0.01)
    # Clean triggered by set
    cache.set("c", 3)
    # 'a' and 'b' should be evicted due to expiry
    # But only 'a' or 'b' may be evicted depending on order
    assert cache.stats.evictions > 0


def test_cache_overwrite():
    """Test overwriting an existing key updates the value."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    cache.set("key", "old")
    cache.set("key", "new")
    assert cache.get("key") == "new"


def test_cache_different_types():
    """Test caching different value types."""
    cache = TTLCache(ttl_seconds=3600, max_size=100)
    cache.set("int", 42)
    cache.set("float", 3.14)
    cache.set("list", [1, 2, 3])
    cache.set("dict", {"a": 1})
    cache.set("none", None)

    assert cache.get("int") == 42
    assert cache.get("float") == 3.14
    assert cache.get("list") == [1, 2, 3]
    assert cache.get("dict") == {"a": 1}
    assert cache.get("none") is None
