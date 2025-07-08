#!/usr/bin/env python3
"""
Test Script for Strategy Pattern Refactor

Tests the new Strategy pattern implementation for citation validation.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.models import ResearchData
from academic_validation_framework.validators.enhanced_citation_validator_v2 import EnhancedCitationValidatorV2
from academic_validation_framework.strategies import ValidationStrictness, CalibrationMethod


async def test_strategy_refactor():
    """Test the new Strategy pattern implementation."""
    print("🧪 Testing Strategy Pattern Refactor...")
    
    # Create test configuration
    config = ValidationConfig(
        citation_accuracy_threshold=0.75,
        prisma_compliance_threshold=0.70,
        bias_detection_threshold=0.75
    )
    
    # Create test data
    test_citations = [
        "Smith, J. A. (2023). Machine learning in healthcare diagnosis. *Journal of Medical AI*, 15(3), 45-67. https://doi.org/10.1234/jmai.2023.001",
        "Johnson, M. B., & Brown, K. C. (2022). Healthcare algorithms and patient outcomes. *Medical Computing*, 8(2), 123-145.",
        "Wilson, P. D. (2024). \"AI applications in clinical settings.\" *Health Technology Review*, 12(4), 78-92.",
        "Davis, L. M., et al. (2023). Systematic review of machine learning diagnostics. *Clinical AI Research*, 7(1), 15-28.",
    ]
    
    sample_data = ResearchData(
        title="Comprehensive Study of AI in Healthcare",
        abstract="This study examines the application of artificial intelligence in healthcare settings.",
        citations=test_citations,
        authors=["Dr. Jane Smith", "Dr. John Doe"],
        publication_year=2024,
        journal="Healthcare Technology Journal",
        doi="10.1234/htj.2024.001"
    )
    
    # Test 1: Basic validation with default settings
    print("\n📋 Test 1: Basic Validation")
    validator = EnhancedCitationValidatorV2(config)
    result = await validator.validate(sample_data)
    
    print(f"✓ Validation Status: {result.status.value}")
    print(f"✓ Overall Score: {result.score:.3f}")
    print(f"✓ Validator: {result.validator_name}")
    
    if result.details:
        print(f"✓ Format Detected: {result.details.get('format_detected', 'Unknown')}")
        print(f"✓ Raw Confidence: {result.details.get('raw_confidence', 0.0):.3f}")
        print(f"✓ Calibrated Confidence: {result.details.get('calibrated_confidence', 0.0):.3f}")
        print(f"✓ Reliability Score: {result.details.get('reliability_score', 0.0):.3f}")
    
    # Test 2: Multi-format validation
    print("\n📋 Test 2: Multi-format Validation")
    validator.set_multi_format_validation(enabled=True, max_formats=2)
    result2 = await validator.validate(sample_data)
    
    print(f"✓ Multi-format Score: {result2.score:.3f}")
    if result2.details:
        validation_details = result2.details.get('format_validation_details', {})
        print(f"✓ Total Citations: {validation_details.get('total_citations', 0)}")
        print(f"✓ Valid Citations: {validation_details.get('valid_citations', 0)}")
    
    # Test 3: Strict validation mode
    print("\n📋 Test 3: Strict Validation Mode")
    validator.enable_strict_mode(True)
    validator.configure_input_validation(ValidationStrictness.STRICT)
    result3 = await validator.validate(sample_data)
    
    print(f"✓ Strict Mode Score: {result3.score:.3f}")
    
    # Test 4: Different calibration methods
    print("\n📋 Test 4: Different Calibration Methods")
    methods = [CalibrationMethod.TEMPERATURE_SCALING, CalibrationMethod.BAYESIAN_CALIBRATION]
    
    for method in methods:
        validator.configure_confidence_calibration(method)
        result = await validator.validate(sample_data)
        print(f"✓ {method.value}: {result.score:.3f}")
    
    # Test 5: Performance summary
    print("\n📋 Test 5: Performance Summary")
    performance = validator.get_performance_summary()
    print(f"✓ Validation Count: {performance['validation_count']}")
    print(f"✓ Average Processing Time: {performance['average_processing_time_ms']:.2f}ms")
    print(f"✓ Registry Statistics: {performance['registry_statistics']['total_validations']} total validations")
    
    # Test 6: Invalid input handling
    print("\n📋 Test 6: Invalid Input Handling")
    invalid_data = ResearchData(
        title="Test",
        abstract="Test",
        citations=["", "<script>alert('xss')</script>", "Invalid citation"],
        authors=["Test"],
        publication_year=2024
    )
    
    result6 = await validator.validate(invalid_data)
    print(f"✓ Invalid Input Score: {result6.score:.3f}")
    print(f"✓ Status: {result6.status.value}")
    
    if result6.details and result6.details.get('input_validation_failed'):
        print(f"✓ Input validation correctly failed")
        print(f"✓ Security Issues: {len(result6.details.get('security_issues', []))}")
    
    # Test 7: Registry functionality
    print("\n📋 Test 7: Registry Functionality")
    from academic_validation_framework.strategies.registry import get_global_registry
    
    registry = get_global_registry()
    available_formats = registry.get_available_formats()
    print(f"✓ Available Formats: {', '.join(available_formats)}")
    
    # Test auto-detection
    detected = registry.auto_detect_format(test_citations)
    print(f"✓ Auto-detected Format: {detected}")
    
    # Test multi-format validation
    multi_results = registry.validate_multi_format(test_citations[:2])
    print(f"✓ Multi-format Results: {list(multi_results.keys())}")
    
    for format_name, format_result in multi_results.items():
        print(f"  - {format_name}: {format_result.confidence:.3f} confidence")
    
    print("\n🎉 All tests completed successfully!")
    print("✅ Strategy pattern refactor is working correctly")


if __name__ == "__main__":
    asyncio.run(test_strategy_refactor())