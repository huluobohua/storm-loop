"""
Tests for Redis cache service
"""
import pytest
import asyncio
import json
import pickle
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis
from datetime import datetime, timedelta

from storm_loop.config import STORMLoopConfig, OperationMode
from storm_loop.services.cache_service import CacheService, get_cache_service, close_cache_service


class TestCacheService:
    """Test CacheService functionality"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Fixture for mock Redis client"""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = True
        mock_client.ttl.return_value = 300
        mock_client.keys.return_value = ['test:key1', 'test:key2']
        mock_client.info.return_value = {
            'connected_clients': 1,
            'used_memory_human': '1M',
            'total_commands_processed': 100,
            'keyspace_hits': 80,
            'keyspace_misses': 20,
            'evicted_keys': 0
        }
        return mock_client
    
    @pytest.fixture
    def config(self):
        """Fixture for test configuration"""
        return STORMLoopConfig(
            mode=OperationMode.ACADEMIC,
            redis_host="localhost",
            redis_port=6379,
            redis_db=0,
            redis_password=None
        )
    
    @pytest.fixture
    async def cache_service(self, mock_redis_client, config):
        """Fixture for CacheService instance with mocked Redis"""
        with patch.object(CacheService, '__init__', lambda self, redis_client=None: None):
            service = CacheService()
            service.config = config
            service._redis_client = mock_redis_client
            service._connection_pool = None
            service._is_connected = True
            
            # Initialize key prefixes and TTLs
            service.KEY_PREFIXES = {
                'search': 'storm:search:',
                'paper': 'storm:paper:',
                'author': 'storm:author:',
                'doi': 'storm:doi:',
                'quality': 'storm:quality:',
                'trending': 'storm:trending:',
                'session': 'storm:session:'
            }
            
            service.DEFAULT_TTLS = {
                'search': 3600,
                'paper': 86400,
                'author': 43200,
                'doi': 604800,
                'quality': 86400,
                'trending': 1800,
                'session': 7200
            }
            
            yield service
    
    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, config):
        """Test cache service initialization"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value.ping = AsyncMock(return_value=True)
            
            service = CacheService()
            await service.connect()
            
            assert service._is_connected is True
    
    @pytest.mark.asyncio
    async def test_connection_failure(self, config):
        """Test handling of connection failures"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value.ping = AsyncMock(side_effect=Exception("Connection failed"))
            
            service = CacheService()
            
            with pytest.raises(Exception):
                await service.connect()
            
            assert service._is_connected is False
    
    @pytest.mark.asyncio
    async def test_set_and_get_operations(self, cache_service):
        """Test basic set and get operations"""
        test_key = "test:key"
        test_value = {"data": "test_value", "number": 42}
        
        # Test set operation
        result = await cache_service.set(test_key, test_value, ttl=300)
        assert result is True
        
        # Mock successful get
        cache_service._redis_client.get.return_value = json.dumps(test_value).encode('utf-8')
        
        # Test get operation
        cached_value = await cache_service.get(test_key)
        assert cached_value == test_value
    
    @pytest.mark.asyncio
    async def test_serialization_deserialization(self, cache_service):
        """Test data serialization and deserialization"""
        # Test JSON serialization
        json_data = {"key": "value", "number": 123}
        serialized = cache_service._serialize_data(json_data)
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized == json_data
        
        # Test pickle fallback for complex objects
        class CustomObject:
            def __init__(self, value):
                self.value = value
            
            def __eq__(self, other):
                return isinstance(other, CustomObject) and self.value == other.value
        
        complex_obj = CustomObject("test")
        serialized = cache_service._serialize_data(complex_obj)
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized == complex_obj
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache_service):
        """Test cache key generation"""
        key = cache_service._generate_cache_key('search', 'machine learning', limit=10, source='openalex')
        assert key.startswith('storm:search:machine learning:')
        assert len(key) > len('storm:search:machine learning:')
        
        # Same parameters should generate same key
        key2 = cache_service._generate_cache_key('search', 'machine learning', limit=10, source='openalex')
        assert key == key2
        
        # Different parameters should generate different keys
        key3 = cache_service._generate_cache_key('search', 'machine learning', limit=20, source='openalex')
        assert key != key3
    
    @pytest.mark.asyncio
    async def test_cache_search_results(self, cache_service):
        """Test caching search results"""
        query = "machine learning"
        results = {"papers": [{"title": "Test Paper"}], "count": 1}
        
        result = await cache_service.cache_search_results(query, results, source="openalex")
        assert result is True
        
        cache_service._redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_search_results(self, cache_service):
        """Test retrieving cached search results"""
        query = "machine learning"
        expected_results = {"papers": [{"title": "Test Paper"}], "count": 1}
        
        # Mock cache hit
        cache_service._redis_client.get.return_value = json.dumps(expected_results).encode('utf-8')
        
        results = await cache_service.get_cached_search_results(query, source="openalex")
        assert results == expected_results
    
    @pytest.mark.asyncio
    async def test_cache_paper_details(self, cache_service):
        """Test caching paper details"""
        paper_id = "paper_123"
        paper_data = {"title": "Test Paper", "authors": ["Dr. Test"]}
        
        result = await cache_service.cache_paper_details(paper_id, paper_data)
        assert result is True
        
        cache_service._redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_doi_resolution(self, cache_service):
        """Test caching DOI resolution"""
        doi = "10.1000/test"
        paper_data = {"title": "Test Paper", "doi": doi}
        
        result = await cache_service.cache_doi_resolution(doi, paper_data)
        assert result is True
        
        cache_service._redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_quality_score(self, cache_service):
        """Test caching quality scores"""
        paper_id = "paper_123"
        quality_metrics = {"overall_score": 0.85, "citation_score": 0.9}
        
        result = await cache_service.cache_quality_score(paper_id, quality_metrics)
        assert result is True
        
        cache_service._redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, cache_service):
        """Test pattern-based cache invalidation"""
        pattern = "storm:search:*"
        
        count = await cache_service.invalidate_pattern(pattern)
        assert count == 2  # Based on mock keys returned
        
        cache_service._redis_client.keys.assert_called_once_with(pattern)
        cache_service._redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_cache_invalidation(self, cache_service):
        """Test search cache invalidation"""
        query = "machine learning"
        
        count = await cache_service.invalidate_search_cache(query)
        assert count == 2
        
        # Test invalidating all search cache
        count_all = await cache_service.invalidate_search_cache()
        assert count_all == 2
    
    @pytest.mark.asyncio
    async def test_cache_warm_up(self, cache_service):
        """Test cache warm-up functionality"""
        async def mock_data_provider():
            return [
                {
                    'type': 'search',
                    'key': 'storm:search:popular_query',
                    'data': {'result': 'popular_data'},
                    'ttl': 3600
                },
                {
                    'type': 'paper',
                    'key': 'storm:paper:popular_paper',
                    'data': {'title': 'Popular Paper'},
                    'ttl': 86400
                }
            ]
        
        await cache_service.warm_up_cache(mock_data_provider)
        
        # Should have called set for each item
        assert cache_service._redis_client.setex.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """Test cache statistics retrieval"""
        stats = await cache_service.get_cache_stats()
        
        assert 'connected_clients' in stats
        assert 'used_memory' in stats
        assert 'hit_rate' in stats
        assert stats['hit_rate'] == 0.8  # 80 hits / 100 total
    
    @pytest.mark.asyncio
    async def test_health_check(self, cache_service):
        """Test Redis health check"""
        # Test healthy connection
        health = await cache_service.health_check()
        assert health is True
        
        # Test unhealthy connection
        cache_service._redis_client.ping.side_effect = Exception("Connection lost")
        health = await cache_service.health_check()
        assert health is False
    
    @pytest.mark.asyncio
    async def test_ttl_operations(self, cache_service):
        """Test TTL-related operations"""
        key = "test:key"
        
        # Test getting TTL
        ttl = await cache_service.get_ttl(key)
        assert ttl == 300
        
        # Test key existence
        exists = await cache_service.exists(key)
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_delete_operation(self, cache_service):
        """Test cache deletion"""
        key = "test:key"
        
        result = await cache_service.delete(key)
        assert result is True
        
        cache_service._redis_client.delete.assert_called_with(key)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cache_service):
        """Test error handling in cache operations"""
        # Test get operation with Redis error
        cache_service._redis_client.get.side_effect = Exception("Redis error")
        result = await cache_service.get("test:key")
        assert result is None
        
        # Test set operation with Redis error
        cache_service._redis_client.setex.side_effect = Exception("Redis error")
        result = await cache_service.set("test:key", "value", 300)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_connection_not_established(self, config):
        """Test operations when connection is not established"""
        service = CacheService()
        service.config = config
        service._is_connected = False
        
        # All operations should return defaults when not connected
        assert await service.get("key") is None
        assert await service.set("key", "value") is False
        assert await service.delete("key") is False
        assert await service.exists("key") is False
        assert await service.get_ttl("key") is None
        assert await service.invalidate_pattern("*") == 0


class TestCacheServiceGlobal:
    """Test global cache service functions"""
    
    @pytest.mark.asyncio
    async def test_get_cache_service_singleton(self):
        """Test global cache service singleton pattern"""
        with patch.object(CacheService, 'connect', new_callable=AsyncMock):
            service1 = await get_cache_service()
            service2 = await get_cache_service()
            
            # Should return same instance
            assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_close_cache_service(self):
        """Test closing global cache service"""
        with patch.object(CacheService, 'connect', new_callable=AsyncMock), \
             patch.object(CacheService, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            
            await get_cache_service()
            await close_cache_service()
            
            mock_disconnect.assert_called_once()


class TestCacheSerializationEdgeCases:
    """Test edge cases in cache serialization"""
    
    @pytest.fixture
    def cache_service(self):
        """Simple cache service for serialization tests"""
        service = CacheService()
        return service
    
    def test_serialization_none_value(self, cache_service):
        """Test serialization of None value"""
        serialized = cache_service._serialize_data(None)
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized is None
    
    def test_serialization_empty_containers(self, cache_service):
        """Test serialization of empty containers"""
        # Empty dict
        serialized = cache_service._serialize_data({})
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized == {}
        
        # Empty list
        serialized = cache_service._serialize_data([])
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized == []
    
    def test_deserialization_invalid_data(self, cache_service):
        """Test deserialization of invalid data"""
        # Invalid JSON and pickle data
        invalid_data = b"invalid_data_that_cannot_be_deserialized"
        
        with patch('pickle.loads', side_effect=Exception("Pickle error")):
            result = cache_service._deserialize_data(invalid_data)
            assert result is None
    
    def test_serialization_complex_nested_data(self, cache_service):
        """Test serialization of complex nested data structures"""
        complex_data = {
            "papers": [
                {
                    "id": "paper_1",
                    "title": "Test Paper",
                    "authors": ["Dr. A", "Dr. B"],
                    "metadata": {
                        "citations": 100,
                        "year": 2023,
                        "keywords": ["AI", "ML", "DL"]
                    }
                }
            ],
            "stats": {
                "total": 1,
                "search_time": 150.5
            }
        }
        
        serialized = cache_service._serialize_data(complex_data)
        deserialized = cache_service._deserialize_data(serialized)
        assert deserialized == complex_data