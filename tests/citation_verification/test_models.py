"""
Test-Driven Development for Citation Verification Models

Tests the core data models used in citation verification.
Written before implementation to specify exact behavior.
"""

import pytest
from datetime import datetime
from typing import List

from knowledge_storm.citation_verification.models import (
    Citation, VerificationResult, ValidationReport
)


class TestCitation:
    """Test suite for Citation model."""
    
    def test_citation_creation_with_required_fields(self):
        """Test creating citation with minimum required fields."""
        # Act
        citation = Citation(
            title="Test Paper",
            authors=["Smith, J."],
            journal="Test Journal",
            year=2023
        )
        
        # Assert
        assert citation.title == "Test Paper"
        assert citation.authors == ["Smith, J."]
        assert citation.journal == "Test Journal"
        assert citation.year == 2023
        assert citation.doi is None
        assert citation.volume is None
        assert citation.pages is None
    
    def test_citation_creation_with_all_fields(self):
        """Test creating citation with all available fields."""
        # Act
        citation = Citation(
            title="Complete Test Paper",
            authors=["Smith, J.", "Doe, A."],
            journal="Complete Test Journal",
            year=2023,
            volume="42",
            pages="123-145",
            doi="10.1000/test.doi.123",
            url="https://example.com/paper"
        )
        
        # Assert
        assert citation.title == "Complete Test Paper"
        assert citation.authors == ["Smith, J.", "Doe, A."]
        assert citation.journal == "Complete Test Journal"
        assert citation.year == 2023
        assert citation.volume == "42"
        assert citation.pages == "123-145"
        assert citation.doi == "10.1000/test.doi.123"
        assert citation.url == "https://example.com/paper"
    
    def test_citation_validation_rejects_empty_title(self):
        """Test that empty title raises validation error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Citation(
                title="",
                authors=["Smith, J."],
                journal="Test Journal", 
                year=2023
            )
    
    def test_citation_validation_rejects_empty_authors(self):
        """Test that empty authors list raises validation error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Authors cannot be empty"):
            Citation(
                title="Test Paper",
                authors=[],
                journal="Test Journal",
                year=2023
            )
    
    def test_citation_validation_rejects_future_year(self):
        """Test that future publication years are rejected."""
        # Arrange
        future_year = datetime.now().year + 1
        
        # Act & Assert
        with pytest.raises(ValueError, match="Publication year cannot be in the future"):
            Citation(
                title="Test Paper",
                authors=["Smith, J."],
                journal="Test Journal",
                year=future_year
            )
    
    def test_citation_validation_rejects_invalid_year(self):
        """Test that unrealistic publication years are rejected."""
        # Act & Assert
        with pytest.raises(ValueError, match="Publication year must be reasonable"):
            Citation(
                title="Test Paper", 
                authors=["Smith, J."],
                journal="Test Journal",
                year=1800  # Too old for modern academic papers
            )
    
    def test_citation_equality_comparison(self):
        """Test citation equality based on core fields."""
        # Arrange
        citation1 = Citation(
            title="Same Paper",
            authors=["Smith, J."],
            journal="Same Journal",
            year=2023
        )
        citation2 = Citation(
            title="Same Paper",
            authors=["Smith, J."],
            journal="Same Journal", 
            year=2023
        )
        citation3 = Citation(
            title="Different Paper",
            authors=["Smith, J."],
            journal="Same Journal",
            year=2023
        )
        
        # Act & Assert
        assert citation1 == citation2
        assert citation1 != citation3
    
    def test_citation_hash_consistency(self):
        """Test that citation hashing is consistent for equal citations."""
        # Arrange
        citation1 = Citation(
            title="Test Paper",
            authors=["Smith, J."],
            journal="Test Journal",
            year=2023
        )
        citation2 = Citation(
            title="Test Paper", 
            authors=["Smith, J."],
            journal="Test Journal",
            year=2023
        )
        
        # Act & Assert
        assert hash(citation1) == hash(citation2)
    
    def test_citation_string_representation(self):
        """Test citation string representation for debugging."""
        # Arrange
        citation = Citation(
            title="Test Paper",
            authors=["Smith, J.", "Doe, A."],
            journal="Test Journal",
            year=2023
        )
        
        # Act
        str_repr = str(citation)
        
        # Assert
        assert "Test Paper" in str_repr
        assert "Smith, J." in str_repr
        assert "Test Journal" in str_repr
        assert "2023" in str_repr


class TestVerificationResult:
    """Test suite for VerificationResult model."""
    
    def test_verification_result_creation_verified(self):
        """Test creating verified result."""
        # Act
        result = VerificationResult(
            is_verified=True,
            confidence_score=0.95,
            verification_source="openalex",
            issues=[]
        )
        
        # Assert
        assert result.is_verified is True
        assert result.confidence_score == 0.95
        assert result.verification_source == "openalex"
        assert result.issues == []
        assert result.error_type is None
    
    def test_verification_result_creation_failed(self):
        """Test creating failed verification result."""
        # Act
        result = VerificationResult(
            is_verified=False,
            confidence_score=0.1,
            verification_source="crossref",
            issues=["fabricated", "invalid_doi"],
            error_type="validation_failed"
        )
        
        # Assert
        assert result.is_verified is False
        assert result.confidence_score == 0.1
        assert result.verification_source == "crossref"
        assert "fabricated" in result.issues
        assert "invalid_doi" in result.issues
        assert result.error_type == "validation_failed"
    
    def test_verification_result_confidence_score_validation(self):
        """Test confidence score must be between 0 and 1."""
        # Act & Assert
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            VerificationResult(
                is_verified=True,
                confidence_score=1.5,  # Invalid score > 1
                verification_source="openalex",
                issues=[]
            )
        
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            VerificationResult(
                is_verified=False,
                confidence_score=-0.1,  # Invalid score < 0
                verification_source="openalex",
                issues=[]
            )
    
    def test_verification_result_source_validation(self):
        """Test verification source must be valid."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid verification source"):
            VerificationResult(
                is_verified=True,
                confidence_score=0.9,
                verification_source="invalid_source",
                issues=[]
            )


class TestValidationReport:
    """Test suite for ValidationReport model."""
    
    def test_validation_report_creation(self):
        """Test creating validation report."""
        # Arrange
        results = [
            VerificationResult(True, 0.95, "openalex", []),
            VerificationResult(False, 0.1, "crossref", ["fabricated"])
        ]
        
        # Act
        report = ValidationReport(
            total_citations=2,
            verified_count=1,
            fabricated_count=1,
            verification_results=results
        )
        
        # Assert
        assert report.total_citations == 2
        assert report.verified_count == 1
        assert report.fabricated_count == 1
        assert len(report.verification_results) == 2
        assert isinstance(report.generated_at, datetime)
    
    def test_validation_report_consistency_validation(self):
        """Test that report counts are consistent with results."""
        # Arrange
        results = [
            VerificationResult(True, 0.95, "openalex", [])
        ]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Verification counts inconsistent"):
            ValidationReport(
                total_citations=2,  # Inconsistent with results length
                verified_count=1,
                fabricated_count=0,
                verification_results=results
            )
    
    def test_validation_report_summary_statistics(self):
        """Test validation report summary calculations."""
        # Arrange
        results = [
            VerificationResult(True, 0.95, "openalex", []),
            VerificationResult(True, 0.88, "crossref", []),
            VerificationResult(False, 0.1, "openalex", ["fabricated"]),
            VerificationResult(False, 0.2, "crossref", ["invalid_doi"])
        ]
        
        # Act
        report = ValidationReport(
            total_citations=4,
            verified_count=2,
            fabricated_count=2,
            verification_results=results
        )
        
        # Assert
        assert report.verification_rate == 0.5  # 2/4 = 0.5
        assert report.average_confidence >= 0.0
        assert report.average_confidence <= 1.0
    
    def test_validation_report_with_empty_results(self):
        """Test validation report with no citations."""
        # Act
        report = ValidationReport(
            total_citations=0,
            verified_count=0,
            fabricated_count=0,
            verification_results=[]
        )
        
        # Assert
        assert report.total_citations == 0
        assert report.verified_count == 0
        assert report.fabricated_count == 0
        assert report.verification_rate == 0.0
        assert report.average_confidence == 0.0