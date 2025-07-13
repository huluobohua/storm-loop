"""
PRISMA Assistant Package

Focused modules for systematic literature review automation following PRISMA guidelines.
Achieves 80% automation at 80% confidence with transparent limitations.
"""

# Data models
from .models import (
    Paper, 
    SearchStrategy, 
    ExtractionTemplate, 
    ScreeningResult
)

# Core functionality modules
from .search import SearchStrategyBuilder
from .screening import ScreeningAssistant, PRISMAScreener
from .extraction import DataExtractionHelper
from .reporting import ZeroDraftGenerator
from .assistant import PRISMAAssistant

# Main exports for external use
__all__ = [
    # Data models
    'Paper',
    'SearchStrategy', 
    'ExtractionTemplate',
    'ScreeningResult',
    
    # Core components
    'SearchStrategyBuilder',
    'ScreeningAssistant',
    'PRISMAScreener',
    'DataExtractionHelper', 
    'ZeroDraftGenerator',
    
    # Main orchestrator
    'PRISMAAssistant',
]

__version__ = '0.2.0'
__author__ = 'PRISMA Assistant Team'