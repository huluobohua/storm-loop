"""
Comprehensive tests for warm_cache performance optimization.
Addresses Issue #65: Performance Optimization and Scalability for Academic Research Loads.
"""

import asyncio
import pytest
import time
import unittest.mock
from unittest.mock import AsyncMock, patch, Mock
from typing import List, Dict, Any

from knowledge_storm.services.academic_source_service import AcademicSourceService


class TestWarmCachePerformance:
    """Test suite for warm_cache performance and concurrency."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock AcademicSourceService for testing."""
        with patch.multiple(
            'knowledge_storm.services.academic_source_service',
            CacheService=Mock(),
            CircuitBreaker=Mock(),
            CacheKeyBuilder=Mock()
        ):
            service = AcademicSourceService()
            service.search_combined = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_warm_cache_concurrency_limit(self, mock_service):
        """Test that warm_cache respects the parallel concurrency limit."""
        # Track concurrent calls
        concurrent_calls = 0
        max_concurrent = 0
        
        async def mock_search_combined(query: str, limit: int = 10):
            nonlocal concurrent_calls, max_concurrent
            concurrent_calls += 1
            max_concurrent = max(max_concurrent, concurrent_calls)
            
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            concurrent_calls -= 1
            return []

        mock_service.search_combined = mock_search_combined
        
        queries = [f"test query {i}" for i in range(20)]
        parallel_limit = 5
        
        await mock_service.warm_cache(queries, parallel=parallel_limit)
        
        # Verify concurrency was limited
        assert max_concurrent <= parallel_limit, f"Concurrency limit violated: {max_concurrent} > {parallel_limit}"

    @pytest.mark.asyncio
    async def test_warm_cache_error_handling(self, mock_service):
        """Test that warm_cache continues processing when some queries fail."""
        call_count = 0
        
        async def mock_search_combined(query: str, limit: int = 10):
            nonlocal call_count
            call_count += 1
            
            # Fail every third query
            if call_count % 3 == 0:
                raise Exception(f"Mock error for query: {query}")
            
            return [{"test": "result"}]

        mock_service.search_combined = mock_search_combined
        
        queries = [f"test query {i}" for i in range(9)]
        
        # Should not raise exception despite 3 failures
        await mock_service.warm_cache(queries, parallel=2)
        
        # Verify all queries were attempted
        assert call_count == 9

    @pytest.mark.asyncio
    async def test_warm_cache_performance_improvement(self, mock_service):
        """Test that warm_cache is faster than sequential processing."""
        api_delay = 0.1  # 100ms per API call
        
        async def mock_search_combined(query: str, limit: int = 10):
            await asyncio.sleep(api_delay)
            return [{"test": "result"}]

        mock_service.search_combined = mock_search_combined
        
        queries = [f"test query {i}" for i in range(10)]
        
        # Test concurrent warm_cache
        start_time = time.time()
        await mock_service.warm_cache(queries, parallel=5)
        concurrent_time = time.time() - start_time
        
        # Test sequential processing for comparison
        start_time = time.time()
        for query in queries:
            await mock_service.search_combined(query)
        sequential_time = time.time() - start_time
        
        # Concurrent should be significantly faster
        speedup_ratio = sequential_time / concurrent_time
        assert speedup_ratio > 2.0, f"Insufficient speedup: {speedup_ratio:.2f}x"

    @pytest.mark.asyncio
    async def test_warm_cache_configuration(self, mock_service):
        """Test that warm_cache uses configuration defaults properly."""
        mock_service.search_combined = AsyncMock(return_value=[])
        
        with patch('knowledge_storm.storm_config.STORMConfig') as mock_config_class:
            mock_config = Mock()
            mock_config.cache_warm_parallel = 7
            mock_config_class.return_value = mock_config
            
            # Test with no parallel parameter (should use config)
            queries = ["test query"]
            await mock_service.warm_cache(queries)
            
            # Verify config was used
            mock_config_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_warm_cache_large_workload(self, mock_service):
        """Test warm_cache with academic research scale workloads."""
        mock_service.search_combined = AsyncMock(return_value=[])
        
        # Test with 1000 queries (typical literature review scale)
        queries = [f"academic paper query {i}" for i in range(1000)]
        
        start_time = time.time()
        await mock_service.warm_cache(queries, parallel=20)
        duration = time.time() - start_time
        
        # Should complete within reasonable time (5 minutes max)
        assert duration < 300, f"Large workload took too long: {duration:.2f}s"
        
        # Verify all queries were processed
        assert mock_service.search_combined.call_count == 1000

    @pytest.mark.asyncio
    async def test_warm_cache_logging(self, mock_service, caplog):
        """Test that warm_cache produces proper logging output."""
        mock_service.search_combined = AsyncMock(return_value=[])
        
        queries = ["test query 1", "test query 2"]
        
        with caplog.at_level("INFO"):
            await mock_service.warm_cache(queries, parallel=2)
        
        # Check for start and completion log messages
        log_messages = [record.message for record in caplog.records]
        
        start_logged = any("Starting warm_cache" in msg for msg in log_messages)
        completion_logged = any("Completed warm_cache" in msg for msg in log_messages)
        
        assert start_logged, "Missing start log message"
        assert completion_logged, "Missing completion log message"


class TestCrossrefRMOptionalDependency:
    """Test optional dependency handling for CrossrefRM."""

    def test_crossref_rm_import_success(self):
        """Test successful import of CrossrefRM when dependencies are available."""
        from knowledge_storm.modules import CrossrefRM
        assert CrossrefRM is not None

    @patch.dict('sys.modules', {'dspy': None})
    def test_crossref_rm_import_failure_handling(self):
        """Test graceful handling when dspy dependency is missing."""
        # Force reimport with mocked missing dependency
        import importlib
        import sys
        
        # Remove from cache to force reimport
        modules_to_reload = [
            'knowledge_storm.modules',
            'knowledge_storm.modules.academic_rm'
        ]
        
        for mod in modules_to_reload:
            if mod in sys.modules:
                del sys.modules[mod]
        
        try:
            from knowledge_storm.modules import CrossrefRM
            # Should be None when dependency is missing
            assert CrossrefRM is None
        except ImportError:
            # Also acceptable - import error is handled gracefully
            pass


if __name__ == "__main__":
    pytest.main([__file__])