"""
Shared caching utilities for Looking Glass.

Provides TTL-based in-memory caching with statistics tracking.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class TTLCache:
    """Simple TTL-based in-memory cache with stats."""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if not found or expired."""
        if key not in self._cache:
            self.stats.misses += 1
            return None
        
        entry = self._cache[key]
        if time.time() - entry["timestamp"] > self._ttl:
            del self._cache[key]
            self.stats.misses += 1
            return None
        
        self.stats.hits += 1
        return entry["value"]
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp."""
        self._clean()
        self._cache[key] = {"value": value, "timestamp": time.time()}
    
    def _clean(self):
        """Remove expired entries and enforce max size."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["timestamp"] > self._ttl]
        for k in expired:
            del self._cache[k]
            self.stats.evictions += 1
        
        if len(self._cache) > self._max_size:
            oldest = sorted(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            for k in oldest[:len(self._cache) - self._max_size]:
                del self._cache[k]
                self.stats.evictions += 1
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def __len__(self):
        """Return number of cached entries."""
        return len(self._cache)


# Pre-configured caches for the application
image_annotation_cache = TTLCache(ttl_seconds=3600, max_size=1000)
translation_cache = TTLCache(ttl_seconds=3600, max_size=1000)
