"""
Academic validation modules for research quality assessment.
"""

from .base import BaseValidator
from .prisma_validator import PRISMAValidator
from .citation_accuracy_validator import CitationAccuracyValidator
from .real_prisma_validator import RealPRISMAValidator
from .real_citation_validator import RealCitationValidator
from .real_bias_detector import RealBiasDetector

__all__ = [
    "BaseValidator",
    "PRISMAValidator", 
    "CitationAccuracyValidator",
    "RealPRISMAValidator",
    "RealCitationValidator",
    "RealBiasDetector",
]