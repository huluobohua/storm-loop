"""
Academic Validation Framework
Main entry point for the framework with no circular dependencies
Follows SOLID principles and provides clean dependency injection
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
    Follows Single Responsibility and Dependency Inversion principles
    """
    
    def __init__(self, strategy: IBiasDetectionStrategy = None):
        """
        Initialize framework with proper dependency injection
        
        Args:
            strategy: Optional bias detection strategy implementing IBiasDetectionStrategy
        """
        self.bias_check = BiasCheck()
        self.bias_detector = BiasDetector(strategy=strategy)
    
    def validate_basic(self):
        """Perform basic validation to verify framework works"""
        return {"status": "working", "framework": "initialized"}
    
    def validate_for_bias(self, data):
        """
        Validate data for bias using configured strategy
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return self.bias_detector.detect_bias(data)
    
    def set_strategy(self, strategy: IBiasDetectionStrategy):
        """
        Set bias detection strategy
        
        Args:
            strategy: New strategy implementing IBiasDetectionStrategy
        """
        self.bias_detector.set_strategy(strategy)


__all__ = [
    "AcademicValidationFramework", 
    "BiasCheck", 
    "BiasDetector",
    "ValidationResult",
    "Validator",
    "IBiasDetectionStrategy",
    "DefaultBiasDetectionStrategy",
    "AdvancedBiasDetectionStrategy",
    "BiasDetectionStrategy"  # Legacy alias
]
