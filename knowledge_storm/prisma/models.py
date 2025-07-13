"""
PRISMA data models for systematic review process.

Contains the core data structures used across the PRISMA assistant modules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class Paper:
    """Represents a research paper in the systematic review."""
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
    """Result of paper screening process."""
    paper_id: str
    decision: str  # include, exclude, maybe
    confidence: float
    reasons: List[str]
    reviewer: str
    timestamp: str
    notes: Optional[str] = None