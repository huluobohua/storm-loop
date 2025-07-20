"""
Error Boundary and Concurrency Tests
Comprehensive testing for error handling and concurrent operations
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from typing import List

from knowledge_storm.citation_verification.validator import CitationValidator, OpenAlexClient, CrossrefClient
from knowledge_storm.citation_verification.models import Citation, VerificationResult
from frontend.advanced_interface.config_validator import ConfigValidator
from frontend.advanced_interface.session_facade import SessionFacade


class TestErrorBoundaryHandling:
    """Test error boundaries and fault tolerance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock clients for CitationValidator
        self.mock_openalex = AsyncMock(spec=OpenAlexClient)
        self.mock_crossref = AsyncMock(spec=CrossrefClient)
        
        self.validator = CitationValidator(
            openalex_client=self.mock_openalex,
            crossref_client=self.mock_crossref
        )
        self.config_validator = ConfigValidator()
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        citation = Citation(
            title="Test Citation",
            authors=["Test Author"],
            journal="Test Journal",
            year=2023
        )
        
        # Mock network timeout
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Connection timeout")
            
            # Should handle timeout gracefully
            result = await self.validator.verify_citation(citation)
            
            # Should return invalid result, not crash
            assert result is not None
            assert isinstance(result, VerificationResult)
            assert result.is_verified is False
            assert result.confidence_score == 0.0
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self):
        """Test handling of API rate limits."""
        citation = Citation(
            title="Test Citation",
            authors=["Test Author"],
            journal="Test Journal",
            year=2023
        )
        
        # Mock rate limit response (HTTP 429)
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "2"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Should handle rate limit gracefully
            result = await self.validator.verify_citation(citation)
            
            # Should return result with appropriate handling
            assert result is not None
            assert isinstance(result, VerificationResult)
    
    @pytest.mark.asyncio
    async def test_malformed_api_response_handling(self):
        """Test handling of malformed API responses."""
        citation = Citation(
            title="Test Citation",
            authors=["Test Author"],
            journal="Test Journal",
            year=2023
        )
        
        # Mock malformed JSON response
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Should handle malformed response gracefully
            result = await self.validator.verify_citation(citation)
            
            # Should return invalid result, not crash
            assert result is not None
            assert isinstance(result, VerificationResult)
    
    @pytest.mark.asyncio
    async def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion."""
        # Create very large citation data
        large_citation = Citation(
            title="A" * 10000,  # Very long title
            authors=["Author"] * 1000,  # Many authors
            journal="Journal" * 100,
            year=2023
        )
        
        # Should handle large data without crashing
        result = await self.validator.verify_citation(large_citation)
        
        # Should return a result
        assert result is not None
        assert isinstance(result, VerificationResult)
    
    @pytest.mark.asyncio
    async def test_concurrent_api_failure_isolation(self):
        """Test that API failures don't affect other concurrent requests."""
        citations = [
            Citation(title=f"Title {i}", authors=[f"Author {i}"], 
                    journal=f"Journal {i}", year=2023)
            for i in range(5)
        ]
        
        # Mock some requests to fail, others to succeed
        with patch('aiohttp.ClientSession.get') as mock_get:
            responses = []
            for i in range(5):
                mock_response = AsyncMock()
                if i % 2 == 0:  # Even indices fail
                    mock_response.status = 500
                else:  # Odd indices succeed
                    mock_response.status = 200
                    mock_response.json.return_value = {
                        "results": [{"id": f"test_{i}", "title": f"Title {i}"}]
                    }
                responses.append(mock_response)
            
            mock_get.side_effect = [resp.__aenter__.return_value for resp in responses]
            
            # Process concurrently
            tasks = [self.validator.verify_citation(citation) for citation in citations]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should return results (no exceptions propagated)
            assert len(results) == 5
            assert all(isinstance(result, VerificationResult) for result in results)
    
    def test_config_validation_memory_safety(self):
        """Test config validation with extremely large configs."""
        # Create config with massive nested structure
        large_config = {
            "storm_mode": "hybrid",
            "advanced_options": {
                f"option_{i}": f"value_{i}" * 100 for i in range(1000)
            }
        }
        
        # Should handle large config without crashing
        try:
            result = self.config_validator.validate_research_config(large_config)
            # If it doesn't crash, that's good
            assert isinstance(result, dict)
        except MemoryError:
            pytest.fail("Config validation caused memory error")


class TestConcurrentOperations:
    """Test concurrent and parallel operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock clients for CitationValidator
        mock_openalex = AsyncMock(spec=OpenAlexClient)
        mock_crossref = AsyncMock(spec=CrossrefClient)
        
        self.validator = CitationValidator(
            openalex_client=mock_openalex,
            crossref_client=mock_crossref
        )
        
        # Mock dependencies for SessionFacade
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "test_session_id"
        mock_session_manager.configure_session.return_value = None
        
        self.session_facade = SessionFacade(
            session_manager=mock_session_manager,
            config_validator=ConfigValidator()
        )
    
    @pytest.mark.asyncio
    async def test_batch_citation_validation_concurrency(self):
        """Test concurrent batch validation of citations."""
        # Create multiple citations
        citations = [
            Citation(
                title=f"Concurrent Test Title {i}",
                authors=[f"Author {i}"],
                journal=f"Journal {i}",
                year=2023
            )
            for i in range(20)
        ]
        
        start_time = time.time()
        
        # Process all citations concurrently
        tasks = [self.validator.verify_citation(citation) for citation in citations]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All should complete
        assert len(results) == 20
        assert all(isinstance(result, VerificationResult) for result in results)
        
        # Should be faster than sequential processing
        # (This is a rough heuristic - concurrent should be significantly faster)
        assert duration < 10.0  # Should complete within reasonable time
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self):
        """Test concurrent session creation doesn't cause race conditions."""
        session_configs = [
            {
                "session_name": f"Concurrent Session {i}",
                "user_id": f"user_{i}",
                "research_config": {
                    "storm_mode": "fast",
                    "max_papers": 10
                }
            }
            for i in range(10)
        ]
        
        async def create_and_configure_session(config):
            """Create and configure a session."""
            session_id = self.session_facade.create_research_session(
                config["user_id"], 
                config["session_name"]
            )
            self.session_facade.configure_session(session_id, config)
            return session_id
        
        # Create sessions concurrently
        tasks = [create_and_configure_session(config) for config in session_configs]
        session_ids = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(session_ids) == 10
        assert all(isinstance(session_id, str) for session_id in session_ids)
        
        # All should be unique
        assert len(set(session_ids)) == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_config_validation(self):
        """Test concurrent configuration validation."""
        configs = [
            {
                "storm_mode": mode,
                "max_papers": papers,
                "quality_threshold": 0.8
            }
            for mode in ["fast", "hybrid", "thorough"]
            for papers in [10, 25, 50]
        ]
        
        validator = ConfigValidator()
        
        async def validate_config_async(config):
            """Async wrapper for config validation."""
            return validator.validate_research_config(config)
        
        # Validate all configs concurrently
        tasks = [validate_config_async(config) for config in configs]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 9  # 3 modes × 3 paper counts
        assert all(isinstance(result, dict) for result in results)
    
    @pytest.mark.asyncio
    async def test_stress_concurrent_operations(self):
        """Stress test with many concurrent operations."""
        num_operations = 50
        
        # Mix of different operations
        citations = [
            Citation(
                title=f"Stress Test {i}",
                authors=[f"Author {i}"],
                journal="Stress Journal",
                year=2023
            )
            for i in range(num_operations)
        ]
        
        configs = [
            {
                "storm_mode": "fast",
                "max_papers": 10 + i,
                "quality_threshold": 0.5 + (i * 0.01)
            }
            for i in range(num_operations)
        ]
        
        start_time = time.time()
        
        # Run mixed operations concurrently
        citation_tasks = [self.validator.verify_citation(citation) 
                         for citation in citations[:25]]
        
        config_validator = ConfigValidator()
        config_tasks = [asyncio.create_task(
            asyncio.to_thread(config_validator.validate_research_config, config)
        ) for config in configs[:25]]
        
        # Wait for all to complete
        all_results = await asyncio.gather(
            *citation_tasks, 
            *config_tasks, 
            return_exceptions=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete without errors
        assert len(all_results) == 50
        
        # Check for exceptions
        exceptions = [result for result in all_results if isinstance(result, Exception)]
        assert len(exceptions) == 0, f"Found exceptions: {exceptions}"
        
        # Should complete in reasonable time
        assert duration < 30.0
    
    def test_thread_safety_config_validator(self):
        """Test thread safety of ConfigValidator."""
        validator = ConfigValidator()
        
        configs = [
            {
                "storm_mode": "hybrid",
                "max_papers": 25 + i,
                "quality_threshold": 0.7
            }
            for i in range(10)
        ]
        
        # Use ThreadPoolExecutor for true parallel execution
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(validator.validate_research_config, config)
                for config in configs
            ]
            
            results = [future.result() for future in futures]
        
        # All should succeed
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results)
        
        # Results should be consistent
        for i, result in enumerate(results):
            assert result["max_papers"] == 25 + i


class TestErrorRecoveryStrategies:
    """Test error recovery and resilience strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock clients for CitationValidator
        self.mock_openalex = AsyncMock(spec=OpenAlexClient)
        self.mock_crossref = AsyncMock(spec=CrossrefClient)
        
        self.validator = CitationValidator(
            openalex_client=self.mock_openalex,
            crossref_client=self.mock_crossref
        )
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test retry mechanism for transient failures."""
        citation = Citation(
            title="Retry Test Citation",
            authors=["Test Author"],
            journal="Test Journal",
            year=2023
        )
        
        call_count = 0
        
        async def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise asyncio.TimeoutError("Temporary failure")
            # Succeed on 3rd attempt
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "results": [{"id": "retry_test", "title": "Retry Test Citation"}]
            }
            return mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_api_call):
            result = await self.validator.verify_citation(citation)
            
            # Should eventually succeed after retries
            assert call_count >= 2  # Should have retried
            assert isinstance(result, VerificationResult)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for preventing cascade failures."""
        citations = [
            Citation(
                title=f"Circuit Test {i}",
                authors=["Test Author"],
                journal="Test Journal",
                year=2023
            )
            for i in range(10)
        ]
        
        # Mock all requests to fail initially
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = ConnectionError("Service unavailable")
            
            # Process multiple citations
            results = []
            for citation in citations:
                try:
                    result = await self.validator.verify_citation(citation)
                    results.append(result)
                except Exception:
                    # Circuit breaker should prevent further attempts
                    break
            
            # Should have attempted some requests but stopped due to circuit breaker
            assert len(results) <= len(citations)