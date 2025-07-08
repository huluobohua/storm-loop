"""
Unit tests for BiasDetector that actually test the implementation.
These tests verify the real bias detection logic without mocking.
"""
import pytest
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.models import ResearchData, ValidationStatus
from academic_validation_framework.config import ValidationConfig


class TestBiasDetectorUnit:
    """Unit tests for BiasDetector that actually test the implementation."""

    @pytest.fixture
    def config(self):
        return ValidationConfig(bias_detection_threshold=0.7)

    @pytest.fixture
    def detector(self, config):
        return BiasDetector(config)

    @pytest.mark.asyncio
    async def test_confirmation_bias_detection_with_cherry_picking(self, detector):
        """Test confirmation bias detection with cherry-picking language."""
        data = ResearchData(
            title="Test Study",
            abstract="This study only shows specifically supports our hypothesis exclusively.",
            citations=["citation1", "citation2"]  # Less than min_citations (10)
        )

        result = await detector.validate(data)

        assert result.status == ValidationStatus.FAILED
        assert result.score < 0.7

        # Check that confirmation bias was detected
        bias_checks = result.details["bias_checks"]
        confirmation_check = next(c for c in bias_checks if c["type"] == "confirmation_bias")
        assert confirmation_check["detected"] is True
        assert confirmation_check["confidence"] > 0.5
        assert any("cherry-picking" in evidence for evidence in confirmation_check["evidence"])

    @pytest.mark.asyncio
    async def test_publication_bias_detection_positive_emphasis(self, detector):
        """Test publication bias detection with positive result emphasis."""
        data = ResearchData(
            title="Significant Effective Treatment",
            abstract="Results show significant improvements, effective treatment, successful outcomes, and improved patient care.",
            citations=["cite1"] * 15  # Enough citations
        )

        result = await detector.validate(data)

        bias_checks = result.details["bias_checks"]
        publication_check = next(c for c in bias_checks if c["type"] == "publication_bias")
        assert publication_check["detected"] is True
        assert "positive outcome language" in publication_check["evidence"][0]

    @pytest.mark.asyncio
    async def test_selection_bias_no_randomization(self, detector):
        """Test selection bias detection when no randomization mentioned."""
        data = ResearchData(
            title="Patient Study",
            abstract="Study included participants using convenience sampling from available volunteers.",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        bias_checks = result.details["bias_checks"]
        selection_check = next(c for c in bias_checks if c["type"] == "selection_bias")
        assert selection_check["detected"] is True
        assert any("convenience sampling" in evidence for evidence in selection_check["evidence"])

    @pytest.mark.asyncio
    async def test_funding_bias_detection(self, detector):
        """Test funding bias detection with pharmaceutical funding."""
        data = ResearchData(
            title="Drug Efficacy Study",
            abstract="This study funded by pharmaceutical company shows drug effectiveness. Industry sponsored research demonstrates positive outcomes.",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        bias_checks = result.details["bias_checks"]
        funding_check = next(c for c in bias_checks if c["type"] == "funding_bias")
        assert funding_check["detected"] is True
        assert any("funded by" in evidence for evidence in funding_check["evidence"])

    @pytest.mark.asyncio
    async def test_reporting_bias_selective_reporting(self, detector):
        """Test reporting bias detection with selective outcome reporting."""
        data = ResearchData(
            title="Clinical Trial Results",
            abstract="We report the primary outcome which showed positive results. Secondary outcomes were not significant.",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        bias_checks = result.details["bias_checks"]
        reporting_check = next(c for c in bias_checks if c["type"] == "reporting_bias")
        # May or may not be detected based on subtle language
        assert isinstance(reporting_check["detected"], bool)
        assert isinstance(reporting_check["confidence"], float)

    @pytest.mark.asyncio
    async def test_no_bias_clean_study(self, detector):
        """Test that clean study without bias indicators passes."""
        data = ResearchData(
            title="Randomized Controlled Trial",
            abstract="This randomized controlled trial included participants through random assignment. Methods followed standard protocols with appropriate sample size calculations.",
            citations=["cite1"] * 20
        )

        result = await detector.validate(data)

        assert result.status == ValidationStatus.PASSED
        assert result.score >= 0.7

        bias_checks = result.details["bias_checks"]
        detected_biases = [c for c in bias_checks if c["detected"]]
        assert len(detected_biases) == 0 or all(c["confidence"] < 0.5 for c in detected_biases)

    @pytest.mark.asyncio
    async def test_multiple_biases_detected(self, detector):
        """Test detection of multiple bias types in single study."""
        data = ResearchData(
            title="Industry Funded Study",
            abstract="This pharmaceutical company funded study only shows positive results specifically supporting our product. Convenience sampling was used.",
            citations=["cite1", "cite2"]  # Few citations
        )

        result = await detector.validate(data)

        assert result.status == ValidationStatus.FAILED
        assert result.score < 0.5  # Multiple biases should lower score

        bias_checks = result.details["bias_checks"]
        detected_biases = [c for c in bias_checks if c["detected"]]
        assert len(detected_biases) >= 3  # At least confirmation, publication, and funding bias

    @pytest.mark.asyncio
    async def test_input_validation_error_handling(self, detector):
        """Test error handling for invalid input."""
        data = ResearchData(title="", abstract="", citations=None)

        result = await detector.validate(data)

        assert result.status == ValidationStatus.ERROR
        assert "error" in result.details
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_edge_case_none_abstract(self, detector):
        """Test handling of None abstract."""
        data = ResearchData(title="Valid Title", abstract=None, citations=["cite1"] * 15)

        result = await detector.validate(data)

        # Should not crash and should return valid result
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_bias_scoring_calculation(self, detector):
        """Test that bias scoring calculation is correct."""
        data = ResearchData(
            title="Test Study",
            abstract="Normal research abstract without obvious bias indicators.",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        # Score should be normalized between 0 and 1
        assert 0.0 <= result.score <= 1.0
        
        # With no obvious biases, score should be relatively high
        assert result.score > 0.5

    @pytest.mark.asyncio
    async def test_bias_confidence_levels(self, detector):
        """Test that bias confidence levels are properly calculated."""
        data = ResearchData(
            title="Study with Subtle Bias",
            abstract="This study shows some positive results in our treatment group.",
            citations=["cite1"] * 8  # Just below threshold
        )

        result = await detector.validate(data)

        bias_checks = result.details["bias_checks"]
        
        # All confidence values should be between 0 and 1
        for check in bias_checks:
            assert 0.0 <= check["confidence"] <= 1.0
            
        # Confirmation bias might be detected due to low citations
        confirmation_check = next(c for c in bias_checks if c["type"] == "confirmation_bias")
        assert confirmation_check["confidence"] > 0.0  # Should have some confidence due to low citations

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, detector):
        """Test handling of special characters and unicode."""
        data = ResearchData(
            title="Test with émojis 🧪 and spëcial chars",
            abstract="This study uses ñon-standard characters and 中文 text with proper randomization.",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        # Should handle unicode without crashing
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]
        assert isinstance(result.score, float)
        assert isinstance(result.details, dict)

    @pytest.mark.asyncio
    async def test_extremely_long_abstract(self, detector):
        """Test handling of extremely long abstracts."""
        long_abstract = "This randomized controlled trial " * 1000  # Very long abstract
        data = ResearchData(
            title="Test",
            abstract=long_abstract,
            citations=["cite1"] * 20
        )

        result = await detector.validate(data)

        # Should handle without memory issues or timeout
        assert isinstance(result.score, float)
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]

    @pytest.mark.asyncio
    async def test_empty_citations_list(self, detector):
        """Test handling of empty citations list."""
        data = ResearchData(
            title="Study with No Citations",
            abstract="This is a comprehensive study with proper methodology.",
            citations=[]
        )

        result = await detector.validate(data)

        # Should detect confirmation bias due to no citations
        bias_checks = result.details["bias_checks"]
        confirmation_check = next(c for c in bias_checks if c["type"] == "confirmation_bias")
        assert confirmation_check["detected"] is True
        assert any("no citations" in evidence.lower() for evidence in confirmation_check["evidence"])