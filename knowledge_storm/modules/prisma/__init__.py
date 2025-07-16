"""
PRISMA Assistant Package.

Focused modules for systematic review automation following the 80/20 methodology.
Implements the PRISMA methodology with integration to STORM-Academic VERIFY system.
"""

from .core import Paper, SearchStrategy, ExtractionTemplate, ScreeningResult
from .search_strategy import SearchStrategyBuilder
from .screening import ScreeningAssistant, PRISMAScreener
from .extraction import DataExtractionHelper
from .abstract_analyzer import AbstractAnalyzer, AbstractAnalysisResult
from .draft_generation import ZeroDraftGenerator

__all__ = [
    'Paper',
    'SearchStrategy',
    'ExtractionTemplate', 
    'ScreeningResult',
    'SearchStrategyBuilder',
    'ScreeningAssistant',
    'PRISMAScreener',
    'DataExtractionHelper',
    'AbstractAnalyzer',
    'AbstractAnalysisResult',
    'ZeroDraftGenerator'
]