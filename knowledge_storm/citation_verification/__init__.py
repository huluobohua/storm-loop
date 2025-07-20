"""
Citation Verification Module

Provides comprehensive citation integrity verification to prevent fabricated
academic references and ensure all citations map to legitimate sources.

Core Components:
- CitationValidator: Real-time citation verification
- SourceMapper: Paper -> citation relationship tracking  
- IntegrityChecker: Fabrication detection and prevention
- QualityScorer: Citation relevance and authority assessment
"""

from .models import Citation, VerificationResult, ValidationReport
from .validator import CitationValidator, OpenAlexClient, CrossrefClient
from .source_mapper import SourceMapper, PaperSource
from .integrity_checker import IntegrityChecker
from .quality_scorer import QualityScorer
from .quality_components import RelevanceScorer, AuthorityScorer, RecencyScorer, AccessibilityScorer
from .pattern_detectors import TitlePatternDetector, AuthorPatternDetector, JournalPatternDetector, DOIPatternDetector

__all__ = [
    'Citation',
    'VerificationResult', 
    'ValidationReport',
    'CitationValidator',
    'OpenAlexClient',
    'CrossrefClient',
    'SourceMapper',
    'PaperSource',
    'IntegrityChecker',
    'QualityScorer',
    'RelevanceScorer',
    'AuthorityScorer', 
    'RecencyScorer',
    'AccessibilityScorer',
    'TitlePatternDetector',
    'AuthorPatternDetector',
    'JournalPatternDetector',
    'DOIPatternDetector'
]