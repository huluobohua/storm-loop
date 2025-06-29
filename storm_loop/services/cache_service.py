"""
Redis caching service for STORM-Loop
"""
import asyncio
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List, Callable, ClassVar
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from functools import wraps

from storm_loop.config import get_config
from storm_loop.utils.logging import storm_logger


class CacheService:
    """
    Redis-based caching service with async support
    
    Provides high-performance caching for API responses, search results,
    and other frequently accessed data with TTL support and intelligent
    invalidation strategies.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.config = get_config()
        self._redis_client = redis_client
        self._connection_pool = None
        self._is_connected = False
        
        # Cache key prefixes for different data types
        self.KEY_PREFIXES = {
            'search': 'storm:search:',
            'paper': 'storm:paper:',
            'author': 'storm:author:',
            'doi': 'storm:doi:',
            'quality': 'storm:quality:',
            'trending': 'storm:trending:',
            'session': 'storm:session:'
        }
        
        # Default TTL values (in seconds)
        self.DEFAULT_TTLS = {
            'search': 3600,      # 1 hour for search results
            'paper': 86400,      # 24 hours for paper details
            'author': 43200,     # 12 hours for author info
            'doi': 172800,       # 48 hours for DOI resolution
            'quality': 86400,    # 24 hours for quality scores
            'trending': 1800,    # 30 minutes for trending papers
            'session': 7200      # 2 hours for session data
        }
    
    async def connect(self) -> None:
        """Initialize Redis connection with connection pooling"""
        if self._is_connected:
            return
        
        try:
            if not self._redis_client:
                # Create connection pool for better performance
                self._connection_pool = ConnectionPool(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    password=self.config.redis_password,
                    max_connections=self.config.redis_max_connections,
                    retry_on_timeout=True,
                    health_check_interval=self.config.redis_health_check_interval
                )
                
                self._redis_client = redis.Redis(
                    connection_pool=self._connection_pool,
                    decode_responses=False  # Handle binary data
                )
            
            # Test connection
            await self._redis_client.ping()
            self._is_connected = True
            storm_logger.info(f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}")
            
        except Exception as e:
            storm_logger.error(f"Failed to connect to Redis: {str(e)}")
            self._is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        self._is_connected = False
        storm_logger.info("Disconnected from Redis")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    def _generate_cache_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate standardized cache key with optional parameters and size limits"""
        # Sanitize identifier to remove dangerous characters
        safe_identifier = self._sanitize_cache_key_component(identifier)
        base_key = f"{self.KEY_PREFIXES.get(prefix, prefix)}{safe_identifier}"
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_params = sorted(kwargs.items())
            params_str = json.dumps(sorted_params, sort_keys=True, default=str)
            param_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            base_key += f":{param_hash}"
        
        # Enforce key size limit
        if len(base_key.encode('utf-8')) > self.config.cache_max_key_size:
            # Use hash for very long keys
            key_hash = hashlib.sha256(base_key.encode('utf-8')).hexdigest()
            base_key = f"{self.KEY_PREFIXES.get(prefix, prefix)}hash:{key_hash[:32]}"
        
        return base_key
    
    def _sanitize_cache_key_component(self, component: str) -> str:
        """Sanitize cache key component to remove dangerous characters"""
        if not component:
            return "empty"
        
        # Remove or replace dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:"
        sanitized = ''.join(c if c in safe_chars else '_' for c in component)
        
        # Ensure key component isn't empty after sanitization
        return sanitized if sanitized else "sanitized"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            # Try JSON first for better readability and debugging
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, default=str).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(data)
        except Exception as e:
            storm_logger.warning(f"Serialization fallback to pickle: {str(e)}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to pickle
            try:
                return pickle.loads(data)
            except Exception as e:
                storm_logger.error(f"Failed to deserialize data: {str(e)}")
                return None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_connected:
            return None
        
        try:
            data = await self._redis_client.get(key)
            if data is None:
                return None
            
            result = self._deserialize_data(data)
            storm_logger.debug(f"Cache hit: {key}")
            return result
            
        except Exception as e:
            storm_logger.error(f"Cache get failed for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL and size limits"""
        if not self._is_connected:
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            
            # Check value size limit
            if len(serialized_data) > self.config.cache_max_value_size:
                storm_logger.warning(
                    f"Cache value too large for key {key}: {len(serialized_data)} bytes "
                    f"(max: {self.config.cache_max_value_size})"
                )
                return False
            
            if ttl is not None:
                result = await self._redis_client.setex(key, ttl, serialized_data)
            else:
                result = await self._redis_client.set(key, serialized_data)
            
            storm_logger.debug(f"Cache set: {key} (TTL: {ttl}, Size: {len(serialized_data)} bytes)")
            return bool(result)
            
        except Exception as e:
            storm_logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_connected:
            return False
        
        try:
            result = await self._redis_client.delete(key)
            storm_logger.debug(f"Cache delete: {key}")
            return bool(result)
            
        except Exception as e:
            storm_logger.warning(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._is_connected:
            return False
        
        try:
            result = await self._redis_client.exists(key)
            return bool(result)
        except Exception as e:
            storm_logger.warning(f"Cache exists check failed for key {key}: {str(e)}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key"""
        if not self._is_connected:
            return None
        
        try:
            ttl = await self._redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            storm_logger.warning(f"Cache TTL check failed for key {key}: {str(e)}")
            return None
    
    async def cache_search_results(
        self, 
        query: str, 
        results: Any, 
        source: str = "combined",
        filters: Optional[Dict] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search results with structured key"""
        cache_key = self._generate_cache_key(
            'search', 
            f"{source}:{query}",
            filters=filters
        )
        ttl = ttl or self.DEFAULT_TTLS['search']
        return await self.set(cache_key, results, ttl)
    
    async def get_cached_search_results(
        self, 
        query: str, 
        source: str = "combined",
        filters: Optional[Dict] = None
    ) -> Optional[Any]:
        """Get cached search results"""
        cache_key = self._generate_cache_key(
            'search', 
            f"{source}:{query}",
            filters=filters
        )
        return await self.get(cache_key)
    
    async def cache_paper_details(self, paper_id: str, paper_data: Any, ttl: Optional[int] = None) -> bool:
        """Cache paper details"""
        cache_key = self._generate_cache_key('paper', paper_id)
        ttl = ttl or self.DEFAULT_TTLS['paper']
        return await self.set(cache_key, paper_data, ttl)
    
    async def get_cached_paper_details(self, paper_id: str) -> Optional[Any]:
        """Get cached paper details"""
        cache_key = self._generate_cache_key('paper', paper_id)
        return await self.get(cache_key)
    
    async def cache_doi_resolution(self, doi: str, paper_data: Any, ttl: Optional[int] = None) -> bool:
        """Cache DOI resolution results"""
        cache_key = self._generate_cache_key('doi', doi)
        ttl = ttl or self.DEFAULT_TTLS['doi']
        return await self.set(cache_key, paper_data, ttl)
    
    async def get_cached_doi_resolution(self, doi: str) -> Optional[Any]:
        """Get cached DOI resolution"""
        cache_key = self._generate_cache_key('doi', doi)
        return await self.get(cache_key)
    
    async def cache_quality_score(self, paper_id: str, quality_metrics: Any, ttl: Optional[int] = None) -> bool:
        """Cache quality score for a paper"""
        cache_key = self._generate_cache_key('quality', paper_id)
        ttl = ttl or self.DEFAULT_TTLS['quality']
        return await self.set(cache_key, quality_metrics, ttl)
    
    async def get_cached_quality_score(self, paper_id: str) -> Optional[Any]:
        """Get cached quality score"""
        cache_key = self._generate_cache_key('quality', paper_id)
        return await self.get(cache_key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern using SCAN for production safety"""
        if not self._is_connected:
            return 0
        
        try:
            count = 0
            batch_size = self.config.cache_scan_batch_size
            keys_to_delete = []
            
            # Use SCAN instead of KEYS for production safety
            async for key in self._redis_client.scan_iter(match=pattern, count=batch_size):
                keys_to_delete.append(key)
                
                # Delete in batches to avoid memory issues
                if len(keys_to_delete) >= batch_size:
                    deleted = await self._redis_client.delete(*keys_to_delete)
                    count += deleted
                    keys_to_delete.clear()
            
            # Delete remaining keys
            if keys_to_delete:
                deleted = await self._redis_client.delete(*keys_to_delete)
                count += deleted
            
            storm_logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
            return count
            
        except Exception as e:
            storm_logger.warning(f"Cache pattern invalidation failed for pattern {pattern}: {str(e)}")
            return 0
    
    async def invalidate_search_cache(self, query: Optional[str] = None) -> int:
        """Invalidate search results cache"""
        if query:
            pattern = f"{self.KEY_PREFIXES['search']}*{query}*"
        else:
            pattern = f"{self.KEY_PREFIXES['search']}*"
        return await self.invalidate_pattern(pattern)
    
    async def warm_up_cache(self, data_provider: Callable) -> None:
        """Warm up cache with frequently accessed data"""
        try:
            storm_logger.info("Starting cache warm-up")
            
            # This would be called with a function that provides popular data
            popular_data = await data_provider()
            
            for item in popular_data:
                if 'type' in item and 'key' in item and 'data' in item:
                    await self.set(
                        item['key'], 
                        item['data'], 
                        item.get('ttl', self.DEFAULT_TTLS.get(item['type'], 3600))
                    )
            
            storm_logger.info(f"Cache warm-up completed: {len(popular_data)} items")
            
        except Exception as e:
            storm_logger.warning(f"Cache warm-up failed: {str(e)}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._is_connected:
            return {}
        
        try:
            info = await self._redis_client.info()
            
            stats = {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'evicted_keys': info.get('evicted_keys', 0)
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            if hits + misses > 0:
                stats['hit_rate'] = hits / (hits + misses)
            else:
                stats['hit_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            storm_logger.warning(f"Failed to get cache stats: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if not self._is_connected:
                return False
            
            await self._redis_client.ping()
            return True
            
        except Exception as e:
            storm_logger.warning(f"Redis health check failed: {str(e)}")
            return False


class CacheServiceManager:
    """Thread-safe singleton manager for cache service"""
    
    _instance: ClassVar[Optional[CacheService]] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _initialized: ClassVar[bool] = False
    
    @classmethod
    async def get_instance(cls) -> CacheService:
        """Get cache service instance with thread-safe initialization"""
        if cls._instance is None or not cls._initialized:
            async with cls._lock:
                if cls._instance is None or not cls._initialized:
                    cls._instance = CacheService()
                    await cls._instance.connect()
                    cls._initialized = True
        
        return cls._instance
    
    @classmethod
    async def close_instance(cls) -> None:
        """Close cache service instance"""
        async with cls._lock:
            if cls._instance and cls._initialized:
                await cls._instance.disconnect()
                cls._instance = None
                cls._initialized = False
    
    @classmethod
    async def reset_for_testing(cls) -> None:
        """Reset instance for testing purposes"""
        await cls.close_instance()


async def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    return await CacheServiceManager.get_instance()


async def close_cache_service() -> None:
    """Close global cache service"""
    await CacheServiceManager.close_instance()