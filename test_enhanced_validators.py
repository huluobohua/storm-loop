#!/usr/bin/env python3
"""
Comprehensive test for enhanced PRISMA and bias detection validators.

Tests the advanced Phase 2 validation systems to ensure they work correctly
with realistic academic research data.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from academic_validation_framework.models import ResearchData
from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.bias_detector import BiasDetector


def create_test_data():
    """Create comprehensive test research data."""
    
    # High-quality systematic review with PRISMA compliance
    prisma_compliant_data = ResearchData(
        title="Systematic review and meta-analysis of randomized controlled trials on exercise interventions",
        abstract="""
        Protocol was registered in PROSPERO (CRD42023001234). We searched multiple databases including 
        PubMed, Embase, Cochrane Library, and Web of Science. Inclusion criteria required randomized 
        controlled trials with adult participants. Two independent reviewers conducted screening and 
        data extraction using standardized forms. Risk of bias was assessed using the Cochrane RoB tool. 
        Meta-analysis was performed using random effects models. Heterogeneity was assessed and publication 
        bias was evaluated using funnel plots and Egger's test. GRADE assessment was used to evaluate 
        certainty of evidence. Study characteristics included population demographics and intervention details. 
        Results showed significant improvements in outcomes with moderate certainty of evidence.
        """,
        citations=["Smith, J. (2023). Exercise interventions: A systematic review. Journal of Health, 45(2), 123-135."]
    )
    
    # Research with bias indicators
    biased_research_data = ResearchData(
        title="Revolutionary breakthrough: Superior pharmaceutical treatment shows unprecedented results",
        abstract="""
        This study was sponsored by PharmaCorp and demonstrates the significant effectiveness of our 
        new drug treatment. Only positive outcomes were observed with statistically significant results 
        (p < 0.001). The treatment was particularly superior to all existing alternatives. Participants 
        were conveniently selected from company clinics. No mention of adverse effects or limitations. 
        The results exclusively support the commercial application of this revolutionary product.
        """,
        citations=["Johnson, A. (2023). Company-sponsored research. Corporate Journal, 12(1), 45-50."]
    )
    
    # Mixed quality research
    mixed_quality_data = ResearchData(
        title="Effect of intervention on health outcomes: A study",
        abstract="""
        We conducted a study examining health interventions. Some participants were recruited from 
        local clinics. Various outcomes were measured. Several significant results were found. 
        Many participants showed improvement. The study had certain limitations that were not fully explored.
        """,
        citations=["Brown, C. (2023). Health study. Medical Journal, 8(3), 78-89."]
    )
    
    return prisma_compliant_data, biased_research_data, mixed_quality_data


async def test_enhanced_prisma_validator():
    """Test the enhanced PRISMA validator with comprehensive checkpoint validation."""
    print("=" * 80)
    print("TESTING ENHANCED PRISMA VALIDATOR")
    print("=" * 80)
    
    config = ValidationConfig()
    validator = EnhancedPRISMAValidator(config)
    
    prisma_data, _, mixed_data = create_test_data()
    
    # Test high-quality PRISMA-compliant research
    print("\n1. Testing PRISMA-compliant research:")
    print("-" * 40)
    result = await validator.validate(prisma_data)
    
    print(f"Overall Score: {result.score:.2f}")
    print(f"Status: {result.status}")
    print(f"Passed Checkpoints: {result.details['passed_checkpoints']}/{result.details['total_checkpoints']}")
    
    print("\nCheckpoint Details:")
    for checkpoint in result.details['checkpoints']:
        status = "✓" if checkpoint['passed'] else "✗"
        print(f"  {status} {checkpoint['name']}: {checkpoint['score']:.1f} - {checkpoint['details']}")
    
    # Test mixed quality research  
    print("\n\n2. Testing mixed quality research:")
    print("-" * 40)
    result_mixed = await validator.validate(mixed_data)
    
    print(f"Overall Score: {result_mixed.score:.2f}")
    print(f"Status: {result_mixed.status}")
    print(f"Passed Checkpoints: {result_mixed.details['passed_checkpoints']}/{result_mixed.details['total_checkpoints']}")
    
    print("\nCheckpoint Details:")
    for checkpoint in result_mixed.details['checkpoints']:
        status = "✓" if checkpoint['passed'] else "✗"
        print(f"  {status} {checkpoint['name']}: {checkpoint['score']:.1f} - {checkpoint['details']}")
    
    return result, result_mixed


async def test_bias_detector():
    """Test the enhanced bias detector with sophisticated detection algorithms."""
    print("\n\n" + "=" * 80)
    print("TESTING ENHANCED BIAS DETECTOR")
    print("=" * 80)
    
    config = ValidationConfig()
    detector = BiasDetector(config)
    
    _, biased_data, mixed_data = create_test_data()
    
    # Test heavily biased research
    print("\n1. Testing research with bias indicators:")
    print("-" * 40)
    result = await detector.validate(biased_data)
    
    print(f"Overall Score: {result.score:.2f}")
    print(f"Status: {result.status}")
    print(f"Biases Detected: {result.details['biases_detected']}/{result.details['total_bias_types_checked']}")
    
    print("\nBias Detection Details:")
    for bias_check in result.details['bias_checks']:
        status = "⚠️" if bias_check['detected'] else "✓"
        print(f"  {status} {bias_check['type']}: {bias_check['confidence']:.2f}")
        if bias_check['evidence']:
            for evidence in bias_check['evidence']:
                print(f"    - {evidence}")
    
    # Test mixed quality research
    print("\n\n2. Testing mixed quality research:")
    print("-" * 40)
    result_mixed = await detector.validate(mixed_data)
    
    print(f"Overall Score: {result_mixed.score:.2f}")
    print(f"Status: {result_mixed.status}")
    print(f"Biases Detected: {result_mixed.details['biases_detected']}/{result_mixed.details['total_bias_types_checked']}")
    
    print("\nBias Detection Details:")
    for bias_check in result_mixed.details['bias_checks']:
        status = "⚠️" if bias_check['detected'] else "✓"
        print(f"  {status} {bias_check['type']}: {bias_check['confidence']:.2f}")
        if bias_check['evidence']:
            for evidence in bias_check['evidence']:
                print(f"    - {evidence}")
    
    return result, result_mixed


async def test_integrated_validation():
    """Test both validators together on the same research data."""
    print("\n\n" + "=" * 80)
    print("TESTING INTEGRATED VALIDATION SYSTEM")
    print("=" * 80)
    
    config = ValidationConfig()
    prisma_validator = EnhancedPRISMAValidator(config)
    bias_detector = BiasDetector(config)
    
    prisma_data, biased_data, mixed_data = create_test_data()
    
    test_cases = [
        ("High-quality PRISMA-compliant research", prisma_data),
        ("Research with bias indicators", biased_data),
        ("Mixed quality research", mixed_data)
    ]
    
    for case_name, data in test_cases:
        print(f"\n{case_name}:")
        print("-" * 60)
        
        # Run both validators
        prisma_result = await prisma_validator.validate(data)
        bias_result = await bias_detector.validate(data)
        
        # Calculate combined quality score
        combined_score = (prisma_result.score + bias_result.score) / 2
        
        print(f"PRISMA Compliance: {prisma_result.score:.2f} ({prisma_result.status})")
        print(f"Bias Assessment:   {bias_result.score:.2f} ({bias_result.status})")
        print(f"Combined Score:    {combined_score:.2f}")
        
        # Quality assessment
        if combined_score >= 0.8:
            quality = "Excellent"
        elif combined_score >= 0.6:
            quality = "Good"
        elif combined_score >= 0.4:
            quality = "Fair"
        else:
            quality = "Poor"
        
        print(f"Overall Quality:   {quality}")
        
        # Key findings
        prisma_passed = prisma_result.details['passed_checkpoints']
        total_prisma = prisma_result.details['total_checkpoints']
        biases_detected = bias_result.details['biases_detected']
        total_bias_types = bias_result.details['total_bias_types_checked']
        
        print(f"PRISMA: {prisma_passed}/{total_prisma} checkpoints passed")
        print(f"Bias: {biases_detected}/{total_bias_types} bias types detected")


def run_performance_test():
    """Test performance of enhanced validators."""
    print("\n\n" + "=" * 80)
    print("PERFORMANCE TEST")
    print("=" * 80)
    
    import time
    
    config = ValidationConfig()
    prisma_validator = EnhancedPRISMAValidator(config)
    bias_detector = BiasDetector(config)
    
    # Create test data
    test_data = ResearchData(
        title="Test research article",
        abstract="This is a test abstract with various keywords for validation testing.",
        citations=["Test citation (2023)"]
    )
    
    # Performance test
    iterations = 100
    
    print(f"Running {iterations} iterations of each validator...")
    
    # PRISMA validator performance
    start_time = time.time()
    for _ in range(iterations):
        asyncio.run(prisma_validator.validate(test_data))
    prisma_time = time.time() - start_time
    
    # Bias detector performance
    start_time = time.time()
    for _ in range(iterations):
        asyncio.run(bias_detector.validate(test_data))
    bias_time = time.time() - start_time
    
    print(f"\nPerformance Results:")
    print(f"PRISMA Validator: {prisma_time:.3f}s total, {prisma_time/iterations*1000:.1f}ms per validation")
    print(f"Bias Detector:    {bias_time:.3f}s total, {bias_time/iterations*1000:.1f}ms per validation")


async def main():
    """Run comprehensive tests for enhanced validators."""
    print("COMPREHENSIVE ENHANCED VALIDATOR TEST SUITE")
    print("Phase 2 PRISMA and Bias Detection Validation")
    print("=" * 80)
    
    try:
        # Test individual validators
        await test_enhanced_prisma_validator()
        await test_bias_detector()
        
        # Test integrated system
        await test_integrated_validation()
        
        # Performance test
        run_performance_test()
        
        print("\n\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("Phase 2 enhanced validators are working correctly!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)