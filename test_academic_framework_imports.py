"""
Test-Driven Development: Import and Circular Dependency Tests
RED Phase: These tests MUST fail initially and specify exact requirements
"""

import pytest
import sys
from pathlib import Path

class TestAcademicFrameworkImports:
    """Test suite ensuring no circular import dependencies exist"""
    
    def test_import_academic_validation_framework_succeeds(self):
        """
        Acceptance Criteria: `import academic_validation_framework` succeeds
        This is the primary requirement from issue #145
        """
        try:
            import academic_validation_framework
            assert academic_validation_framework is not None
        except ImportError as e:
            pytest.fail(f"Failed to import academic_validation_framework: {e}")
    
    def test_import_bias_detector_succeeds(self):
        """
        Test that bias_detector module can be imported without circular dependency errors
        """
        try:
            from academic_validation_framework.validators import bias_detector
            assert bias_detector is not None
        except ImportError as e:
            pytest.fail(f"Failed to import bias_detector: {e}")
    
    def test_import_bias_detection_strategies_succeeds(self):
        """
        Test that bias_detection_strategies module can be imported independently
        """
        try:
            from academic_validation_framework.validators.strategies import bias_detection_strategies
            assert bias_detection_strategies is not None
        except ImportError as e:
            pytest.fail(f"Failed to import bias_detection_strategies: {e}")
    
    def test_bias_check_model_exists_in_models_module(self):
        """
        Test that BiasCheck model is properly located in models.py (not in detector)
        This is the core fix required to break circular dependency
        """
        try:
            from academic_validation_framework.models import BiasCheck
            assert BiasCheck is not None
            assert hasattr(BiasCheck, '__init__')
        except ImportError as e:
            pytest.fail(f"BiasCheck not found in models module: {e}")
    
    def test_bias_detector_can_use_bias_check_without_circular_import(self):
        """
        Test that BiasDetector can use BiasCheck from models without circular dependency
        """
        try:
            from academic_validation_framework.validators.bias_detector import BiasDetector
            from academic_validation_framework.models import BiasCheck
            
            # Should be able to create instances without import errors
            detector = BiasDetector()
            bias_check = BiasCheck()
            
            assert detector is not None
            assert bias_check is not None
        except ImportError as e:
            pytest.fail(f"Circular import still exists: {e}")
    
    def test_strategy_pattern_uses_dependency_injection(self):
        """
        Test that strategies use dependency injection instead of direct imports
        """
        try:
            from academic_validation_framework.validators.strategies.bias_detection_strategies import DefaultBiasDetectionStrategy
            from academic_validation_framework.models import BiasCheck
            
            # Strategy should accept BiasCheck as dependency
            strategy = DefaultBiasDetectionStrategy()
            bias_check = BiasCheck()
            
            # Should be able to inject dependency without import errors
            assert hasattr(strategy, 'check_bias') or hasattr(strategy, 'validate')
        except ImportError as e:
            pytest.fail(f"Strategy dependency injection not implemented: {e}")
    
    def test_framework_instantiation_works(self):
        """
        Acceptance Criteria: Framework can be instantiated and basic validation works
        """
        try:
            import academic_validation_framework
            
            # Should be able to create main framework instance
            framework = academic_validation_framework.AcademicValidationFramework()
            assert framework is not None
            
            # Basic validation should work
            result = framework.validate_basic()
            assert result is not None
        except Exception as e:
            pytest.fail(f"Framework instantiation failed: {e}")

class TestBiasCheckModel:
    """Test BiasCheck model behavior and interface"""
    
    def test_bias_check_has_required_interface(self):
        """
        Test that BiasCheck provides the interface expected by strategies
        """
        from academic_validation_framework.models import BiasCheck
        
        bias_check = BiasCheck()
        
        # Must have core validation method
        assert hasattr(bias_check, 'validate')
        assert callable(bias_check.validate)
        
        # Deprecated properties should exist as class properties but raise NotImplementedError when accessed
        assert 'is_valid' in dir(bias_check.__class__)
        assert 'errors' in dir(bias_check.__class__)
        
        # Verify they raise NotImplementedError for safety
        try:
            _ = bias_check.is_valid
            assert False, "is_valid should raise NotImplementedError"
        except NotImplementedError:
            pass  # Expected behavior
            
        try:
            _ = bias_check.errors
            assert False, "errors should raise NotImplementedError"
        except NotImplementedError:
            pass  # Expected behavior
    
    def test_bias_check_validation_behavior(self):
        """
        Test BiasCheck validation behavior follows SOLID principles
        """
        from academic_validation_framework.models import BiasCheck
        
        bias_check = BiasCheck()
        
        # Test with valid input
        result = bias_check.validate({"valid": "data"})
        assert result is not None
        
        # Test with invalid input  
        result = bias_check.validate(None)
        assert result is not None

class TestDependencyInjectionPattern:
    """Test that dependency injection properly replaces direct imports"""
    
    def test_bias_detector_accepts_strategy_injection(self):
        """
        Test BiasDetector uses dependency injection for strategies
        """
        from academic_validation_framework.validators.bias_detector import BiasDetector
        from academic_validation_framework.validators.strategies.bias_detection_strategies import DefaultBiasDetectionStrategy
        
        strategy = DefaultBiasDetectionStrategy()
        detector = BiasDetector(strategy=strategy)
        
        assert detector is not None
        assert detector.strategy is strategy
    
    def test_strategy_accepts_bias_check_injection(self):
        """
        Test strategies accept BiasCheck as injected dependency
        """
        from academic_validation_framework.validators.strategies.bias_detection_strategies import DefaultBiasDetectionStrategy
        from academic_validation_framework.models import BiasCheck
        
        bias_check = BiasCheck()
        strategy = DefaultBiasDetectionStrategy(bias_check=bias_check)
        
        assert strategy is not None
        assert strategy.bias_check is bias_check

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
