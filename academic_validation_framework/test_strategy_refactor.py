"""
Test script demonstrating the Strategy pattern refactor for citation validation.

This script shows how the new architecture works and compares it with the old if-elif approach.
"""

import asyncio
import json
from typing import List, Dict, Any

from models import ResearchData, ValidationStatus
from config import ValidationConfig
from strategies import (
    ValidationStrategyRegistry,
    CitationInputValidator,
    ConfidenceCalibrator,
    ValidationLevel,
    CalibrationMethod
)
from validators.enhanced_citation_validator_v2 import (
    EnhancedCitationValidatorV2,
    CitationValidationConfig
)


def create_test_citations() -> List[str]:
    """Create a diverse set of test citations in different formats."""
    return [
        # APA format
        'Smith, J. A. (2020). The impact of climate change on biodiversity. Nature, 578(7796), 241-245.',
        
        # MLA format  
        'Johnson, Mary K. "Digital Transformation in Education." Educational Technology Review, vol. 45, no. 3, 2021, pp. 15-28.',
        
        # Chicago format
        'Brown, Robert L. Climate Policy and Economic Growth. Chicago: University of Chicago Press, 2019.',
        
        # IEEE format
        'A. B. Chen, C. D. Wang, and E. F. Li, "Machine learning approaches to natural language processing," IEEE Transactions on Computers, vol. 69, no. 4, pp. 123-135, Apr. 2020.',
        
        # Harvard format
        'Davis, S. (2021) 'Sustainable development goals and corporate responsibility', Journal of Business Ethics, 156(2), pp. 45-62.',
        
        # Malformed citations
        'Invalid citation without proper formatting',
        'Smith 2020 no parentheses or proper structure',
        
        # Partially correct citations
        'Wilson, T. (2019). Incomplete citation missing journal info.',
        'Complete Author Name, "Good Title," But Missing Publication Details.',
        
        # Citations with special characters and URLs
        'García, M. & Müller, K. (2021). International collaboration in research. doi:10.1038/s41586-021-03456-9',
        'Taylor, A. (2020). Online learning platforms. Available at: https://example.com/article [Accessed 15 March 2021].'
    ]


async def demonstrate_strategy_pattern():
    """Demonstrate the Strategy pattern implementation."""
    print("=== Citation Validation Strategy Pattern Demo ===\n")
    
    # Initialize configuration
    config = ValidationConfig()
    citation_config = CitationValidationConfig(
        input_validation_level=ValidationLevel.MODERATE,
        confidence_calibration_method=CalibrationMethod.TEMPERATURE_SCALING,
        enable_multi_format_validation=True,
        format_preferences=["APA", "MLA", "Chicago", "IEEE", "Harvard"],
        strict_mode=True
    )
    
    # Create validator instance
    validator = EnhancedCitationValidatorV2(config, citation_config)
    
    # Create test data
    test_citations = create_test_citations()
    research_data = ResearchData(
        title="Test Research Paper",
        abstract="This is a test abstract for demonstration purposes.",
        citations=test_citations
    )
    
    print(f"Testing {len(test_citations)} citations with multi-format validation...\n")
    
    # Perform validation
    result = await validator.validate(research_data)
    
    # Display results
    print("=== VALIDATION RESULTS ===")
    print(f"Status: {result.status.value}")
    print(f"Overall Score: {result.score:.3f}")
    print(f"Best Format: {result.details.get('best_format', 'Unknown')}")
    print()
    
    # Show format-specific results
    format_results = result.details.get('format_results', {})
    for format_name, format_data in format_results.items():
        if 'error' in format_data:
            print(f"{format_name}: ERROR - {format_data['error']}")
        else:
            confidence = format_data['overall_confidence']
            print(f"{format_name}: {confidence:.3f} confidence")
    
    print()
    
    # Show individual citation analysis
    print("=== INDIVIDUAL CITATION ANALYSIS ===")
    if 'best_format' in result.details and result.details['best_format'] in format_results:
        best_format = result.details['best_format']
        best_results = format_results[best_format]['results']
        
        for i, (citation, citation_result) in enumerate(zip(test_citations, best_results)):
            print(f"\nCitation {i+1} ({best_format}):")
            print(f"  Text: {citation[:80]}{'...' if len(citation) > 80 else ''}")
            print(f"  Valid: {citation_result.is_valid}")
            print(f"  Confidence: {citation_result.confidence:.3f}")
            
            if citation_result.errors:
                print(f"  Errors: {len(citation_result.errors)}")
                for error in citation_result.errors[:2]:  # Show first 2 errors
                    print(f"    - {error.message}")
            
            if citation_result.warnings:
                print(f"  Warnings: {len(citation_result.warnings)}")
    
    print()
    
    # Show performance statistics
    print("=== PERFORMANCE STATISTICS ===")
    stats = validator.get_performance_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    return result


async def demonstrate_individual_strategies():
    """Demonstrate individual strategy usage."""
    print("\n=== INDIVIDUAL STRATEGY DEMONSTRATION ===\n")
    
    # Initialize registry
    registry = ValidationStrategyRegistry()
    
    # Test APA strategy
    apa_strategy = registry.get_strategy("APA", strict_mode=True)
    apa_citation = "Smith, J. A. (2020). The impact of climate change. Nature, 578, 241-245."
    
    print("Testing APA Strategy:")
    print(f"Citation: {apa_citation}")
    
    apa_result = apa_strategy.validate_single_citation(apa_citation)
    print(f"Valid: {apa_result.is_valid}")
    print(f"Confidence: {apa_result.confidence:.3f}")
    print(f"Errors: {len(apa_result.errors)}")
    
    if apa_result.errors:
        for error in apa_result.errors:
            print(f"  - {error.message} ({error.severity.value})")
    
    print()
    
    # Test IEEE strategy
    ieee_strategy = registry.get_strategy("IEEE", strict_mode=True)
    ieee_citation = 'A. B. Chen, "Machine learning," IEEE Trans. Computers, vol. 69, no. 4, pp. 123-135, 2020.'
    
    print("Testing IEEE Strategy:")
    print(f"Citation: {ieee_citation}")
    
    ieee_result = ieee_strategy.validate_single_citation(ieee_citation)
    print(f"Valid: {ieee_result.is_valid}")
    print(f"Confidence: {ieee_result.confidence:.3f}")
    print(f"Errors: {len(ieee_result.errors)}")
    
    if ieee_result.errors:
        for error in ieee_result.errors:
            print(f"  - {error.message} ({error.severity.value})")


async def demonstrate_input_validation():
    """Demonstrate input validation layer."""
    print("\n=== INPUT VALIDATION DEMONSTRATION ===\n")
    
    input_validator = CitationInputValidator(ValidationLevel.MODERATE)
    
    test_inputs = [
        "Smith, J. (2020). Valid citation example.",
        "Too short",
        "Normal citation with some <script>alert('xss')</script> suspicious content",
        "Very " + "long " * 200 + "citation that exceeds reasonable length limits",
        "",  # Empty
        None,  # None input
        "Citation with\x00null bytes and\x01control chars"
    ]
    
    for i, test_input in enumerate(test_inputs):
        print(f"Input {i+1}: {str(test_input)[:50]}{'...' if test_input and len(str(test_input)) > 50 else ''}")
        
        try:
            result = input_validator.validate_single_input(test_input)
            print(f"  Valid: {result.is_valid}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Warnings: {len(result.warnings)}")
            
            if result.errors:
                for error in result.errors[:2]:
                    print(f"    - {error}")
            
            if result.sanitized_input and result.sanitized_input != str(test_input):
                print(f"  Sanitized: {result.sanitized_input[:50]}...")
        
        except Exception as e:
            print(f"  Exception: {e}")
        
        print()


async def demonstrate_confidence_calibration():
    """Demonstrate confidence calibration system."""
    print("\n=== CONFIDENCE CALIBRATION DEMONSTRATION ===\n")
    
    from strategies.confidence_calibrator import CalibrationData, ConfidenceCalibrator
    from strategies.base import ValidationError, ValidationSeverity
    
    calibrator = ConfidenceCalibrator(CalibrationMethod.TEMPERATURE_SCALING)
    
    # Test different calibration scenarios
    test_scenarios = [
        {
            'name': 'High confidence, no errors',
            'data': CalibrationData(
                raw_confidence=0.95,
                validation_errors=[],
                citation_length=150,
                format_indicators=5
            )
        },
        {
            'name': 'Medium confidence, minor errors',
            'data': CalibrationData(
                raw_confidence=0.75,
                validation_errors=[
                    ValidationError("Minor formatting issue", ValidationSeverity.MINOR)
                ],
                citation_length=120,
                format_indicators=3
            )
        },
        {
            'name': 'Low confidence, critical errors',
            'data': CalibrationData(
                raw_confidence=0.4,
                validation_errors=[
                    ValidationError("Missing required field", ValidationSeverity.CRITICAL),
                    ValidationError("Invalid format", ValidationSeverity.MAJOR)
                ],
                citation_length=50,
                format_indicators=1
            )
        }
    ]
    
    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        data = scenario['data']
        
        metrics = calibrator.calibrate_confidence(data)
        
        print(f"  Raw Confidence: {data.raw_confidence:.3f}")
        print(f"  Calibrated Confidence: {metrics.calibrated_confidence:.3f}")
        print(f"  Confidence Interval: ({metrics.confidence_interval[0]:.3f}, {metrics.confidence_interval[1]:.3f})")
        print(f"  Reliability Score: {metrics.reliability_score:.3f}")
        print(f"  Uncertainty Estimate: {metrics.uncertainty_estimate:.3f}")
        print()


async def compare_with_old_approach():
    """Compare the new Strategy pattern with the old if-elif approach."""
    print("\n=== COMPARISON WITH OLD APPROACH ===\n")
    
    # Simulate old if-elif validation (simplified)
    def old_validate_format(format_name: str, citations: List[str]) -> Dict[str, Any]:
        """Simulate the old if-elif chain approach."""
        if format_name == "APA":
            # Old APA validation logic
            valid_count = sum(1 for c in citations if '(' in c and ')' in c)
            confidence = valid_count / len(citations) if citations else 0
            return {"valid": confidence > 0.8, "confidence": confidence}
        elif format_name == "MLA":
            # Old MLA validation logic  
            valid_count = sum(1 for c in citations if '"' in c)
            confidence = valid_count / len(citations) if citations else 0
            return {"valid": confidence > 0.7, "confidence": confidence}
        elif format_name == "Chicago":
            # Old Chicago validation logic
            return {"valid": True, "confidence": 0.7}  # Placeholder
        elif format_name == "IEEE":
            # Old IEEE validation logic
            return {"valid": True, "confidence": 0.8}  # Placeholder
        elif format_name == "Harvard":
            # Old Harvard validation logic
            return {"valid": True, "confidence": 0.72}  # Placeholder
        else:
            return {"valid": False, "confidence": 0.0}
    
    test_citations = create_test_citations()[:5]  # Use subset for comparison
    
    print("OLD APPROACH (if-elif chain):")
    print("Problems:")
    print("- Difficult to extend with new formats")
    print("- Violates Open/Closed Principle")
    print("- No sophisticated error handling")
    print("- Limited confidence calibration")
    print("- Tightly coupled validation logic")
    print()
    
    for format_name in ["APA", "MLA", "Chicago"]:
        old_result = old_validate_format(format_name, test_citations)
        print(f"{format_name}: Valid={old_result['valid']}, Confidence={old_result['confidence']:.3f}")
    
    print("\nNEW APPROACH (Strategy pattern):")
    print("Benefits:")
    print("- Easily extensible (Open/Closed Principle)")
    print("- Clean separation of concerns (Single Responsibility)")
    print("- Dependency injection support")
    print("- Sophisticated error handling and confidence calibration")
    print("- Comprehensive input validation")
    print("- Performance monitoring and statistics")
    print("- Type safety and better testing")
    print()
    
    # Show new approach results
    registry = ValidationStrategyRegistry()
    for format_name in ["APA", "MLA", "Chicago"]:
        strategy = registry.get_strategy(format_name)
        results = strategy.validate_citations(test_citations)
        overall_confidence = strategy.calculate_overall_confidence(results)
        valid_count = sum(1 for r in results if r.is_valid)
        
        print(f"{format_name}: Valid={valid_count}/{len(results)}, Confidence={overall_confidence:.3f}")


async def main():
    """Main demonstration function."""
    print("Citation Validation Strategy Pattern Refactor Demonstration")
    print("=" * 60)
    
    # Run all demonstrations
    await demonstrate_strategy_pattern()
    await demonstrate_individual_strategies()
    await demonstrate_input_validation()
    await demonstrate_confidence_calibration()
    await compare_with_old_approach()
    
    print("\n" + "=" * 60)
    print("Strategy Pattern Refactor Demonstration Complete!")
    print("\nKey Architecture Benefits:")
    print("✓ SOLID Principles compliance")
    print("✓ Easy extensibility for new citation formats")
    print("✓ Robust error handling and input validation")
    print("✓ Sophisticated confidence calibration")
    print("✓ Comprehensive testing capabilities")
    print("✓ Performance monitoring and statistics")
    print("✓ Clean separation of concerns")
    print("✓ Type safety and maintainability")


if __name__ == "__main__":
    asyncio.run(main())