"""
Quality Scorer

Orchestrates citation quality assessment using focused components.
Provides comprehensive scoring by coordinating specialized scorers.
"""

from typing import Dict, Optional
from .models import Citation
from .quality_components import (
    RelevanceScorer, AuthorityScorer, RecencyScorer, AccessibilityScorer
)


class QualityScorer:
    """
    Orchestrates citation quality scoring.
    
    Coordinates specialized scoring components.
    Single responsibility: quality score coordination.
    """
    
    def __init__(self):
        """Initialize scoring components."""
        self._relevance = RelevanceScorer()
        self._authority = AuthorityScorer()
        self._recency = RecencyScorer()
        self._accessibility = AccessibilityScorer()
    
    def score_citation(self, citation: Citation, context: Optional[str] = None) -> Dict[str, float]:
        """Calculate comprehensive quality score for citation."""
        scores = {
            'relevance_score': self._relevance.score(citation, context),
            'authority_score': self._authority.score(citation),
            'recency_score': self._recency.score(citation),
            'accessibility_score': self._accessibility.score(citation)
        }
        
        scores['overall_score'] = self._calculate_overall(scores)
        return scores
    
    def _calculate_overall(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            'relevance_score': 0.3,
            'authority_score': 0.4,
            'recency_score': 0.2,
            'accessibility_score': 0.1
        }
        
        overall = sum(
            scores[metric] * weight 
            for metric, weight in weights.items()
            if metric in scores
        )
        
        return min(overall, 1.0)
    
    def score_bibliography(self, citations: list, context: Optional[str] = None) -> Dict[str, float]:
        """Score entire bibliography quality."""
        if not citations:
            return {
                'average_quality': 0.0,
                'quality_variance': 0.0,
                'low_quality_count': 0,
                'high_quality_count': 0
            }
        
        scores = [
            self.score_citation(citation, context)['overall_score']
            for citation in citations
        ]
        
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        
        low_quality = sum(1 for s in scores if s < 0.3)
        high_quality = sum(1 for s in scores if s >= 0.7)
        
        return {
            'average_quality': avg_score,
            'quality_variance': variance,
            'low_quality_count': low_quality,
            'high_quality_count': high_quality,
            'total_citations': len(citations)
        }