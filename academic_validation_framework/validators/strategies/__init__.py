"""
Strategies package for bias detection
"""

from .bias_detection_strategies import (
    DefaultBiasDetectionStrategy, 
    AdvancedBiasDetectionStrategy,
    BiasDetectionStrategy  # Legacy alias
)

__all__ = [
    "DefaultBiasDetectionStrategy", 
    "AdvancedBiasDetectionStrategy",
    "BiasDetectionStrategy"  # Legacy alias for backward compatibility
]