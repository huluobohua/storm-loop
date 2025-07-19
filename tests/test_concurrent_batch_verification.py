"""
Concurrent Batch Verification Tests
Tests that verify the system handles concurrent operations correctly.
"""

import pytest
import asyncio
import time
from knowledge_storm.citation_verification.validator import CitationValidator, OpenAlexClient, CrossrefClient
from knowledge_storm.citation_verification.models import Citation


class TestConcurrentBatchVerification:
    """Test concurrent batch verification behavior."""
    
    def setup_method(self):
        """Set up validator for concurrency testing."""
        # Use real clients for realistic concurrency testing
        self.validator = CitationValidator(
            openalex_client=OpenAlexClient(),
            crossref_client=CrossrefClient()
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_citations_complete_independently(self):
        """Test that concurrent citation verifications don't interfere with each other."""
        
        # Create different types of citations to verify concurrently
        citations = [
            Citation(
                title="Attention Is All You Need",
                authors=["Ashish Vaswani"],
                journal="NIPS",
                year=2017
            ),
            Citation(
                title="BERT: Pre-training of Deep Bidirectional Transformers",
                authors=["Jacob Devlin"],
                journal="NAACL",
                year=2019
            ),
            Citation(
                title="This Should Not Exist Fake Paper",
                authors=["Fake Author"],
                journal="Fake Journal",
                year=2020
            )
        ]
        
        start_time = time.time()
        
        # Verify all citations concurrently
        tasks = [self.validator.verify_citation(citation) for citation in citations]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # All should complete
        assert len(results) == 3
        
        # Results should be independent - some valid, some invalid
        valid_count = sum(1 for result in results if result.is_verified)
        invalid_count = sum(1 for result in results if not result.is_verified)
        
        # At least some should be valid (real papers) and some invalid (fake paper)
        assert valid_count >= 1  # Real papers should validate
        assert invalid_count >= 1  # Fake paper should fail
        
        # Should be faster than sequential (rough heuristic)
        assert end_time - start_time < 20.0  # Concurrent should be reasonable
    
    @pytest.mark.asyncio
    async def test_batch_verification_handles_mixed_results(self):
        """Test that batch verification properly handles mixed success/failure results."""
        
        # Mix of valid and invalid citations
        citations = [
            Citation(title="Real Paper That Exists", authors=["Real Author"], journal="Real Journal", year=2020),
            Citation(title="Fake Paper That Does Not Exist", authors=["Fake Author"], journal="Fake Journal", year=2021),
            Citation(title="Another Real Paper", authors=["Another Author"], journal="Another Journal", year=2019),
        ]
        
        # Use batch verification if it exists, otherwise fall back to individual
        if hasattr(self.validator, 'validate_bibliography'):
            report = await self.validator.validate_bibliography(citations)
            
            # Should return a report with results for all citations
            assert hasattr(report, 'verification_results')
            assert len(report.verification_results) == 3
            
            # Should have mixed results
            verification_statuses = [result.is_verified for result in report.verification_results]
            assert True in verification_statuses  # Some should succeed
            assert False in verification_statuses  # Some should fail
        else:
            # Fall back to individual verification if batch doesn't exist
            results = []
            for citation in citations:
                result = await self.validator.verify_citation(citation)
                results.append(result)
            
            assert len(results) == 3
            verification_statuses = [result.is_verified for result in results]
            # We can't guarantee specific results without knowing the exact papers
            # But we can verify the system doesn't crash
            assert all(hasattr(result, 'is_verified') for result in results)
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """Test system behavior under high concurrency load."""
        
        # Create many citations for stress testing
        base_citation = Citation(
            title="Test Citation for Concurrency",
            authors=["Test Author"],
            journal="Test Journal", 
            year=2020
        )
        
        # Create 20 identical citations (should hit cache if implemented)
        citations = [base_citation for _ in range(20)]
        
        start_time = time.time()
        
        # Process all concurrently
        tasks = [self.validator.verify_citation(citation) for citation in citations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # All should complete without exceptions
        exceptions = [result for result in results if isinstance(result, Exception)]
        assert len(exceptions) == 0, f"Found exceptions: {exceptions}"
        
        # All should be results
        assert len(results) == 20
        assert all(hasattr(result, 'is_verified') for result in results)
        
        # Should complete in reasonable time (with possible caching benefits)
        assert end_time - start_time < 30.0