"""
VERIFY System Package

Validated, Efficient Research with Iterative Fact-checking and Yield optimization.
Focused modules for fact verification, memory learning, and targeted fixes.
"""

# Data models
from .models import (
    Claim,
    VerificationResult, 
    ResearchPattern
)

# Core functionality modules  
from .fact_checker import FactChecker
from .memory import ResearchMemory
from .fixer import TargetedFixer
from .system import VERIFYSystem

# Main exports for external use
__all__ = [
    # Data models
    'Claim',
    'VerificationResult',
    'ResearchPattern',
    
    # Core components
    'FactChecker',
    'ResearchMemory', 
    'TargetedFixer',
    
    # Main orchestrator
    'VERIFYSystem',
]

__version__ = '0.2.0'
__author__ = 'VERIFY System Team'