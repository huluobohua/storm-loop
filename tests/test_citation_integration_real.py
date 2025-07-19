"""
Integration Tests - Real Citation Verification
Tests that verify the system works with actual dependencies when enabled.
"""

import pytest
import os
from knowledge_storm.citation_verification.validator import CitationValidator, OpenAlexClient, CrossrefClient
from knowledge_storm.citation_verification.models import Citation


class TestRealCitationIntegration:
    """Integration tests that run with real dependencies when enabled."""
    
    def setup_method(self):
        """Set up real clients for integration testing."""
        if not os.getenv("INTEGRATION_TESTS_ENABLED"):
            pytest.skip("Integration tests not enabled - set INTEGRATION_TESTS_ENABLED=1")
        
        # Use real clients - no mocks
        self.validator = CitationValidator(
            openalex_client=OpenAlexClient(),
            crossref_client=CrossrefClient()
        )
    
    @pytest.mark.asyncio
    async def test_validates_real_citation_successfully(self):
        """Test that the system can validate a well-known real citation."""
        # This is a real, well-known paper that should exist
        citation = Citation(
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
            journal="Advances in Neural Information Processing Systems",
            year=2017
        )
        
        # This should work with real APIs
        result = await self.validator.verify_citation(citation)
        
        # Should successfully validate
        assert result.is_verified is True
        assert result.confidence_score > 0.8
        assert result.verification_source in ["openalex", "crossref"]
    
    @pytest.mark.asyncio 
    async def test_handles_nonexistent_citation_gracefully(self):
        """Test that the system gracefully handles citations that don't exist."""
        # This citation should not exist in any database
        fake_citation = Citation(
            title="A Completely Fabricated Study on Nonexistent Phenomena in Academic Research",
            authors=["John Fakename", "Jane Notreal"],
            journal="International Journal of Fabricated Research",
            year=2020  # Recent but fake
        )
        
        # Should handle gracefully without crashing
        result = await self.validator.verify_citation(fake_citation)
        
        # Should return invalid result, not crash
        assert result.is_verified is False
        assert result.confidence_score == 0.0
        assert len(result.issues) > 0  # Should have issues explaining why it failed