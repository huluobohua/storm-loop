"""
Test suite for enhanced validators - CI/CD compatible.
"""
import pytest
import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.strategies.apa_strategy import APACitationStrategy
from academic_validation_framework.models import ResearchData, Citation
from academic_validation_framework.config import ValidationConfig


@pytest.mark.academic_validation
@pytest.mark.asyncio
async def test_enhanced_prisma_validator():
    """Test enhanced PRISMA compliance validator."""
    config = ValidationConfig()
    validator = EnhancedPRISMAValidator(config)
    
    # High-quality systematic review data
    data = ResearchData(
        title="Comprehensive Systematic Review and Meta-Analysis of Treatment Efficacy",
        abstract="""
        Background: This systematic review followed PRISMA guidelines and was registered in PROSPERO (CRD42024001234).
        
        Methods: We systematically searched PubMed, Embase, Cochrane Library, and Web of Science databases from inception
        to January 2024. Eligibility criteria included randomized controlled trials comparing treatment X with placebo.
        Two independent reviewers screened articles, extracted data, and assessed risk of bias using the Cochrane RoB tool.
        
        Results: From 1,234 identified records, 45 studies (n=12,567 participants) met inclusion criteria. 
        Meta-analysis using random-effects models showed a significant treatment effect (OR: 2.34, 95% CI: 1.89-2.91).
        Heterogeneity was moderate (I²=45%). Publication bias was assessed using funnel plots and Egger's test (p=0.12).
        
        Conclusions: This systematic review provides high-quality evidence supporting treatment efficacy. 
        The certainty of evidence was rated as high using GRADE criteria.
        
        Registration: PROSPERO CRD42024001234
        """,
        citations=[Citation(text=f"Author{i} et al. (2024)") for i in range(1, 46)]
    )
    
    result = await validator.validate(data)
    
    assert result.status.name == "PASSED"
    assert result.score >= 0.9
    assert result.details["checkpoints_passed"] >= 10
    
    # Poor methodology paper
    poor_data = ResearchData(
        title="A Study on Treatment Effects",
        abstract="We looked at some patients and found that the treatment worked better than placebo.",
        citations=[]
    )
    
    poor_result = await validator.validate(poor_data)
    assert poor_result.status.name == "FAILED"
    assert poor_result.score < 0.5


@pytest.mark.academic_validation
@pytest.mark.asyncio
async def test_bias_detector():
    """Test comprehensive bias detection."""
    config = ValidationConfig()
    detector = BiasDetector(config)
    
    # Data with multiple bias indicators
    biased_data = ResearchData(
        title="Industry-Sponsored Study Shows Amazing Results",
        abstract="""
        This study was sponsored by XYZ Pharmaceutical Company. We exclusively selected participants
        who showed positive early response. Only significant positive results are reported here.
        The treatment showed breakthrough efficacy with no side effects mentioned.
        """,
        citations=[Citation(text="Industry Author et al. (2024)")]
    )
    
    result = await detector.validate(biased_data)
    
    assert result.status.name == "FAILED"
    assert result.score < 0.6
    
    bias_details = result.details["bias_checks"]
    detected_biases = [b for b in bias_details if b["detected"]]
    assert len(detected_biases) >= 3  # Should detect multiple biases


@pytest.mark.academic_validation
@pytest.mark.asyncio
async def test_apa_citation_strategy():
    """Test APA citation format validation."""
    strategy = APACitationStrategy()
    
    # Valid APA citation
    valid_citation = Citation(
        text="Smith, J. D., & Johnson, K. L. (2024). Understanding citation formats. Journal of Academic Writing, 15(3), 234-256. https://doi.org/10.1234/jaw.2024.15.3.234"
    )
    
    result = await strategy.validate_citation(valid_citation)
    assert result.is_valid
    assert result.confidence >= 0.9
    
    # Invalid APA citation
    invalid_citation = Citation(
        text="John Smith wrote about citations in 2024"
    )
    
    invalid_result = await strategy.validate_citation(invalid_citation)
    assert not invalid_result.is_valid
    assert len(invalid_result.errors) > 0


@pytest.mark.quick
def test_basic_imports():
    """Quick test to ensure all modules can be imported."""
    from academic_validation_framework import __version__
    from academic_validation_framework.validators import enhanced_prisma_validator
    from academic_validation_framework.validators import bias_detector
    from academic_validation_framework.strategies import apa_strategy
    
    assert __version__ is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validator_integration():
    """Test integration between validators."""
    config = ValidationConfig()
    prisma_validator = EnhancedPRISMAValidator(config)
    bias_detector_instance = BiasDetector(config)
    
    # Create test data
    data = ResearchData(
        title="Systematic Review of Treatment Options",
        abstract="A comprehensive review following PRISMA guidelines with PROSPERO registration.",
        citations=[Citation(text=f"Author{i} et al. (2024)") for i in range(20)]
    )
    
    # Run both validators
    prisma_result = await prisma_validator.validate(data)
    bias_result = await bias_detector_instance.validate(data)
    
    # Calculate combined score
    combined_score = (prisma_result.score + bias_result.score) / 2
    
    assert combined_score > 0.5
    assert prisma_result.validator_name == "enhanced_prisma_validator"
    assert bias_result.validator_name == "bias_detector"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])