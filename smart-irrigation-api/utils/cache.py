"""Caching utility for improving API performance."""

from datetime import datetime, timedelta
from typing import Optional, Any
from cachetools import TTLCache
from config import settings


class CacheManager:
    """Manager class for in-memory caching with TTL."""
    
    def __init__(self, maxsize: int = 100, ttl: int = None):
        """
        Initialize cache manager.
        
        Args:
            maxsize: Maximum number of items in cache
            ttl: Time-to-live in seconds (default from settings)
        """
        if ttl is None:
            ttl = settings.CACHE_TTL_SECONDS
        
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        try:
            return self.cache.get(key)
        except KeyError:
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
        """
        try:
            del self.cache[key]
        except KeyError:
            pass
    
    def clear(self) -> None:
        """Clear all items from cache."""
        self.cache.clear()
    
    def has(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        return key in self.cache
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats (size, maxsize, ttl)
        """
        return {
            "current_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl_seconds": self.ttl
        }


# Global cache instances
sensors_cache = CacheManager(maxsize=50, ttl=settings.CACHE_TTL_SECONDS)


def get_sensors_cache() -> CacheManager:
    """Get the global sensors cache instance."""
    return sensors_cache
