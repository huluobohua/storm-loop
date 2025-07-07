"""
Cache decorator for research planning operations.

Provides a clean separation of caching concerns from core business logic
following the Single Responsibility Principle.
"""

import asyncio
import functools
import hashlib
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

# Constants
CACHE_TIMEOUT_SECONDS = 5.0


def cache_with_timeout(
    cache_key_func: Optional[Callable] = None,
    timeout: float = CACHE_TIMEOUT_SECONDS,
    namespace: str = "default"
) -> Callable[[F], F]:
    """
    Decorator for caching async function results with timeout protection.
    
    Provides clean separation of caching logic from business logic,
    following the Single Responsibility Principle.
    
    Args:
        cache_key_func: Optional function to generate cache keys. 
                       If None, uses function name and arguments.
        timeout: Timeout for cache operations in seconds
        namespace: Cache namespace for key collision prevention
        
    Returns:
        Decorated function with caching behavior
        
    Example:
        @cache_with_timeout(namespace="research_plan")
        async def plan_research(self, topic: str) -> Dict:
            # Core business logic only
            return await self._generate_plan_internal(topic)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Skip caching if no cache service available
            if not hasattr(self, 'cache') or self.cache is None:
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            cache_key = _generate_cache_key(
                func, args, kwargs, cache_key_func, namespace
            )
            
            # Try to get cached result
            cached_result = await _try_get_cached(
                self.cache, cache_key, timeout, func.__name__
            )
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}", extra={"cache_key": cache_key})
                return cached_result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            
            # Cache result asynchronously (non-blocking)
            asyncio.create_task(
                _try_cache_result(self.cache, cache_key, result, timeout, func.__name__)
            )
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func: Callable, 
    args: tuple, 
    kwargs: dict, 
    cache_key_func: Optional[Callable],
    namespace: str
) -> str:
    """
    Generate secure, collision-resistant cache key.
    
    Args:
        func: The function being cached
        args: Function positional arguments
        kwargs: Function keyword arguments  
        cache_key_func: Optional custom key generation function
        namespace: Cache namespace
        
    Returns:
        Secure cache key string
    """
    if cache_key_func:
        key_data = cache_key_func(*args, **kwargs)
    else:
        # Default: use function name and arguments
        # Skip 'self' parameter (args[0])
        key_parts = [func.__name__] + [str(arg) for arg in args[1:]]
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_data = ":".join(key_parts)
    
    # Create collision-resistant key with namespace and hash
    full_key = f"{namespace}:v1:{key_data}"
    hash_digest = hashlib.sha256(full_key.encode('utf-8')).hexdigest()
    
    return f"{namespace}:v1:{hash_digest[:16]}"


async def _try_get_cached(
    cache, 
    cache_key: str, 
    timeout: float, 
    func_name: str
) -> Optional[Any]:
    """
    Try to retrieve cached result with timeout protection.
    
    Args:
        cache: Cache service instance
        cache_key: Cache key to retrieve
        timeout: Operation timeout in seconds
        func_name: Function name for logging
        
    Returns:
        Cached result or None if not found/error
    """
    try:
        return await asyncio.wait_for(
            cache.get(cache_key),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(
            f"Cache retrieval timed out for {func_name}",
            extra={"timeout": timeout, "cache_key": cache_key}
        )
        return None
    except Exception as e:
        logger.warning(
            f"Cache retrieval failed for {func_name}",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "cache_key": cache_key
            }
        )
        return None


async def _try_cache_result(
    cache, 
    cache_key: str, 
    result: Any, 
    timeout: float, 
    func_name: str
) -> None:
    """
    Try to cache result with timeout protection.
    
    Args:
        cache: Cache service instance
        cache_key: Cache key to store under
        result: Result to cache
        timeout: Operation timeout in seconds
        func_name: Function name for logging
    """
    try:
        await asyncio.wait_for(
            cache.set(cache_key, result),
            timeout=timeout
        )
        logger.debug(
            f"Cached result for {func_name}",
            extra={"cache_key": cache_key}
        )
    except asyncio.TimeoutError:
        logger.warning(
            f"Cache storage timed out for {func_name}",
            extra={"timeout": timeout, "cache_key": cache_key}
        )
    except Exception as e:
        logger.warning(
            f"Cache storage failed for {func_name}",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "cache_key": cache_key
            }
        )


def research_plan_cache_key(topic: str) -> str:
    """
    Custom cache key generator for research planning.
    
    Args:
        topic: Research topic
        
    Returns:
        Normalized cache key component
    """
    # Import here to avoid circular dependency
    import unicodedata
    
    # Normalize topic for consistent caching
    normalized = unicodedata.normalize('NFKC', topic).strip()
    return f"research_plan:{normalized}"