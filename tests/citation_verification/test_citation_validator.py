"""
Test-Driven Development for CitationValidator

Tests written BEFORE implementation to specify exact behavior.
Covers all edge cases, error scenarios, and integration points.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from knowledge_storm.citation_verification.models import (
    Citation, VerificationResult, ValidationReport
)
from knowledge_storm.citation_verification.validator import CitationValidator


class TestCitationValidator:
    """Test suite for CitationValidator following TDD principles."""
    
    @pytest.fixture
    def mock_openalex_client(self):
        """Mock OpenAlex client for testing."""
        mock_client = AsyncMock()
        return mock_client
    
    @pytest.fixture  
    def mock_crossref_client(self):
        """Mock Crossref client for testing."""
        mock_client = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def citation_validator(self, mock_openalex_client, mock_crossref_client):
        """Citation validator with mocked dependencies."""
        return CitationValidator(
            openalex_client=mock_openalex_client,
            crossref_client=mock_crossref_client
        )
    
    @pytest.fixture
    def valid_citation(self):
        """Valid citation for testing."""
        return Citation(
            title="Deep Learning for Natural Language Processing",
            authors=["Smith, J.", "Doe, A."],
            journal="Nature Machine Intelligence", 
            year=2023,
            volume="5",
            pages="123-135",
            doi="10.1038/s42256-023-00123-4"
        )
    
    @pytest.fixture
    def fabricated_citation(self):
        """Fabricated citation that should be detected."""
        return Citation(
            title="Quantum Computing Advances in Fake Research",
            authors=["Fictional, A.", "Made, U.P."],
            journal="Journal of Imaginary Science",
            year=2024,
            volume="42",
            pages="1-999",
            doi="10.1000/fake.doi.123"
        )

    # RED PHASE: Write failing tests first
    
    @pytest.mark.asyncio
    async def test_verify_valid_citation_returns_verified_result(
        self, citation_validator, valid_citation, mock_openalex_client
    ):
        """Test that valid citations return verified results."""
        # Arrange
        mock_openalex_client.verify_paper.return_value = {
            'exists': True,
            'metadata_matches': True,
            'authors_match': True
        }
        
        # Act
        result = await citation_validator.verify_citation(valid_citation)
        
        # Assert
        assert isinstance(result, VerificationResult)
        assert result.is_verified is True
        assert result.confidence_score >= 0.9
        assert result.verification_source in ['openalex', 'openalex_crossref']
        assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_verify_fabricated_citation_returns_failed_result(
        self, citation_validator, fabricated_citation, mock_openalex_client
    ):
        """Test that fabricated citations are detected and rejected."""
        # Arrange
        mock_openalex_client.verify_paper.return_value = {
            'exists': False,
            'metadata_matches': False,
            'authors_match': False
        }
        
        # Act
        result = await citation_validator.verify_citation(fabricated_citation)
        
        # Assert
        assert isinstance(result, VerificationResult)
        assert result.is_verified is False
        assert result.confidence_score <= 0.1
        assert 'fabricated' in result.issues
        assert result.verification_source in ['openalex', 'openalex_crossref']
    
    @pytest.mark.asyncio
    async def test_verify_citation_with_invalid_doi_returns_failed_result(
        self, citation_validator, mock_crossref_client
    ):
        """Test DOI validation detects invalid DOIs."""
        # Arrange
        citation = Citation(
            title="Test Paper",
            authors=["Test, A."],
            journal="Test Journal",
            year=2023,
            doi="invalid.doi.format"
        )
        mock_crossref_client.validate_doi.return_value = False
        
        # Act
        result = await citation_validator.verify_citation(citation)
        
        # Assert
        assert result.is_verified is False
        assert 'invalid_doi' in result.issues
    
    @pytest.mark.asyncio
    async def test_verify_citation_handles_api_timeouts_gracefully(
        self, citation_validator, valid_citation, mock_openalex_client
    ):
        """Test error handling for API timeouts."""
        # Arrange
        mock_openalex_client.verify_paper.side_effect = asyncio.TimeoutError()
        
        # Act
        result = await citation_validator.verify_citation(valid_citation)
        
        # Assert
        assert isinstance(result, VerificationResult)
        assert result.is_verified is False
        assert result.error_type == 'timeout'
        assert 'api_timeout' in result.issues
    
    @pytest.mark.asyncio
    async def test_verify_citation_handles_network_errors_gracefully(
        self, citation_validator, valid_citation, mock_openalex_client
    ):
        """Test error handling for network failures."""
        # Arrange
        mock_openalex_client.verify_paper.side_effect = ConnectionError("Network error")
        
        # Act
        result = await citation_validator.verify_citation(valid_citation)
        
        # Assert
        assert result.is_verified is False
        assert result.error_type == 'network_error'
        assert 'connection_failed' in result.issues
    
    @pytest.mark.asyncio
    async def test_validate_bibliography_processes_multiple_citations(
        self, citation_validator, valid_citation, fabricated_citation
    ):
        """Test batch validation of citation lists."""
        # Arrange
        citations = [valid_citation, fabricated_citation]
        
        # Act
        report = await citation_validator.validate_bibliography(citations)
        
        # Assert
        assert isinstance(report, ValidationReport)
        assert report.total_citations == 2
        assert report.verified_count >= 0
        assert report.fabricated_count >= 0
        assert len(report.verification_results) == 2
    
    @pytest.mark.asyncio
    async def test_validate_bibliography_with_empty_list_returns_empty_report(
        self, citation_validator
    ):
        """Test edge case of empty citation list."""
        # Act
        report = await citation_validator.validate_bibliography([])
        
        # Assert
        assert report.total_citations == 0
        assert report.verified_count == 0
        assert report.fabricated_count == 0
        assert len(report.verification_results) == 0
    
    def test_citation_validator_respects_sandi_metz_rules(self):
        """Test that CitationValidator follows Sandi Metz rules."""
        # This test ensures our implementation follows the rules:
        # - No more than 100 lines per class
        # - No more than 5 lines per method
        # - No more than 4 parameters per method
        # - No more than 4 instance variables
        pass  # Will implement after class is created
    
    @pytest.mark.asyncio
    async def test_verify_citation_with_partial_metadata_match(
        self, citation_validator, mock_openalex_client
    ):
        """Test handling of citations with partial metadata matches."""
        # Arrange
        citation = Citation(
            title="Slightly Different Title from Database",
            authors=["Smith, J."],
            journal="Nature",
            year=2023
        )
        mock_openalex_client.verify_paper.return_value = {
            'exists': True,
            'metadata_matches': False,
            'title_similarity': 0.8,
            'authors_match': True
        }
        
        # Act
        result = await citation_validator.verify_citation(citation)
        
        # Assert
        assert result.is_verified is True  # Should still verify with high similarity
        assert result.confidence_score >= 0.7
        assert 'partial_match' in result.issues
    
    @pytest.mark.asyncio 
    async def test_verify_citation_respects_rate_limits(
        self, citation_validator, valid_citation, mock_openalex_client
    ):
        """Test that rate limiting is properly handled."""
        # Arrange
        mock_openalex_client.verify_paper.side_effect = Exception("Rate limit exceeded")
        
        # Act
        result = await citation_validator.verify_citation(valid_citation)
        
        # Assert
        # Should handle rate limit as an error for now
        assert result.is_verified is False
        assert result.error_type == "unknown_error"
        assert "Rate limit exceeded" in result.issues


class TestCitationValidatorPerformance:
    """Performance tests for CitationValidator."""
    
    @pytest.mark.asyncio
    async def test_verification_completes_within_time_limit(self):
        """Test that citation verification meets performance requirements."""
        # Arrange
        mock_openalex = AsyncMock()
        mock_crossref = AsyncMock()
        mock_openalex.verify_paper.return_value = {'exists': True, 'metadata_matches': True, 'authors_match': True}
        
        validator = CitationValidator(mock_openalex, mock_crossref)
        citation = Citation(
            title="Test Paper",
            authors=["Test, A."],
            journal="Test Journal",
            year=2023
        )
        
        start_time = datetime.now()
        
        # Act
        await validator.verify_citation(citation)
        
        # Assert
        duration = (datetime.now() - start_time).total_seconds()
        assert duration < 5.0  # Must complete within 5 seconds per requirements
    
    @pytest.mark.asyncio
    async def test_batch_validation_scales_appropriately(self):
        """Test that batch validation performance scales appropriately."""
        # Arrange
        mock_openalex = AsyncMock()
        mock_crossref = AsyncMock()
        mock_openalex.verify_paper.return_value = {'exists': True, 'metadata_matches': True, 'authors_match': True}
        
        validator = CitationValidator(mock_openalex, mock_crossref)
        citation = Citation(
            title="Test Paper",
            authors=["Test, A."],
            journal="Test Journal", 
            year=2023
        )
        citations = [citation] * 10  # 10 identical citations
        start_time = datetime.now()
        
        # Act
        await validator.validate_bibliography(citations)
        
        # Assert
        duration = (datetime.now() - start_time).total_seconds()
        assert duration < 30.0  # Batch processing should be efficient


class TestCitationValidatorIntegration:
    """Integration tests for CitationValidator with real dependencies."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_openalex_integration(self):
        """Integration test with real OpenAlex API (requires network)."""
        import os
        if not os.getenv("INTEGRATION_TESTS_ENABLED"):
            pytest.skip("Integration tests not enabled - set INTEGRATION_TESTS_ENABLED=1")
        
        from knowledge_storm.citation_verification import CitationValidator
        from knowledge_storm.citation_verification.models import Citation
        
        # Use real validator (no mocks)
        validator = CitationValidator()
        
        # Real citation that should exist in OpenAlex
        real_citation = Citation(
            id="test_1",
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            journal="Advances in Neural Information Processing Systems",
            year=2017,
            doi="10.48550/arXiv.1706.03762"
        )
        
        # Test validation
        result = await validator.validate_citation(real_citation)
        
        # Should find the paper
        assert result.is_valid is True
        assert result.confidence_score > 0.8
        assert result.source_database in ["openalex", "crossref"]
        assert "transformer" in result.title.lower() or "attention" in result.title.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_crossref_integration(self):
        """Integration test with real Crossref API (requires network)."""
        import os
        if not os.getenv("INTEGRATION_TESTS_ENABLED"):
            pytest.skip("Integration tests not enabled - set INTEGRATION_TESTS_ENABLED=1")
        
        from knowledge_storm.citation_verification import CitationValidator
        from knowledge_storm.citation_verification.models import Citation
        
        # Use real validator (no mocks)
        validator = CitationValidator()
        
        # Real citation that should exist in Crossref
        real_citation = Citation(
            id="test_2",
            title="The PageRank Citation Ranking: Bringing Order to the Web",
            authors=["Lawrence Page", "Sergey Brin", "Rajeev Motwani", "Terry Winograd"],
            journal="Stanford InfoLab",
            year=1999,
            doi="10.1145/289444.289459"  # This is a real DOI
        )
        
        # Test validation
        result = await validator.validate_citation(real_citation)
        
        # Should find the paper
        assert result.is_valid is True
        assert result.confidence_score > 0.7
        assert result.source_database in ["openalex", "crossref"]
        assert "pagerank" in result.title.lower() or "page" in result.title.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_error_recovery(self):
        """Test error recovery and fallback strategies."""
        import os
        if not os.getenv("INTEGRATION_TESTS_ENABLED"):
            pytest.skip("Integration tests not enabled - set INTEGRATION_TESTS_ENABLED=1")
        
        from knowledge_storm.citation_verification import CitationValidator
        from knowledge_storm.citation_verification.models import Citation
        
        validator = CitationValidator()
        
        # Citation with intentionally problematic data to test error handling
        problematic_citation = Citation(
            id="test_error",
            title="Ä" * 500,  # Very long title with special chars
            authors=["Invalid@Author.Name"] * 100,  # Many invalid authors
            journal="Non-Existent Journal åæø",
            year=1800,  # Very old year
            doi="invalid-doi-format"
        )
        
        # Should handle gracefully without crashing
        result = await validator.validate_citation(problematic_citation)
        
        # Should return a result (even if invalid)
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'confidence_score')
        # Likely invalid, but shouldn't crash
        assert result.confidence_score >= 0.0