"""
Test-Driven Development for IntegrityChecker Dependency Injection

Tests written BEFORE refactoring to specify exact behavior.
Ensures dependency injection compliance and integration with CitationValidator.
"""

import pytest
from unittest.mock import Mock, patch
from knowledge_storm.citation_verification.models import Citation, VerificationResult
from knowledge_storm.citation_verification.integrity_checker import IntegrityChecker


class TestIntegrityCheckerDependencyInjection:
    """Test suite for IntegrityChecker dependency injection refactor."""
    
    @pytest.fixture
    def mock_title_detector(self):
        """Mock title pattern detector."""
        mock = Mock()
        mock.detect.return_value = []
        return mock
    
    @pytest.fixture
    def mock_author_detector(self):
        """Mock author pattern detector.""" 
        mock = Mock()
        mock.detect.return_value = []
        return mock
    
    @pytest.fixture
    def mock_journal_detector(self):
        """Mock journal pattern detector."""
        mock = Mock()
        mock.detect.return_value = []
        return mock
    
    @pytest.fixture
    def mock_doi_detector(self):
        """Mock DOI pattern detector."""
        mock = Mock()
        mock.detect.return_value = []
        return mock
    
    @pytest.fixture
    def valid_citation(self):
        """Valid citation for testing."""
        return Citation(
            title="Valid Research Title",
            authors=["Smith, J.", "Doe, A."],
            journal="Nature",
            year=2023,
            doi="10.1038/nature.2023.123"
        )
    
    def test_integrity_checker_accepts_detector_dependencies(
        self, mock_title_detector, mock_author_detector, 
        mock_journal_detector, mock_doi_detector
    ):
        """TEST (RED): IntegrityChecker should accept detectors via constructor."""
        # This test will fail until we refactor IntegrityChecker
        
        # Act & Assert
        checker = IntegrityChecker(
            title_detector=mock_title_detector,
            author_detector=mock_author_detector,
            journal_detector=mock_journal_detector,
            doi_detector=mock_doi_detector
        )
        
        assert checker._title_detector is mock_title_detector
        assert checker._author_detector is mock_author_detector
        assert checker._journal_detector is mock_journal_detector
        assert checker._doi_detector is mock_doi_detector
    
    def test_integrity_checker_uses_injected_detectors(
        self, mock_title_detector, mock_author_detector,
        mock_journal_detector, mock_doi_detector, valid_citation
    ):
        """TEST (RED): IntegrityChecker should use injected detectors."""
        # Arrange
        mock_title_detector.detect.return_value = ["fabricated_title"]
        mock_author_detector.detect.return_value = ["suspicious_author"]
        mock_journal_detector.detect.return_value = []
        mock_doi_detector.detect.return_value = []
        
        checker = IntegrityChecker(
            title_detector=mock_title_detector,
            author_detector=mock_author_detector,
            journal_detector=mock_journal_detector,
            doi_detector=mock_doi_detector
        )
        
        # Act
        issues = checker.check_citation(valid_citation)
        
        # Assert
        assert "fabricated_title" in issues
        assert "suspicious_author" in issues
        mock_title_detector.detect.assert_called_once_with(valid_citation.title)
        mock_author_detector.detect.assert_called_once_with(valid_citation.authors)
    
    def test_integrity_checker_maintains_backward_compatibility(self):
        """TEST (RED): IntegrityChecker should work without dependency injection."""
        # For backward compatibility, should work with no parameters
        
        # Act & Assert - this should work (may create real detectors)
        checker = IntegrityChecker()
        assert hasattr(checker, '_title_detector')
        assert hasattr(checker, '_author_detector')
        assert hasattr(checker, '_journal_detector')
        assert hasattr(checker, '_doi_detector')


class TestCitationValidatorIntegrityIntegration:
    """Test suite for CitationValidator + IntegrityChecker integration."""
    
    @pytest.fixture
    def mock_integrity_checker(self):
        """Mock integrity checker."""
        mock = Mock()
        mock.check_citation.return_value = []
        return mock
    
    @pytest.fixture
    def mock_openalex_client(self):
        """Mock OpenAlex client."""
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.verify_paper = AsyncMock(return_value={
            'exists': True,
            'metadata_matches': True,
            'authors_match': True
        })
        return mock
    
    @pytest.fixture
    def mock_crossref_client(self):
        """Mock Crossref client.""" 
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.verify_paper = AsyncMock(return_value={
            'exists': True,
            'metadata_matches': True
        })
        return mock
    
    @pytest.fixture
    def valid_citation(self):
        """Valid citation for testing."""
        return Citation(
            title="Valid Research Title",
            authors=["Smith, J."],
            journal="Nature",
            year=2023
        )
    
    @pytest.mark.asyncio
    async def test_citation_validator_accepts_integrity_checker_dependency(
        self, mock_openalex_client, mock_crossref_client, mock_integrity_checker
    ):
        """TEST (RED): CitationValidator should accept IntegrityChecker via constructor."""
        # This test will fail until we refactor CitationValidator
        
        from knowledge_storm.citation_verification.validator import CitationValidator
        
        # Act & Assert
        validator = CitationValidator(
            openalex_client=mock_openalex_client,
            crossref_client=mock_crossref_client,
            integrity_checker=mock_integrity_checker
        )
        
        assert validator._integrity_checker is mock_integrity_checker
    
    @pytest.mark.asyncio
    async def test_citation_validator_calls_integrity_check_before_api_verification(
        self, mock_openalex_client, mock_crossref_client, 
        mock_integrity_checker, valid_citation
    ):
        """TEST (RED): CitationValidator should call integrity check BEFORE external APIs."""
        from knowledge_storm.citation_verification.validator import CitationValidator
        
        # Arrange
        mock_integrity_checker.check_citation.return_value = []
        
        validator = CitationValidator(
            openalex_client=mock_openalex_client,
            crossref_client=mock_crossref_client,
            integrity_checker=mock_integrity_checker
        )
        
        # Act
        await validator.verify_citation(valid_citation)
        
        # Assert
        mock_integrity_checker.check_citation.assert_called_once_with(valid_citation)
        # Should only call external API if integrity passes
        mock_openalex_client.verify_paper.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_citation_validator_rejects_citation_with_integrity_issues(
        self, mock_openalex_client, mock_crossref_client,
        mock_integrity_checker, valid_citation
    ):
        """TEST (RED): CitationValidator should reject citations with integrity issues."""
        from knowledge_storm.citation_verification.validator import CitationValidator
        
        # Arrange
        mock_integrity_checker.check_citation.return_value = [
            "fabricated_title", "suspicious_author"
        ]
        
        validator = CitationValidator(
            openalex_client=mock_openalex_client,
            crossref_client=mock_crossref_client,
            integrity_checker=mock_integrity_checker
        )
        
        # Act
        result = await validator.verify_citation(valid_citation)
        
        # Assert
        assert isinstance(result, VerificationResult)
        assert result.is_verified is False
        assert result.error_type == "integrity_error"
        assert "fabricated_title" in result.issues
        assert "suspicious_author" in result.issues
        # Should NOT call external APIs if integrity fails
        mock_openalex_client.verify_paper.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_citation_validator_proceeds_to_api_verification_when_integrity_passes(
        self, mock_openalex_client, mock_crossref_client,
        mock_integrity_checker, valid_citation
    ):
        """TEST (RED): CitationValidator should proceed to API verification when integrity passes."""
        from knowledge_storm.citation_verification.validator import CitationValidator
        
        # Arrange
        mock_integrity_checker.check_citation.return_value = []  # No issues
        mock_openalex_client.verify_paper.return_value = {
            'exists': True,
            'metadata_matches': True,
            'authors_match': True
        }
        
        validator = CitationValidator(
            openalex_client=mock_openalex_client,
            crossref_client=mock_crossref_client,
            integrity_checker=mock_integrity_checker
        )
        
        # Act
        result = await validator.verify_citation(valid_citation)
        
        # Assert
        mock_integrity_checker.check_citation.assert_called_once_with(valid_citation)
        mock_openalex_client.verify_paper.assert_called_once_with(valid_citation)
        assert result.is_verified is True
        assert result.confidence_score >= 0.7