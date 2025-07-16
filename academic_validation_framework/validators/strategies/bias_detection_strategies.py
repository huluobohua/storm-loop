"""
Bias detection strategies using dependency injection
No longer imports BiasCheck directly to avoid circular dependencies
Follows SOLID principles and Sandi Metz rules
"""

from typing import Any
from ...models import BiasCheck, ValidationResult, Validator
from ..bias_detector import BiasDetectionStrategy as BaseStrategy


class BiasDetectionStrategy(BaseStrategy):
    """
    Concrete strategy for bias detection using dependency injection
    Accepts BiasCheck as injected dependency instead of importing directly
    Follows Single Responsibility and Dependency Inversion principles
    """
    
    def __init__(self, bias_check: Validator = None):
        """
        Initialize strategy with optional bias check injection
        
        Args:
            bias_check: Validator instance for validation
        """
        self.bias_check = bias_check or BiasCheck()
    
    def check_bias(self, data: Any) -> ValidationResult:
        """
        Check data for bias using injected BiasCheck
        
        Args:
            data: Data to check for bias
            
        Returns:
            ValidationResult: Bias check result
        """
        return self.bias_check.validate(data)
    
    def validate(self, data: Any) -> ValidationResult:
        """Alias for check_bias to support multiple interfaces"""
        return self.check_bias(data)


class AdvancedBiasDetectionStrategy(BaseStrategy):
    """
    Advanced strategy with additional bias detection logic
    Demonstrates Open/Closed Principle - extending without modifying
    """
    
    def __init__(self, bias_check: Validator = None):
        self.bias_check = bias_check or BiasCheck()
    
    def check_bias(self, data: Any) -> ValidationResult:
        """Advanced bias detection with additional checks"""
        # First run basic validation
        result = self.bias_check.validate(data)
        
        if not result.is_valid:
            return result
        
        # Additional advanced checks
        if isinstance(data, dict) and len(data) == 0:
            return ValidationResult(
                is_valid=False,
                errors=["Empty data structures may introduce bias"]
            )
        
        return ValidationResult(is_valid=True)