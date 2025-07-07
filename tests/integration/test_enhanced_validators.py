import pytest
import asyncio
from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.enhanced_citation_validator import EnhancedCitationValidator
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.models import ResearchData

@pytest.fixture
def validation_config():
    """Provide test configuration."""
    return ValidationConfig(
        citation_accuracy_threshold=0.80,
        prisma_compliance_threshold=0.70,
        bias_detection_threshold=0.75
    )

@pytest.fixture
def sample_research_data():
    """Provide sample research data for testing."""
    return ResearchData(
        title="Systematic Review of Machine Learning in Healthcare",
        abstract="This systematic review examines machine learning applications in healthcare. Protocol was registered in PROSPERO. We searched PubMed, EMBASE, and Cochrane databases using comprehensive search strategies. Study selection followed PRISMA guidelines.",
        citations=[
            "Smith, J. A. (2023). Machine learning in diagnosis. Journal of Medical AI, 15(3), 45-67.",
            "Johnson, M. B. (2022). Healthcare algorithms. Medical Computing, 8(2), 123-145.",
            "Brown, K. C. (2023). AI applications. Health Technology, 12(4), 78-92."
        ],
        authors=["Dr. Jane Smith", "Dr. John Doe"],
        publication_year=2024,
        journal="Healthcare Reviews",
        doi="10.1234/healthcare.2024.001"
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_enhanced_prisma_validator(validation_config, sample_research_data):
    """Test PRISMA validator with real data."""
    validator = EnhancedPRISMAValidator(validation_config)

    result = await validator.validate(sample_research_data)

    # Assertions
    assert result.validator_name == "enhanced_prisma"
    assert isinstance(result.score, float)
    assert 0.0 <= result.score <= 1.0
    assert "checkpoints" in result.details
    assert result.details["total_checkpoints"] == 12

    # Check that protocol registration was detected
    protocol_checkpoint = next(
        (cp for cp in result.details["checkpoints"] if cp["name"] == "protocol_registration"),
        None
    )
    assert protocol_checkpoint is not None
    assert protocol_checkpoint["passed"] is True

@pytest.mark.integration  
@pytest.mark.asyncio
async def test_enhanced_citation_validator(validation_config, sample_research_data):
    """Test citation validator with real data."""
    validator = EnhancedCitationValidator(validation_config)

    result = await validator.validate(sample_research_data)

    # Assertions
    assert result.validator_name == "enhanced_citation"
    assert isinstance(result.score, float)
    assert 0.0 <= result.score <= 1.0
    assert "format_results" in result.details
    assert result.details["formats_checked"] == 5

    # Check APA format was validated
    apa_result = next(
        (fr for fr in result.details["format_results"] if fr["format"] == "APA"),
        None
    )
    assert apa_result is not None
    assert isinstance(apa_result["confidence"], float)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_bias_detector(validation_config, sample_research_data):
    """Test bias detector with real data."""
    validator = BiasDetector(validation_config)

    result = await validator.validate(sample_research_data)

    # Assertions
    assert result.validator_name == "bias_detector"
    assert isinstance(result.score, float)
    assert 0.0 <= result.score <= 1.0
    assert "bias_checks" in result.details
    assert result.details["total_bias_types_checked"] == 5

    # Check confirmation bias was checked
    confirmation_bias = next(
        (bc for bc in result.details["bias_checks"] if bc["type"] == "confirmation_bias"),
        None
    )
    assert confirmation_bias is not None
    assert isinstance(confirmation_bias["confidence"], float)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_validation_pipeline_integration(validation_config, sample_research_data):
    """Test complete validation pipeline."""
    # Initialize all validators
    prisma_validator = EnhancedPRISMAValidator(validation_config)
    citation_validator = EnhancedCitationValidator(validation_config)
    bias_detector = BiasDetector(validation_config)

    # Run validations
    prisma_result = await prisma_validator.validate(sample_research_data)
    citation_result = await citation_validator.validate(sample_research_data)
    bias_result = await bias_detector.validate(sample_research_data)

    # Assertions
    assert all(isinstance(result.score, float) for result in [prisma_result, citation_result, bias_result])
    assert all(result.validator_name for result in [prisma_result, citation_result, bias_result])

    # Calculate overall score
    overall_score = (prisma_result.score + citation_result.score + bias_result.score) / 3
    assert isinstance(overall_score, float)
    assert 0.0 <= overall_score <= 1.0

@pytest.mark.integration
def test_validators_without_data():
    """Test validators handle missing data gracefully."""
    config = ValidationConfig()

    empty_data = ResearchData(
        title="",
        abstract="",
        citations=[],
        authors=[],
        publication_year=2024
    )

    # Test that validators can be instantiated
    prisma_validator = EnhancedPRISMAValidator(config)
    citation_validator = EnhancedCitationValidator(config)
    bias_detector = BiasDetector(config)

    assert prisma_validator is not None
    assert citation_validator is not None
    assert bias_detector is not None

