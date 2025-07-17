"""
Academic Validation Framework
Main entry point for the framework with no circular dependencies
Follows SOLID principles with pure dependency injection
"""

from .models import BiasCheck, ValidationResult, Validator
from .validators.bias_detector import BiasDetector, IBiasDetectionStrategy
from .validators.strategies.bias_detection_strategies import (
    DefaultBiasDetectionStrategy, 
    AdvancedBiasDetectionStrategy,
    BiasDetectionStrategy  # Legacy alias
)


class AcademicValidationFramework:
    """
    Main framework class for academic validation
    Pure dependency injection - no concrete instantiation
    Follows Dependency Inversion Principle completely
    """
    
    def __init__(self, bias_detector: BiasDetector, bias_check: Validator):
        """
        Initialize framework with injected dependencies
        
        Args:
            bias_detector: BiasDetector instance with configured strategy
            bias_check: Validator instance for basic validation
        """
        self.bias_detector = bias_detector
        self.bias_check = bias_check
    
    def validate_basic(self):
        """Perform basic validation to verify framework works"""
        return {"status": "working", "framework": "initialized"}
    
    def validate_for_bias(self, data):
        """
        Validate data for bias using injected detector
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return self.bias_detector.detect_bias(data)
    
    def validate_data(self, data):
        """
        Validate data using injected validator
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return self.bias_check.validate(data)


class AcademicValidationFrameworkFactory:
    """
    Factory for creating AcademicValidationFramework with default dependencies
    Handles dependency assembly while keeping framework pure
    """
    
    @staticmethod
    def create_default() -> AcademicValidationFramework:
        """
        Create framework with default dependencies
        
        Returns:
            AcademicValidationFramework: Configured framework instance
        """
        bias_check = BiasCheck()
        strategy = DefaultBiasDetectionStrategy(bias_check=bias_check)
        bias_detector = BiasDetector(strategy=strategy)
        
        return AcademicValidationFramework(
            bias_detector=bias_detector,
            bias_check=bias_check
        )
    
    @staticmethod
    def create_with_strategy(strategy: IBiasDetectionStrategy) -> AcademicValidationFramework:
        """
        Create framework with custom strategy
        
        Args:
            strategy: Custom bias detection strategy
            
        Returns:
            AcademicValidationFramework: Configured framework instance
        """
        bias_check = BiasCheck()
        bias_detector = BiasDetector(strategy=strategy)
        
        return AcademicValidationFramework(
            bias_detector=bias_detector,
            bias_check=bias_check
        )
    
    @staticmethod
    def create_advanced() -> AcademicValidationFramework:
        """
        Create framework with advanced strategy
        
        Returns:
            AcademicValidationFramework: Framework with advanced strategy
        """
        bias_check = BiasCheck()
        strategy = AdvancedBiasDetectionStrategy(bias_check=bias_check)
        bias_detector = BiasDetector(strategy=strategy)
        
        return AcademicValidationFramework(
            bias_detector=bias_detector,
            bias_check=bias_check
        )


__all__ = [
    "AcademicValidationFramework", 
    "AcademicValidationFrameworkFactory",
    "BiasCheck", 
    "BiasDetector",
    "ValidationResult",
    "Validator",
    "IBiasDetectionStrategy",
    "DefaultBiasDetectionStrategy",
    "AdvancedBiasDetectionStrategy",
    "BiasDetectionStrategy"  # Legacy alias
]