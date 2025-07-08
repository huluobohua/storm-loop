"""
LRU (Least Recently Used) Cache implementation for the Academic Validation Framework.
"""
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
import time
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU cache implementation with size and time-based eviction.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to store
            ttl_seconds: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[Any, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, timestamp = self._cache[key]
        
        # Check TTL if configured
        if self.ttl_seconds is not None:
            if time.time() - timestamp > self.ttl_seconds:
                # Expired - remove it
                del self._cache[key]
                self._misses += 1
                return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return value
    
    def put(self, key: Any, value: Any) -> None:
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # If key exists, update it and move to end
        if key in self._cache:
            self._cache[key] = (value, time.time())
            self._cache.move_to_end(key)
            return
        
        # If at capacity, remove oldest item
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1
            logger.debug(f"Evicted key from cache: {oldest_key}")
        
        # Add new item
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def evict_expired(self) -> int:
        """
        Manually evict expired items.
        
        Returns:
            Number of items evicted
        """
        if self.ttl_seconds is None:
            return 0
        
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self._cache.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1
        
        if expired_keys:
            logger.debug(f"Evicted {len(expired_keys)} expired items from cache")
        
        return len(expired_keys)


class SizedLRUCache(LRUCache):
    """
    LRU cache with memory size constraints.
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, 
                 ttl_seconds: Optional[int] = None):
        """
        Initialize sized LRU cache.
        
        Args:
            max_size: Maximum number of items
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time-to-live in seconds
        """
        super().__init__(max_size, ttl_seconds)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_size_bytes = 0
        self._item_sizes: Dict[Any, int] = {}
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        # Simple estimation - can be improved with sys.getsizeof
        if isinstance(obj, str):
            return len(obj.encode('utf-8'))
        elif isinstance(obj, (list, tuple)):
            return sum(self._estimate_size(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) 
                      for k, v in obj.items())
        else:
            # Default size for other objects
            return 100
    
    def put(self, key: Any, value: Any) -> None:
        """Put value in cache with size tracking."""
        estimated_size = self._estimate_size(value)
        
        # Check if single item exceeds max memory
        if estimated_size > self.max_memory_bytes:
            logger.warning(f"Item too large for cache: {estimated_size} bytes")
            return
        
        # Evict items until we have space
        while (self._current_size_bytes + estimated_size > self.max_memory_bytes 
               and len(self._cache) > 0):
            oldest_key = next(iter(self._cache))
            self._evict_item(oldest_key)
        
        # Now use parent's put method
        super().put(key, value)
        
        # Track size
        self._item_sizes[key] = estimated_size
        self._current_size_bytes += estimated_size
    
    def _evict_item(self, key: Any) -> None:
        """Evict a specific item and update size tracking."""
        if key in self._cache:
            del self._cache[key]
            if key in self._item_sizes:
                self._current_size_bytes -= self._item_sizes[key]
                del self._item_sizes[key]
            self._evictions += 1
    
    def clear(self) -> None:
        """Clear cache and size tracking."""
        super().clear()
        self._item_sizes.clear()
        self._current_size_bytes = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get extended statistics including memory usage."""
        stats = super().stats()
        stats.update({
            "memory_used_mb": self._current_size_bytes / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "memory_usage_percent": (self._current_size_bytes / self.max_memory_bytes * 100) 
                                  if self.max_memory_bytes > 0 else 0
        })
        return stats