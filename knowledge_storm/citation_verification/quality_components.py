"""
Quality Scoring Components

Focused quality assessment components following single responsibility.
Each component handles one aspect of citation quality evaluation.
"""

from typing import Dict, Optional, Set
from datetime import datetime
from .models import Citation


class RelevanceScorer:
    """Scores citation relevance to research context."""
    
    def score(self, citation: Citation, context: Optional[str] = None) -> float:
        """Score how relevant citation is to research context."""
        if not context:
            return 0.5  # Neutral score without context
        
        # Simple keyword matching for relevance
        context_words = set(context.lower().split())
        title_words = set(citation.title.lower().split())
        
        overlap = len(context_words.intersection(title_words))
        max_words = max(len(context_words), len(title_words))
        
        if max_words == 0:
            return 0.0
        
        return min(overlap / max_words * 2, 1.0)


class AuthorityScorer:
    """Scores citation authority based on journal and metadata."""
    
    def __init__(self):
        """Initialize journal impact rankings."""
        self._journal_rankings = {
            'nature': 0.95,
            'science': 0.95,
            'cell': 0.90,
            'nature machine intelligence': 0.85,
            'test journal': 0.5,
            'unknown journal': 0.3
        }
    
    def score(self, citation: Citation) -> float:
        """Score citation authority."""
        # Journal ranking component
        journal_score = self._journal_rankings.get(
            citation.journal.lower(), 
            0.3  # Default for unknown journals
        )
        
        # Author count factor (more authors can indicate collaboration)
        author_factor = min(len(citation.authors) / 5.0, 1.0)
        
        # DOI presence indicates formal publication
        doi_factor = 1.0 if citation.doi else 0.8
        
        return (journal_score * 0.7 + author_factor * 0.2 + doi_factor * 0.1)


class RecencyScorer:
    """Scores citation recency relative to current date."""
    
    def __init__(self):
        """Initialize with current year."""
        self._current_year = datetime.now().year
    
    def score(self, citation: Citation) -> float:
        """Score citation recency."""
        age = self._current_year - citation.year
        
        if age < 0:
            return 0.0  # Future dates are suspicious
        elif age <= 2:
            return 1.0  # Very recent
        elif age <= 5:
            return 0.8  # Recent
        elif age <= 10:
            return 0.6  # Moderately recent
        else:
            return max(0.2, 1.0 - (age - 10) * 0.02)  # Older papers


class AccessibilityScorer:
    """Scores citation accessibility based on availability indicators."""
    
    def score(self, citation: Citation) -> float:
        """Score citation accessibility."""
        score = 0.5  # Base score
        
        # DOI improves accessibility
        if citation.doi:
            score += 0.3
        
        # URL improves accessibility
        if citation.url:
            score += 0.2
        
        return min(score, 1.0)