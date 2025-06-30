"""
Caching decorators for STORM-Loop
"""
import asyncio
import functools
import hashlib
import json
from typing import Any, Callable, Optional, Dict, Union, Awaitable, TypeVar, ParamSpec
from datetime import datetime

from storm_loop.services.cache_service import get_cache_service
from storm_loop.utils.logging import storm_logger


def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from function arguments with efficient handling"""
    # Create a stable key from arguments, avoiding expensive string conversion
    key_data = {
        'args': [_safe_arg_repr(arg) for arg in args if not callable(arg)],  # Exclude self/cls
        'kwargs': {k: _safe_arg_repr(v) for k, v in kwargs.items() if not callable(v)}
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def _safe_arg_repr(arg: Any) -> str:
    """Safely represent an argument for caching without expensive conversions"""
    # Handle common types efficiently
    if isinstance(arg, (str, int, float, bool)):
        return str(arg)
    elif isinstance(arg, (list, tuple)) and len(arg) < 10:
        return str(arg)
    elif hasattr(arg, 'id'):  # Objects with ID attribute
        return f"{type(arg).__name__}:{arg.id}"
    elif hasattr(arg, '__dict__') and len(arg.__dict__) < 5:
        return f"{type(arg).__name__}:{hash(frozenset(arg.__dict__.items()) if arg.__dict__ else ())}"
    else:
        # For complex objects, use type and id
        return f"{type(arg).__name__}:{id(arg)}"


def _normalize_doi(doi: str) -> str:
    """Normalize DOI format for consistent caching"""
    if not doi or doi == 'unknown':
        return doi
    
    # Remove common prefixes and normalize
    doi = doi.lower().strip()
    if doi.startswith('https://doi.org/'):
        doi = doi[16:]
    elif doi.startswith('http://dx.doi.org/'):
        doi = doi[18:]
    elif doi.startswith('doi:'):
        doi = doi[4:]
    
    return doi


P = ParamSpec('P')
T = TypeVar('T')

def cached_async(
    prefix: str = "default",
    ttl: Optional[int] = None,
    key_generator: Optional[Callable[..., str]] = None,
    cache_condition: Optional[Callable[[Any], bool]] = None,
    invalidate_on_error: bool = False,
    timeout: Optional[float] = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Async caching decorator for functions
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_generator: Custom function to generate cache keys
        cache_condition: Function to determine if result should be cached
        invalidate_on_error: Whether to invalidate cache on function error
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if cache service is not available
            try:
                cache_service = await get_cache_service()
                if not await cache_service.health_check():
                    storm_logger.debug(f"Cache unavailable for {func.__name__}: health check failed")
                    return await func(*args, **kwargs)
            except Exception as e:
                storm_logger.debug(f"Cache unavailable for {func.__name__}: {str(e)}")
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                base_key = cache_key_generator(*args, **kwargs)
                cache_key = f"{prefix}:{func.__name__}:{base_key}"
            
            # Try to get from cache
            try:
                cached_result = await cache_service.get(cache_key)
                if cached_result is not None:
                    storm_logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return cached_result
                else:
                    storm_logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            except Exception as e:
                storm_logger.warning(f"Cache get failed for {func.__name__}: {str(e)}")
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                
                # Check caching condition
                should_cache = True
                if cache_condition:
                    try:
                        should_cache = cache_condition(result)
                    except Exception as e:
                        storm_logger.warning(f"Cache condition check failed for {func.__name__}: {str(e)}")
                        should_cache = False  # Don't cache if condition check fails
                
                # Cache the result
                if should_cache and result is not None:
                    try:
                        await cache_service.set(cache_key, result, ttl)
                        storm_logger.debug(f"Cached result for {func.__name__}: {cache_key}")
                    except Exception as e:
                        storm_logger.warning(f"Cache set failed for {func.__name__}: {str(e)}")
                elif not should_cache:
                    storm_logger.debug(f"Cache skipped for {func.__name__}: condition not met")
                elif result is None:
                    storm_logger.debug(f"Cache skipped for {func.__name__}: result is None")
                
                return result
                
            except Exception as e:
                # Optionally invalidate cache on error
                if invalidate_on_error:
                    try:
                        await cache_service.delete(cache_key)
                    except Exception:
                        pass
                raise
        
        return wrapper
    return decorator


def cache_academic_search(ttl: int = 3600):
    """Decorator for caching academic search results"""
    def cache_condition(result: Any) -> bool:
        # Only cache if we have results and the result is valid
        try:
            return (
                result is not None and 
                hasattr(result, 'papers') and 
                isinstance(result.papers, (list, tuple)) and 
                len(result.papers) > 0
            )
        except (AttributeError, TypeError):
            return False
    
    def key_generator(*args, **kwargs):
        # Extract query and important parameters for key
        query = kwargs.get('query', args[1] if len(args) > 1 else 'unknown')
        limit = kwargs.get('limit', args[2] if len(args) > 2 else 10)
        sources = kwargs.get('sources', ['default'])
        filters = kwargs.get('filters', {})
        
        key_data = {
            'query': query,
            'limit': limit,
            'sources': sorted(sources) if sources else [],
            'filters': sorted(filters.items()) if filters else []
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return f"academic_search:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    return cached_async(
        prefix="search",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


def cache_paper_details(ttl: int = 86400):
    """Decorator for caching paper details"""
    def cache_condition(result: Any) -> bool:
        # Only cache successful paper retrievals with valid data
        try:
            return (
                result is not None and 
                hasattr(result, 'id') and 
                getattr(result, 'id', None) is not None
            )
        except (AttributeError, TypeError):
            return False
    
    def key_generator(*args, **kwargs):
        # Extract paper identifier
        paper_id = kwargs.get('paper_id') or kwargs.get('doi') or args[1] if len(args) > 1 else 'unknown'
        return f"paper_details:{paper_id}"
    
    return cached_async(
        prefix="paper",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


def cache_doi_resolution(ttl: int = 172800):  # 48 hours
    """Decorator for caching DOI resolution with normalized DOI"""
    def cache_condition(result):
        # Cache both successful and failed DOI resolutions
        return True
    
    def key_generator(*args, **kwargs):
        doi = kwargs.get('doi', args[1] if len(args) > 1 else 'unknown')
        # Normalize DOI format
        normalized_doi = _normalize_doi(doi)
        return f"doi_resolution:{normalized_doi}"
    
    return cached_async(
        prefix="doi",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


def cache_quality_score(ttl: int = 86400):
    """Decorator for caching quality scores"""
    def cache_condition(result: Any) -> bool:
        # Only cache if we have a valid quality metrics object
        try:
            return (
                result is not None and 
                hasattr(result, 'overall_score') and 
                isinstance(getattr(result, 'overall_score', None), (int, float))
            )
        except (AttributeError, TypeError):
            return False
    
    def key_generator(*args, **kwargs):
        # Extract paper object or ID
        paper = args[1] if len(args) > 1 else kwargs.get('paper')
        if hasattr(paper, 'id'):
            paper_id = paper.id
        elif hasattr(paper, 'doi'):
            paper_id = f"doi:{paper.doi}"
        else:
            paper_id = str(paper)
        return f"quality_score:{paper_id}"
    
    return cached_async(
        prefix="quality",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


def cache_author_search(ttl: int = 43200):  # 12 hours
    """Decorator for caching author search results"""
    def cache_condition(result: Any) -> bool:
        try:
            return (
                result is not None and 
                hasattr(result, 'papers') and 
                isinstance(result.papers, (list, tuple)) and 
                len(result.papers) > 0
            )
        except (AttributeError, TypeError):
            return False
    
    def key_generator(*args, **kwargs):
        author_name = kwargs.get('author_name', args[1] if len(args) > 1 else 'unknown')
        limit = kwargs.get('limit', 10)
        return f"author_search:{author_name}:{limit}"
    
    return cached_async(
        prefix="author",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


def cache_trending_papers(ttl: int = 1800):  # 30 minutes
    """Decorator for caching trending papers"""
    def cache_condition(result: Any) -> bool:
        try:
            return (
                result is not None and 
                hasattr(result, 'papers') and 
                isinstance(result.papers, (list, tuple)) and 
                len(result.papers) > 0
            )
        except (AttributeError, TypeError):
            return False
    
    def key_generator(*args, **kwargs):
        days = kwargs.get('days', args[1] if len(args) > 1 else 7)
        limit = kwargs.get('limit', args[2] if len(args) > 2 else 10)
        return f"trending_papers:{days}:{limit}"
    
    return cached_async(
        prefix="trending",
        ttl=ttl,
        key_generator=key_generator,
        cache_condition=cache_condition
    )


class CacheInvalidator:
    """Utility class for cache invalidation"""
    
    @staticmethod
    async def invalidate_paper_cache(paper_id: str):
        """Invalidate all cache entries related to a specific paper"""
        try:
            cache_service = await get_cache_service()
            patterns = [
                f"*paper*{paper_id}*",
                f"*quality*{paper_id}*"
            ]
            
            total_invalidated = 0
            for pattern in patterns:
                count = await cache_service.invalidate_pattern(pattern)
                total_invalidated += count
            
            storm_logger.info(f"Invalidated {total_invalidated} cache entries for paper {paper_id}")
            return total_invalidated
            
        except Exception as e:
            storm_logger.warning(f"Cache invalidation failed for paper {paper_id}: {str(e)}")
            return 0
    
    @staticmethod
    async def invalidate_search_cache(query: Optional[str] = None):
        """Invalidate search cache entries"""
        try:
            cache_service = await get_cache_service()
            
            if query:
                pattern = f"*search*{query}*"
            else:
                pattern = "*search*"
            
            count = await cache_service.invalidate_pattern(pattern)
            storm_logger.info(f"Invalidated {count} search cache entries")
            return count
            
        except Exception as e:
            storm_logger.warning(f"Search cache invalidation failed: {str(e)}")
            return 0
    
    @staticmethod
    async def invalidate_author_cache(author_name: str):
        """Invalidate author-related cache entries"""
        try:
            cache_service = await get_cache_service()
            pattern = f"*author*{author_name}*"
            
            count = await cache_service.invalidate_pattern(pattern)
            storm_logger.info(f"Invalidated {count} cache entries for author {author_name}")
            return count
            
        except Exception as e:
            storm_logger.warning(f"Author cache invalidation failed for {author_name}: {str(e)}")
            return 0
    
    @staticmethod
    async def invalidate_all():
        """Invalidate all STORM-Loop cache entries"""
        try:
            cache_service = await get_cache_service()
            pattern = "storm:*"
            
            count = await cache_service.invalidate_pattern(pattern)
            storm_logger.info(f"Invalidated all cache entries: {count} keys")
            return count
            
        except Exception as e:
            storm_logger.warning(f"Full cache invalidation failed: {str(e)}")
            return 0


# Convenience function for cache warming
async def warm_cache_with_popular_searches() -> None:
    """Warm cache with popular/common searches"""
    try:
        cache_service = await get_cache_service()
        
        # Popular search terms that might be frequently accessed
        popular_searches = [
            "machine learning",
            "artificial intelligence", 
            "deep learning",
            "natural language processing",
            "computer vision",
            "climate change",
            "covid-19",
            "quantum computing"
        ]
        
        warm_up_data = []
        for search_term in popular_searches:
            # This would normally be populated by actual search results
            # For now, we'll just create the cache structure
            warm_up_data.append({
                'type': 'search',
                'key': f"storm:search:warm_up:{search_term}",
                'data': {'status': 'warm_up_placeholder'},
                'ttl': 7200  # 2 hours for warm-up data
            })
        
        async def data_provider():
            return warm_up_data
        
        await cache_service.warm_up_cache(data_provider)
        
    except Exception as e:
        storm_logger.warning(f"Cache warm-up failed: {str(e)}")