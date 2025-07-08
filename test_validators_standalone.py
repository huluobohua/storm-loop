"""
Standalone test for enhanced validators to verify CI readiness.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.models import ResearchData
from academic_validation_framework.config import ValidationConfig


async def test_all_validators():
    """Test all validators to ensure they work."""
    config = ValidationConfig()
    
    # Test data
    good_data = ResearchData(
        title="Comprehensive Systematic Review Following PRISMA Guidelines",
        abstract="""
        This systematic review was registered in PROSPERO (CRD42024001234).
        We searched PubMed, Embase, and Cochrane databases. Risk of bias was
        assessed using the Cochrane RoB tool. Meta-analysis was performed using
        random-effects models. Publication bias was evaluated with funnel plots.
        """,
        citations=[f"Author{i} et al. (2024)" for i in range(30)]
    )
    
    bad_data = ResearchData(
        title="A Biased Study",
        abstract="Only positive results shown. Sponsored by industry. Selected participants.",
        citations=[]
    )
    
    print("Testing Enhanced PRISMA Validator...")
    prisma = EnhancedPRISMAValidator(config)
    
    good_result = await prisma.validate(good_data)
    print(f"✓ Good data score: {good_result.score:.2f} ({good_result.status.name})")
    
    bad_result = await prisma.validate(bad_data)
    print(f"✓ Bad data score: {bad_result.score:.2f} ({bad_result.status.name})")
    
    print("\nTesting Bias Detector...")
    bias_detector = BiasDetector(config)
    
    good_bias = await bias_detector.validate(good_data)
    print(f"✓ Good data bias score: {good_bias.score:.2f} ({good_bias.status.name})")
    
    bad_bias = await bias_detector.validate(bad_data)
    print(f"✓ Bad data bias score: {bad_bias.score:.2f} ({bad_bias.status.name})")
    
    # Check if validators properly differentiate between good and bad data
    assert good_result.score > bad_result.score, "PRISMA validator should score good data higher"
    assert good_bias.score > bad_bias.score, "Bias detector should score good data higher"
    
    print("\n✅ All validators working correctly!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_all_validators())
    sys.exit(0 if success else 1)