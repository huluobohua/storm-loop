"""
Configuration package for Academic Validation Framework.
"""

from .validation_constants import ValidationConstants

# Import from parent module for compatibility
try:
    from ..config import ValidationConfig, FrameworkConfig
    __all__ = ['ValidationConstants', 'ValidationConfig', 'FrameworkConfig']
except ImportError:
    # Fallback for compatibility
    __all__ = ['ValidationConstants']
    
    # Create dummy classes for compatibility
    class FrameworkConfig:
        def __init__(self):
            pass
    
    class ValidationConfig:
        def __init__(self, **kwargs):
            self.bias_detection_threshold = kwargs.get('bias_detection_threshold', 0.7)
            self.prisma_threshold = kwargs.get('prisma_threshold', 0.7)