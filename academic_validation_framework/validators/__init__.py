"""
Academic validation modules for research quality assessment.
"""

from .base import BaseValidator
from .prisma_validator import PRISMAValidator
from .citation_accuracy_validator import CitationAccuracyValidator

__all__ = [
    "BaseValidator",
    "PRISMAValidator", 
    "CitationAccuracyValidator",
]