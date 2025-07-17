"""
Test-Driven Development: SOLID Principles and Refactoring Tests
Verifies that refactored code follows SOLID principles and Sandi Metz rules
"""

import pytest
from academic_validation_framework.models import (
    BiasCheck, ValidationResult, Validator
)
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.validators.strategies.bias_detection_strategies import (
    DefaultBiasDetectionStrategy, AdvancedBiasDetectionStrategy
)
from academic_validation_framework import AcademicValidationFramework


class TestSOLIDPrinciples:
    """Test suite ensuring SOLID principles are followed"""
    
    def test_single_responsibility_principle(self):
        """Each class has a single, well-defined responsibility"""
        bias_check = BiasCheck()
        detector = BiasDetector()
        strategy = DefaultBiasDetectionStrategy()
        
        # BiasCheck: only validates data
        assert hasattr(bias_check, 'validate')
        assert not hasattr(bias_check, 'detect_bias')
        
        # BiasDetector: only detects bias using strategies
        assert hasattr(detector, 'detect_bias')
        assert hasattr(detector, 'set_strategy')
        
        # Strategy: only implements bias checking strategy
        assert hasattr(strategy, 'check_bias')
    
    def test_open_closed_principle(self):
        """Classes are open for extension, closed for modification"""
        # Base strategy can be extended without modification
        basic_strategy = DefaultBiasDetectionStrategy()
        advanced_strategy = AdvancedBiasDetectionStrategy()
        
        # Both implement the same interface
        test_data = {"test": "data"}
        
        basic_result = basic_strategy.check_bias(test_data)
        advanced_result = advanced_strategy.check_bias(test_data)
        
        assert isinstance(basic_result, ValidationResult)
        assert isinstance(advanced_result, ValidationResult)
        
        # Advanced strategy adds behavior without modifying base
        empty_dict_result = advanced_strategy.check_bias({})
        assert not empty_dict_result.is_valid
        assert "Empty data structures" in empty_dict_result.errors[0]
    
    def test_liskov_substitution_principle(self):
        """Subtypes must be substitutable for their base types"""
        validator = BiasCheck()
        detector = BiasDetector()
        
        # BiasCheck implements Validator interface
        assert isinstance(validator, Validator)
        
        # Can substitute any Validator implementation
        custom_validator = BiasCheck()
        strategy = DefaultBiasDetectionStrategy(bias_check=custom_validator)
        
        result = strategy.check_bias({"test": "data"})
        assert isinstance(result, ValidationResult)
    
    def test_interface_segregation_principle(self):
        """No client forced to depend on methods it doesn't use"""
        # DefaultBiasDetectionStrategy only exposes bias checking methods
        strategy = DefaultBiasDetectionStrategy()
        
        # Strategy doesn't have unnecessary validation methods
        assert hasattr(strategy, 'check_bias')
        assert not hasattr(strategy, 'save_to_database')
        assert not hasattr(strategy, 'send_notification')
    
    def test_dependency_inversion_principle(self):
        """Depend on abstractions, not concretions"""
        # BiasDetector depends on strategy abstraction
        detector = BiasDetector()
        
        # Can inject any strategy implementation
        basic_strategy = DefaultBiasDetectionStrategy()
        advanced_strategy = AdvancedBiasDetectionStrategy()
        
        detector.set_strategy(basic_strategy)
        result1 = detector.detect_bias({"test": "data"})
        
        detector.set_strategy(advanced_strategy)
        result2 = detector.detect_bias({"test": "data"})
        
        assert isinstance(result1, ValidationResult)
        assert isinstance(result2, ValidationResult)


class TestSandiMetzRules:
    """Test suite ensuring Sandi Metz rules are followed"""
    
    def test_class_line_count_under_100(self):
        """Classes should be under 100 lines"""
        import inspect
        
        classes_to_check = [
            BiasCheck, ValidationResult, BiasDetector, 
            DefaultBiasDetectionStrategy, AdvancedBiasDetectionStrategy
        ]
        
        for cls in classes_to_check:
            source_lines = inspect.getsourcelines(cls)[0]
            line_count = len(source_lines)
            assert line_count < 100, f"{cls.__name__} has {line_count} lines (max 100)"
    
    def test_method_line_count_under_5(self):
        """Methods should be under 5 lines (excluding docstrings)"""
        import inspect
        
        bias_check = BiasCheck()
        
        # Check validate method line count
        validate_method = getattr(bias_check, 'validate')
        source_lines = inspect.getsourcelines(validate_method)[0]
        
        # Count only non-docstring, non-whitespace, non-signature lines
        code_lines = [line.strip() for line in source_lines 
                     if line.strip() 
                     and not line.strip().startswith('"""')
                     and not line.strip().startswith('def ')]
        
        # Validate method body should follow Sandi Metz 5-line rule
        assert len(code_lines) <= 5, f"validate method has {len(code_lines)} body lines (max 5)"
    
    def test_parameter_count_under_4(self):
        """Methods should have no more than 4 parameters"""
        bias_check = BiasCheck()
        detector = BiasDetector()
        strategy = DefaultBiasDetectionStrategy()
        
        # Check key methods have reasonable parameter counts
        import inspect
        
        validate_sig = inspect.signature(bias_check.validate)
        assert len(validate_sig.parameters) <= 4
        
        detect_sig = inspect.signature(detector.detect_bias)
        assert len(detect_sig.parameters) <= 4
        
        check_sig = inspect.signature(strategy.check_bias)
        assert len(check_sig.parameters) <= 4


class TestValidationResult:
    """Test ValidationResult value object"""
    
    def test_validation_result_immutability(self):
        """ValidationResult should be immutable"""
        result = ValidationResult(is_valid=True, errors=["test"])
        
        # Properties return copies, not references
        errors = result.errors
        errors.append("modified")
        
        # Original should be unchanged
        assert len(result.errors) == 1
        assert "modified" not in result.errors
    
    def test_validation_result_to_dict(self):
        """ValidationResult should convert to dict properly"""
        result = ValidationResult(is_valid=False, errors=["error1", "error2"])
        dict_result = result.to_dict()
        
        expected = {"valid": False, "errors": ["error1", "error2"]}
        assert dict_result == expected


class TestFrameworkIntegration:
    """Test complete framework integration with SOLID principles"""
    
    def test_framework_strategy_injection(self):
        """Framework should support strategy injection"""
        advanced_strategy = AdvancedBiasDetectionStrategy()
        framework = AcademicValidationFramework(strategy=advanced_strategy)
        
        # Framework uses injected strategy
        result = framework.validate_for_bias({})
        assert not result.is_valid
        assert "Empty data structures" in result.errors[0]
    
    def test_framework_strategy_change(self):
        """Framework should allow strategy changes at runtime"""
        framework = AcademicValidationFramework()
        
        # Test with default strategy
        result1 = framework.validate_for_bias({})
        assert result1.is_valid  # Default allows empty dict
        
        # Change to advanced strategy
        advanced_strategy = AdvancedBiasDetectionStrategy()
        framework.set_strategy(advanced_strategy)
        
        result2 = framework.validate_for_bias({})
        assert not result2.is_valid  # Advanced rejects empty dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
