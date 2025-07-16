"""
PRISMA Core Data Models and Types.

Focused module containing only core data structures and type definitions
for PRISMA Assistant functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


@dataclass
class Paper:
    """Represents a research paper in systematic review."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    year: int
    journal: str
    doi: Optional[str] = None
    url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    study_type: Optional[str] = None
    sample_size: Optional[int] = None
    
    # Screening decisions
    screening_decision: Optional[str] = None  # include, exclude, maybe
    exclusion_reason: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class SearchStrategy:
    """Comprehensive search strategy across databases."""
    research_question: str
    pico_elements: Dict[str, List[str]]  # Population, Intervention, Comparison, Outcome
    search_queries: Dict[str, str]  # Database -> query string
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    date_range: Optional[Tuple[int, int]] = None
    languages: List[str] = field(default_factory=lambda: ["English"])


@dataclass
class ExtractionTemplate:
    """Template for systematic data extraction."""
    fields: Dict[str, Dict[str, Any]]  # field_name -> {type, description, required}
    study_characteristics: List[str]
    outcome_measures: List[str]
    quality_indicators: List[str]


@dataclass
class ScreeningResult:
    """Result of paper screening operation."""
    decision: str  # 'include', 'exclude', 'maybe'
    confidence: float
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# Export core types
__all__ = [
    'Paper',
    'SearchStrategy', 
    'ExtractionTemplate',
    'ScreeningResult'
]