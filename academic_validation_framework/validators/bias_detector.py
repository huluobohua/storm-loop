"""
Bias Detector module - refactored to use dependency injection
BiasCheck moved to models.py to break circular dependency
Follows SOLID principles and Sandi Metz rules
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..models import BiasCheck, ValidationResult


class IBiasDetectionStrategy(ABC):
    """
    Interface for bias detection strategies (Interface Segregation)
    Clear naming distinguishes this as an interface/protocol
    """
    
    @abstractmethod
    def check_bias(self, data: Any) -> ValidationResult:
        """Check data for bias"""
        pass


class BiasDetector:
    """
    Bias detector using dependency injection pattern
    No longer contains BiasCheck to avoid circular imports
    Follows Single Responsibility and Dependency Inversion principles
    """
    
    def __init__(self, strategy: IBiasDetectionStrategy):
        """
        Initialize detector with required strategy injection
        Pure dependency injection - no optional dependencies
        
        Args:
            strategy: Required bias detection strategy implementing IBiasDetectionStrategy
        """
        self.strategy = strategy
    
    def detect_bias(self, data: Any) -> ValidationResult:
        """
        Detect bias in data using injected strategy
        
        Args:
            data: Data to analyze for bias
            
        Returns:
            ValidationResult: Bias detection result
        """
        return self.strategy.check_bias(data)
