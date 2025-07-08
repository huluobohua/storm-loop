"""
Comprehensive edge case tests for validators.
"""
import pytest
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.models import ResearchData, ValidationStatus
from academic_validation_framework.config import ValidationConfig


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def config(self):
        return ValidationConfig()

    @pytest.mark.asyncio
    async def test_empty_data(self, config):
        """Test handling of completely empty data."""
        detector = BiasDetector(config)
        data = ResearchData(title="", abstract="", citations=[])

        result = await detector.validate(data)

        assert result.status == ValidationStatus.ERROR
        assert "error" in result.details

    @pytest.mark.asyncio
    async def test_none_values(self, config):
        """Test handling of None values."""
        detector = BiasDetector(config)
        data = ResearchData(title=None, abstract=None, citations=None)

        result = await detector.validate(data)

        # Should handle gracefully without crashing
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED, ValidationStatus.ERROR]

    @pytest.mark.asyncio
    async def test_extremely_long_abstract(self, config):
        """Test handling of extremely long abstracts."""
        detector = BiasDetector(config)
        long_abstract = "word " * 100000  # 100k words
        data = ResearchData(title="Test", abstract=long_abstract, citations=["cite1"])

        result = await detector.validate(data)

        # Should handle without memory issues
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_special_characters_in_text(self, config):
        """Test handling of special characters and unicode."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Test with émojis 🧪 and spëcial chars",
            abstract="This study uses ñon-standard characters and 中文 text",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        # Should handle unicode without crashing
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]

    @pytest.mark.asyncio
    async def test_very_few_citations(self, config):
        """Test handling of very few citations."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Test Study",
            abstract="This is a test study with minimal citations",
            citations=["only one citation"]
        )

        result = await detector.validate(data)

        # Should detect confirmation bias due to few citations
        bias_checks = result.details["bias_checks"]
        confirmation_check = next(c for c in bias_checks if c["type"] == "confirmation_bias")
        assert confirmation_check["detected"] is True

    @pytest.mark.asyncio
    async def test_prisma_validator_edge_cases(self, config):
        """Test PRISMA validator edge cases."""
        validator = EnhancedPRISMAValidator(config)

        # Test with minimal data
        data = ResearchData(title="A", abstract="B", citations=[])
        result = await validator.validate(data)

        assert result.status == ValidationStatus.FAILED
        assert result.score < 0.5

        # Test with None values
        data = ResearchData(title=None, abstract=None, citations=None)
        result = await validator.validate(data)

        assert result.status in [ValidationStatus.FAILED, ValidationStatus.ERROR]

    @pytest.mark.asyncio
    async def test_malformed_citations(self, config):
        """Test handling of malformed citations."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Test Study",
            abstract="Normal abstract text",
            citations=[None, "", "valid citation", 123, {"invalid": "citation"}]  # Mixed types
        )

        result = await detector.validate(data)

        # Should handle mixed citation types gracefully
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED, ValidationStatus.ERROR]

    @pytest.mark.asyncio
    async def test_html_in_abstract(self, config):
        """Test handling of HTML tags in abstract."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Test Study",
            abstract="<p>This study shows <b>significant</b> results with <i>p < 0.05</i></p>",
            citations=["cite1"] * 10
        )

        result = await detector.validate(data)

        # Should process HTML content appropriately
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_repeated_keywords(self, config):
        """Test handling of repeated keywords."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Significant Significant Significant Study",
            abstract="Significant significant SIGNIFICANT results significant findings significant outcomes",
            citations=["cite1"] * 10
        )

        result = await detector.validate(data)

        # Should detect publication bias from repeated positive terms
        bias_checks = result.details["bias_checks"]
        publication_check = next(c for c in bias_checks if c["type"] == "publication_bias")
        assert publication_check["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_mixed_language_abstract(self, config):
        """Test handling of mixed language abstracts."""
        validator = EnhancedPRISMAValidator(config)
        data = ResearchData(
            title="Systematic Review / Revue Systématique",
            abstract="This systematic review was registered in PROSPERO. Cette revue systématique a été enregistrée dans PROSPERO.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        # Should detect PROSPERO registration despite mixed language
        checkpoints = result.details["prisma_checkpoints"]
        protocol_check = next(c for c in checkpoints if c["name"] == "protocol_registration")
        assert protocol_check["passed"] is True

    @pytest.mark.asyncio
    async def test_numerical_data_in_abstract(self, config):
        """Test handling of numerical data."""
        detector = BiasDetector(config)
        data = ResearchData(
            title="Statistical Analysis",
            abstract="Results: 95% CI [1.2-3.4], p=0.001, n=1000, effect size d=0.8",
            citations=["cite1"] * 15
        )

        result = await detector.validate(data)

        # Should handle numerical data without issues
        assert isinstance(result.score, float)
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]

    @pytest.mark.asyncio
    async def test_abstract_with_line_breaks(self, config):
        """Test handling of abstracts with line breaks."""
        validator = EnhancedPRISMAValidator(config)
        data = ResearchData(
            title="Systematic Review",
            abstract="""Background: This is a systematic review.
            
            Methods: We searched PubMed and Embase.
            
            Results: Found 50 studies.
            
            Conclusion: Evidence supports intervention.""",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        # Should detect search strategy across line breaks
        checkpoints = result.details["prisma_checkpoints"]
        search_check = next(c for c in checkpoints if c["name"] == "search_strategy")
        assert search_check["passed"] is True

    @pytest.mark.asyncio
    async def test_concurrent_validation_safety(self, config):
        """Test that validators are safe for concurrent use."""
        detector = BiasDetector(config)
        data1 = ResearchData(title="Study 1", abstract="Abstract 1", citations=["cite1"])
        data2 = ResearchData(title="Study 2", abstract="Abstract 2", citations=["cite2"])

        # Run validations concurrently
        import asyncio
        results = await asyncio.gather(
            detector.validate(data1),
            detector.validate(data2)
        )

        # Both should complete successfully
        assert len(results) == 2
        assert all(hasattr(r, 'status') for r in results)

    @pytest.mark.asyncio
    async def test_boundary_citation_counts(self, config):
        """Test boundary conditions for citation counts."""
        detector = BiasDetector(config)
        
        # Exactly at threshold (assuming 10 is threshold)
        data = ResearchData(
            title="Boundary Test",
            abstract="Standard abstract",
            citations=["cite"] * 10
        )
        result = await detector.validate(data)
        assert isinstance(result.score, float)
        
        # Just below threshold
        data.citations = ["cite"] * 9
        result = await detector.validate(data)
        bias_checks = result.details["bias_checks"]
        confirmation_check = next(c for c in bias_checks if c["type"] == "confirmation_bias")
        assert confirmation_check["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_validator_config_boundaries(self, config):
        """Test validators with extreme config values."""
        # Test with very high threshold
        high_threshold_config = ValidationConfig(bias_detection_threshold=0.99)
        detector = BiasDetector(high_threshold_config)
        
        data = ResearchData(
            title="Normal Study",
            abstract="This study shows some positive results.",
            citations=["cite"] * 20
        )
        
        result = await detector.validate(data)
        # With very high threshold, most studies should pass
        assert result.status == ValidationStatus.PASSED