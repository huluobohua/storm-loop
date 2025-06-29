"""
Tests for cache decorators
"""
import pytest
import asyncio
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from storm_loop.utils.cache_decorators import (
    cached_async, cache_academic_search, cache_paper_details,
    cache_doi_resolution, cache_quality_score, cache_author_search,
    cache_trending_papers, CacheInvalidator, warm_cache_with_popular_searches,
    cache_key_generator
)
from storm_loop.models.academic_models import AcademicPaper, SearchResult, SearchQuery, QualityMetrics


class TestCacheKeyGenerator:
    """Test cache key generation utilities"""
    
    def test_cache_key_generator_basic(self):
        """Test basic cache key generation"""
        key1 = cache_key_generator("arg1", "arg2", kwarg1="value1", kwarg2="value2")
        key2 = cache_key_generator("arg1", "arg2", kwarg1="value1", kwarg2="value2")
        
        # Same arguments should produce same key
        assert key1 == key2
        
        # Different arguments should produce different keys
        key3 = cache_key_generator("arg1", "arg3", kwarg1="value1", kwarg2="value2")
        assert key1 != key3
    
    def test_cache_key_generator_callable_exclusion(self):
        """Test that callable arguments are excluded from key generation"""
        def dummy_func():
            pass
        
        # Should exclude callable arguments
        key = cache_key_generator(dummy_func, "arg2", func_kwarg=dummy_func, kwarg1="value1")
        
        # Key should only contain non-callable arguments
        assert len(key) == 32  # MD5 hash length


class TestCachedAsyncDecorator:
    """Test the core cached_async decorator"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service fixture"""
        service = AsyncMock()
        service.health_check.return_value = True
        service.get.return_value = None
        service.set.return_value = True
        service.delete.return_value = True
        return service
    
    @pytest.mark.asyncio
    async def test_cached_async_basic_functionality(self, mock_cache_service):
        """Test basic caching functionality"""
        call_count = 0
        
        @cached_async(prefix="test", ttl=300)
        async def test_function(arg1, arg2="default"):
            nonlocal call_count
            call_count += 1
            return f"result_{arg1}_{arg2}"
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # First call - cache miss
            result1 = await test_function("value1", arg2="value2")
            assert result1 == "result_value1_value2"
            assert call_count == 1
            
            # Set up cache hit for second call
            mock_cache_service.get.return_value = "cached_result"
            
            # Second call - cache hit
            result2 = await test_function("value1", arg2="value2")
            assert result2 == "cached_result"
            assert call_count == 1  # Function not called again
    
    @pytest.mark.asyncio
    async def test_cached_async_cache_unavailable(self):
        """Test behavior when cache service is unavailable"""
        call_count = 0
        
        @cached_async(prefix="test", ttl=300)
        async def test_function(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', side_effect=Exception("Cache unavailable")):
            # Should still work without caching
            result = await test_function("value")
            assert result == "result_value"
            assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_cached_async_cache_condition(self, mock_cache_service):
        """Test cache condition functionality"""
        call_count = 0
        
        def should_cache(result):
            return "cache_me" in result
        
        @cached_async(prefix="test", ttl=300, cache_condition=should_cache)
        async def test_function(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # Call with result that shouldn't be cached
            result1 = await test_function("no_cache")
            assert result1 == "result_no_cache"
            mock_cache_service.set.assert_not_called()
            
            # Call with result that should be cached
            result2 = await test_function("cache_me")
            assert result2 == "result_cache_me"
            mock_cache_service.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cached_async_custom_key_generator(self, mock_cache_service):
        """Test custom key generator"""
        def custom_key_generator(*args, **kwargs):
            return f"custom_key_{args[1]}"  # Use first argument
        
        @cached_async(prefix="test", key_generator=custom_key_generator)
        async def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            await test_function("value1", "value2")
            
            # Should use custom key
            mock_cache_service.get.assert_called_with("custom_key_value1")
    
    @pytest.mark.asyncio
    async def test_cached_async_error_invalidation(self, mock_cache_service):
        """Test cache invalidation on error"""
        @cached_async(prefix="test", invalidate_on_error=True)
        async def test_function(should_fail):
            if should_fail:
                raise ValueError("Test error")
            return "success"
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # Successful call
            result = await test_function(False)
            assert result == "success"
            
            # Failed call should invalidate cache
            with pytest.raises(ValueError):
                await test_function(True)
            
            mock_cache_service.delete.assert_called_once()


class TestSpecificCacheDecorators:
    """Test specific cache decorators for academic operations"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service fixture"""
        service = AsyncMock()
        service.health_check.return_value = True
        service.get.return_value = None
        service.set.return_value = True
        return service
    
    @pytest.fixture
    def sample_search_result(self):
        """Sample search result for testing"""
        papers = [
            AcademicPaper(id="paper1", title="Test Paper 1"),
            AcademicPaper(id="paper2", title="Test Paper 2")
        ]
        return SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=papers,
            total_count=2,
            source="test"
        )
    
    @pytest.fixture
    def sample_paper(self):
        """Sample paper for testing"""
        return AcademicPaper(
            id="test_paper",
            title="Test Paper",
            doi="10.1000/test"
        )
    
    @pytest.fixture
    def sample_quality_metrics(self):
        """Sample quality metrics for testing"""
        return QualityMetrics(
            citation_score=0.8,
            venue_score=0.9,
            overall_score=0.85
        )
    
    @pytest.mark.asyncio
    async def test_cache_academic_search(self, mock_cache_service, sample_search_result):
        """Test academic search caching decorator"""
        call_count = 0
        
        @cache_academic_search(ttl=3600)
        async def search_papers(self, query, limit=10, sources=None, filters=None):
            nonlocal call_count
            call_count += 1
            return sample_search_result
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # First call
            result1 = await search_papers(None, "machine learning", limit=10, sources=["openalex"])
            assert result1 == sample_search_result
            assert call_count == 1
            
            # Verify cache key generation includes important parameters
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "academic_search:" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_academic_search_condition(self, mock_cache_service):
        """Test academic search cache condition"""
        # Empty result - should not be cached
        empty_result = SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=[],
            total_count=0,
            source="test"
        )
        
        @cache_academic_search(ttl=3600)
        async def search_papers_empty(self, query):
            return empty_result
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            await search_papers_empty(None, "query")
            
            # Should not cache empty results
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_paper_details(self, mock_cache_service, sample_paper):
        """Test paper details caching decorator"""
        @cache_paper_details(ttl=86400)
        async def get_paper_details(self, paper_id):
            return sample_paper
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            result = await get_paper_details(None, "test_paper_id")
            assert result == sample_paper
            
            # Verify cache key uses paper ID
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "paper_details:test_paper_id" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_doi_resolution(self, mock_cache_service, sample_paper):
        """Test DOI resolution caching decorator"""
        @cache_doi_resolution(ttl=604800)
        async def resolve_doi(self, doi):
            return sample_paper
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            result = await resolve_doi(None, "10.1000/test")
            assert result == sample_paper
            
            # Verify cache key uses DOI
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "doi_resolution:10.1000/test" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_quality_score(self, mock_cache_service, sample_quality_metrics, sample_paper):
        """Test quality score caching decorator"""
        @cache_quality_score(ttl=86400)
        async def score_paper(self, paper):
            return sample_quality_metrics
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            result = await score_paper(None, sample_paper)
            assert result == sample_quality_metrics
            
            # Verify cache key uses paper ID
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "quality_score:test_paper" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_author_search(self, mock_cache_service, sample_search_result):
        """Test author search caching decorator"""
        @cache_author_search(ttl=43200)
        async def search_by_author(self, author_name, limit=10):
            return sample_search_result
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            result = await search_by_author(None, "Dr. Smith", limit=20)
            assert result == sample_search_result
            
            # Verify cache key includes author name and limit
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "author_search:Dr. Smith:20" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_trending_papers(self, mock_cache_service, sample_search_result):
        """Test trending papers caching decorator"""
        @cache_trending_papers(ttl=1800)
        async def get_trending_papers(self, days=7, limit=10):
            return sample_search_result
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            result = await get_trending_papers(None, days=14, limit=15)
            assert result == sample_search_result
            
            # Verify cache key includes days and limit
            cache_key = mock_cache_service.set.call_args[0][0]
            assert "trending_papers:14:15" in cache_key


class TestCacheInvalidator:
    """Test cache invalidation utilities"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service fixture"""
        service = AsyncMock()
        service.invalidate_pattern.return_value = 5
        return service
    
    @pytest.mark.asyncio
    async def test_invalidate_paper_cache(self, mock_cache_service):
        """Test paper cache invalidation"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            count = await CacheInvalidator.invalidate_paper_cache("paper_123")
            assert count == 10  # 5 from each pattern
            
            # Should call invalidate_pattern twice
            assert mock_cache_service.invalidate_pattern.call_count == 2
    
    @pytest.mark.asyncio
    async def test_invalidate_search_cache(self, mock_cache_service):
        """Test search cache invalidation"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # Invalidate specific query
            count = await CacheInvalidator.invalidate_search_cache("machine learning")
            assert count == 5
            
            # Invalidate all search cache
            count_all = await CacheInvalidator.invalidate_search_cache()
            assert count_all == 5
    
    @pytest.mark.asyncio
    async def test_invalidate_author_cache(self, mock_cache_service):
        """Test author cache invalidation"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            count = await CacheInvalidator.invalidate_author_cache("Dr. Smith")
            assert count == 5
            
            mock_cache_service.invalidate_pattern.assert_called_with("*author*Dr. Smith*")
    
    @pytest.mark.asyncio
    async def test_invalidate_all(self, mock_cache_service):
        """Test invalidating all cache entries"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            count = await CacheInvalidator.invalidate_all()
            assert count == 5
            
            mock_cache_service.invalidate_pattern.assert_called_with("storm:*")
    
    @pytest.mark.asyncio
    async def test_invalidation_error_handling(self):
        """Test error handling in cache invalidation"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', side_effect=Exception("Cache error")):
            count = await CacheInvalidator.invalidate_paper_cache("paper_123")
            assert count == 0  # Should return 0 on error


class TestCacheWarmUp:
    """Test cache warm-up functionality"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service fixture"""
        service = AsyncMock()
        service.warm_up_cache = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_warm_cache_with_popular_searches(self, mock_cache_service):
        """Test cache warm-up with popular searches"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            await warm_cache_with_popular_searches()
            
            # Should call warm_up_cache
            mock_cache_service.warm_up_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_warm_cache_error_handling(self):
        """Test error handling in cache warm-up"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', side_effect=Exception("Cache error")):
            # Should not raise exception
            await warm_cache_with_popular_searches()


class TestDecoratorIntegration:
    """Test decorator integration scenarios"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service fixture"""
        service = AsyncMock()
        service.health_check.return_value = True
        service.get.return_value = None
        service.set.return_value = True
        return service
    
    @pytest.mark.asyncio
    async def test_multiple_decorators_same_function(self, mock_cache_service):
        """Test multiple cache decorators on same function"""
        call_count = 0
        
        @cache_academic_search(ttl=3600)
        async def complex_search(self, query, **kwargs):
            nonlocal call_count
            call_count += 1
            return SearchResult(
                query=SearchQuery(query=query, limit=10),
                papers=[AcademicPaper(id="test", title="Test")],
                total_count=1,
                source="test"
            )
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # First call
            result1 = await complex_search(None, "query", limit=10, filters={"year": 2023})
            assert call_count == 1
            
            # Second call with same parameters
            mock_cache_service.get.return_value = result1
            result2 = await complex_search(None, "query", limit=10, filters={"year": 2023})
            assert call_count == 1  # Should use cache
    
    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata"""
        @cache_academic_search(ttl=3600)
        async def search_function(query: str) -> SearchResult:
            """Search for academic papers."""
            pass
        
        assert search_function.__name__ == "search_function"
        assert "Search for academic papers" in search_function.__doc__
    
    @pytest.mark.asyncio
    async def test_cache_key_consistency(self, mock_cache_service):
        """Test that cache keys are consistent across calls"""
        @cache_academic_search(ttl=3600)
        async def search_papers(self, query, limit=10, sources=None):
            return SearchResult(
                query=SearchQuery(query=query, limit=limit),
                papers=[],
                total_count=0,
                source="test"
            )
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            # Make multiple calls with same parameters
            await search_papers(None, "query", limit=10, sources=["openalex"])
            key1 = mock_cache_service.get.call_args[0][0]
            
            await search_papers(None, "query", limit=10, sources=["openalex"])
            key2 = mock_cache_service.get.call_args[0][0]
            
            # Keys should be identical
            assert key1 == key2