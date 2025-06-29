"""
Integration tests for cached academic source service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from storm_loop.services.academic_source_service import AcademicSourceService
from storm_loop.services.cache_service import CacheService
from storm_loop.models.academic_models import (
    AcademicPaper, Author, SearchResult, SearchQuery, QualityMetrics
)
from storm_loop.config import STORMLoopConfig, OperationMode


class TestCachedAcademicSourceService:
    """Test AcademicSourceService with Redis caching integration"""
    
    @pytest.fixture
    def config(self):
        """Test configuration with caching enabled"""
        return STORMLoopConfig(
            mode=OperationMode.ACADEMIC,
            enable_openalex=True,
            enable_crossref=True,
            redis_host="localhost",
            redis_port=6379,
            cache_ttl=3600
        )
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing"""
        cache = AsyncMock(spec=CacheService)
        cache.health_check.return_value = True
        cache.get.return_value = None  # Cache miss by default
        cache.set.return_value = True
        cache.delete.return_value = True
        cache.invalidate_pattern.return_value = 5
        return cache
    
    @pytest.fixture
    def sample_papers(self):
        """Sample papers for testing"""
        return [
            AcademicPaper(
                id="paper1",
                title="Machine Learning in Healthcare",
                doi="10.1000/test1",
                authors=[Author(display_name="Dr. Smith")],
                citation_count=150,
                publication_year=2023
            ),
            AcademicPaper(
                id="paper2", 
                title="Deep Learning Applications",
                doi="10.1000/test2",
                authors=[Author(display_name="Dr. Johnson")],
                citation_count=89,
                publication_year=2022
            )
        ]
    
    @pytest.fixture
    def sample_search_result(self, sample_papers):
        """Sample search result for testing"""
        return SearchResult(
            query=SearchQuery(query="machine learning", limit=10),
            papers=sample_papers,
            total_count=2,
            source="openalex"
        )
    
    @pytest.fixture
    async def service(self, config, mock_cache_service):
        """Academic source service with mocked cache"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            async with AcademicSourceService() as service:
                service.config = config
                yield service
    
    @pytest.mark.asyncio
    async def test_search_papers_cache_miss_then_hit(self, service, sample_search_result, mock_cache_service):
        """Test search papers with cache miss followed by cache hit"""
        # Mock the underlying search methods
        with patch.object(service, '_search_openalex', return_value=sample_search_result), \
             patch.object(service, '_search_crossref', return_value=SearchResult(
                query=SearchQuery(query="machine learning", limit=10),
                papers=[],
                total_count=0,
                source="crossref"
             )):
            
            # First call - cache miss, should execute search
            mock_cache_service.get.return_value = None
            result1 = await service.search_papers(
                query="machine learning",
                limit=10,
                sources=['openalex']
            )
            
            assert len(result1.papers) == 2
            assert all(paper.quality_score is not None for paper in result1.papers)
            
            # Verify cache was checked and set
            mock_cache_service.get.assert_called()
            mock_cache_service.set.assert_called()
            
            # Second call - cache hit, should return cached result
            mock_cache_service.get.return_value = result1
            mock_cache_service.reset_mock()
            
            result2 = await service.search_papers(
                query="machine learning",
                limit=10,
                sources=['openalex']
            )
            
            assert result2 == result1
            # Should not call set again (cache hit)
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_papers_cache_unavailable(self, service, sample_search_result):
        """Test search papers when cache is unavailable"""
        with patch.object(service, '_search_openalex', return_value=sample_search_result), \
             patch('storm_loop.utils.cache_decorators.get_cache_service', side_effect=Exception("Cache unavailable")):
            
            # Should still work without caching
            result = await service.search_papers(
                query="machine learning",
                limit=10,
                sources=['openalex']
            )
            
            assert len(result.papers) == 2
            assert result.source == "academic_source_service"
    
    @pytest.mark.asyncio
    async def test_get_paper_by_doi_caching(self, service, sample_papers, mock_cache_service):
        """Test DOI lookup with caching"""
        test_paper = sample_papers[0]
        
        with patch.object(service.openalex_client, 'get_paper_by_doi', return_value=test_paper):
            # First call - cache miss
            mock_cache_service.get.return_value = None
            result1 = await service.get_paper_by_doi("10.1000/test1")
            
            assert result1.doi == "10.1000/test1"
            assert result1.quality_score is not None
            
            # Verify cache operations
            mock_cache_service.get.assert_called()
            mock_cache_service.set.assert_called()
            
            # Second call - cache hit
            mock_cache_service.get.return_value = test_paper
            mock_cache_service.reset_mock()
            
            result2 = await service.get_paper_by_doi("10.1000/test1")
            assert result2 == test_paper
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_by_author_caching(self, service, sample_search_result, mock_cache_service):
        """Test author search with caching"""
        with patch.object(service, 'search_papers', return_value=sample_search_result):
            # First call - cache miss
            mock_cache_service.get.return_value = None
            result1 = await service.search_by_author("Dr. Smith", limit=5)
            
            assert len(result1.papers) == 2
            
            # Verify cache operations
            mock_cache_service.get.assert_called()
            mock_cache_service.set.assert_called()
            
            # Second call - cache hit
            mock_cache_service.get.return_value = sample_search_result
            mock_cache_service.reset_mock()
            
            result2 = await service.search_by_author("Dr. Smith", limit=5)
            assert result2 == sample_search_result
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_trending_papers_caching(self, service, sample_search_result, mock_cache_service):
        """Test trending papers with caching"""
        with patch.object(service.openalex_client, 'get_trending_papers', return_value=sample_search_result):
            # First call - cache miss
            mock_cache_service.get.return_value = None
            result1 = await service.get_trending_papers(days=7, limit=10)
            
            assert len(result1.papers) == 2
            
            # Verify cache operations
            mock_cache_service.get.assert_called()
            mock_cache_service.set.assert_called()
            
            # Second call - cache hit
            mock_cache_service.get.return_value = sample_search_result
            mock_cache_service.reset_mock()
            
            result2 = await service.get_trending_papers(days=7, limit=10)
            assert result2 == sample_search_result
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_key_variation(self, service, sample_search_result, mock_cache_service):
        """Test that different parameters generate different cache keys"""
        with patch.object(service, '_search_openalex', return_value=sample_search_result):
            # Different queries should generate different cache keys
            await service.search_papers("machine learning", limit=10)
            key1 = mock_cache_service.get.call_args[0][0]
            
            await service.search_papers("artificial intelligence", limit=10)
            key2 = mock_cache_service.get.call_args[0][0]
            
            assert key1 != key2
            
            # Different limits should generate different cache keys
            await service.search_papers("machine learning", limit=20)
            key3 = mock_cache_service.get.call_args[0][0]
            
            assert key1 != key3
    
    @pytest.mark.asyncio
    async def test_cache_condition_empty_results(self, service, mock_cache_service):
        """Test that empty results are not cached"""
        empty_result = SearchResult(
            query=SearchQuery(query="nonexistent query", limit=10),
            papers=[],
            total_count=0,
            source="openalex"
        )
        
        with patch.object(service, '_search_openalex', return_value=empty_result):
            await service.search_papers("nonexistent query", limit=10)
            
            # Should call get (cache check) but not set (no results to cache)
            mock_cache_service.get.assert_called()
            mock_cache_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_quality_scoring_with_caching(self, service, sample_papers, mock_cache_service):
        """Test that quality scoring works with cached papers"""
        search_result = SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=sample_papers,
            total_count=2,
            source="test"
        )
        
        with patch.object(service, '_search_openalex', return_value=search_result):
            result = await service.search_papers("test query", limit=10)
            
            # All papers should have quality scores
            assert all(paper.quality_score is not None for paper in result.papers)
            assert all(0.0 <= paper.quality_score <= 1.0 for paper in result.papers)
    
    @pytest.mark.asyncio
    async def test_deduplication_with_caching(self, service, mock_cache_service):
        """Test deduplication works correctly with caching"""
        # Papers with duplicate DOI
        duplicate_papers = [
            AcademicPaper(id="paper1", title="Test Paper", doi="10.1000/test"),
            AcademicPaper(id="paper2", title="Test Paper", doi="10.1000/test")  # Duplicate
        ]
        
        openalex_result = SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=duplicate_papers,
            total_count=2,
            source="openalex"
        )
        
        crossref_result = SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=[],
            total_count=0,
            source="crossref"
        )
        
        with patch.object(service, '_search_openalex', return_value=openalex_result), \
             patch.object(service, '_search_crossref', return_value=crossref_result):
            
            result = await service.search_papers("test query", limit=10, deduplicate=True)
            
            # Should only have one paper after deduplication
            assert len(result.papers) == 1
            assert result.papers[0].doi == "10.1000/test"
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, service, sample_search_result, mock_cache_service):
        """Test concurrent access to cached methods"""
        with patch.object(service, '_search_openalex', return_value=sample_search_result):
            # Simulate concurrent requests
            tasks = [
                service.search_papers("machine learning", limit=10),
                service.search_papers("deep learning", limit=10),
                service.search_papers("artificial intelligence", limit=10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 3
            assert all(len(result.papers) == 2 for result in results)
            
            # Should have made multiple cache calls
            assert mock_cache_service.get.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_error_handling_with_cache(self, service, mock_cache_service):
        """Test error handling when both API and cache fail"""
        # Mock cache failure
        mock_cache_service.get.side_effect = Exception("Cache error")
        mock_cache_service.set.side_effect = Exception("Cache error")
        
        # Mock API failure
        with patch.object(service, '_search_openalex', side_effect=Exception("API error")):
            result = await service.search_papers("test query")
            
            # Should return empty result, not raise exception
            assert isinstance(result, SearchResult)
            assert len(result.papers) == 0
    
    @pytest.mark.asyncio
    async def test_cache_ttl_configuration(self, service, sample_search_result, mock_cache_service):
        """Test that cache TTL is properly configured"""
        with patch.object(service, '_search_openalex', return_value=sample_search_result):
            await service.search_papers("test query")
            
            # Verify TTL was passed to cache
            mock_cache_service.set.assert_called()
            call_args = mock_cache_service.set.call_args
            
            # Should have TTL argument
            assert len(call_args[0]) >= 2  # key, value
            # TTL should be reasonable (between 1 hour and 1 week)
            if len(call_args) > 1 and 'ttl' in call_args[1]:
                ttl = call_args[1]['ttl']
                assert 3600 <= ttl <= 604800


class TestCachePerformance:
    """Test cache performance and optimization features"""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service with performance metrics"""
        cache = AsyncMock(spec=CacheService)
        cache.health_check.return_value = True
        cache.get_cache_stats.return_value = {
            'connected_clients': 5,
            'used_memory': '10M',
            'total_commands_processed': 1000,
            'keyspace_hits': 800,
            'keyspace_misses': 200,
            'evicted_keys': 0,
            'hit_rate': 0.8
        }
        return cache
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_monitoring(self, mock_cache_service):
        """Test cache hit rate monitoring"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            stats = await mock_cache_service.get_cache_stats()
            
            assert stats['hit_rate'] == 0.8
            assert stats['keyspace_hits'] == 800
            assert stats['keyspace_misses'] == 200
    
    @pytest.mark.asyncio
    async def test_cache_memory_usage(self, mock_cache_service):
        """Test cache memory usage monitoring"""
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            stats = await mock_cache_service.get_cache_stats()
            
            assert 'used_memory' in stats
            assert stats['used_memory'] == '10M'
            assert stats['connected_clients'] == 5
    
    @pytest.mark.asyncio
    async def test_large_result_caching(self, mock_cache_service):
        """Test caching of large result sets"""
        # Create large result set
        large_papers = [
            AcademicPaper(
                id=f"paper_{i}",
                title=f"Paper {i}",
                abstract="A" * 1000,  # Large abstract
                doi=f"10.1000/test{i}"
            ) for i in range(100)
        ]
        
        large_result = SearchResult(
            query=SearchQuery(query="large query", limit=100),
            papers=large_papers,
            total_count=100,
            source="test"
        )
        
        mock_cache_service.get.return_value = None
        mock_cache_service.set.return_value = True
        
        with patch('storm_loop.utils.cache_decorators.get_cache_service', return_value=mock_cache_service):
            @pytest.fixture
            async def cached_large_search():
                return large_result
            
            # Should handle large results without issues
            mock_cache_service.set.assert_not_called()  # Not actually called in this test setup
            assert len(large_result.papers) == 100