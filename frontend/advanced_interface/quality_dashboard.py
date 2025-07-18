"""
Quality Assurance Dashboard
Implements bias detection, citation quality metrics, and research completeness analysis
Following Single Responsibility Principle and Interface Segregation Principle
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading
import statistics


@dataclass
class BiasResult:
    """Value object for bias detection results"""
    score: float
    confidence: float


@dataclass
class CitationMetrics:
    """Value object for citation metrics"""
    total_citations: int
    verified_citations: int
    high_quality_citations: int
    average_citation_age: float


@dataclass
class CompletenessAnalysis:
    """Value object for completeness analysis"""
    coverage_score: float
    identified_gaps: List[str]
    recommendations: List[str]


class QualityDashboard:
    """
    Quality assurance dashboard
    Adheres to Single Responsibility Principle - only manages quality metrics
    """
    
    def __init__(self):
        self._bias_results = {}
        self._citation_metrics = None
        self._completeness_analysis = None
        self._lock = threading.RLock()
    
    def update_bias_detection(self, bias_results: Dict[str, Dict[str, float]]) -> None:
        """Update bias detection results"""
        with self._lock:
            self._bias_results = {}
            for bias_type, data in bias_results.items():
                self._bias_results[bias_type] = BiasResult(
                    score=data["score"],
                    confidence=data["confidence"]
                )
    
    def get_bias_display(self) -> Dict[str, Dict[str, float]]:
        """Get bias detection display data"""
        with self._lock:
            display_data = {}
            for bias_type, result in self._bias_results.items():
                display_data[bias_type] = {
                    "score": result.score,
                    "confidence": result.confidence
                }
            return display_data
    
    def update_citation_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update citation quality metrics"""
        with self._lock:
            self._citation_metrics = CitationMetrics(
                total_citations=metrics["total_citations"],
                verified_citations=metrics["verified_citations"],
                high_quality_citations=metrics["high_quality_citations"],
                average_citation_age=metrics["average_citation_age"]
            )
    
    def get_citation_quality_score(self) -> float:
        """Calculate and return citation quality score"""
        with self._lock:
            if not self._citation_metrics:
                return 0.0
            
            metrics = self._citation_metrics
            
            # Calculate verification rate
            verification_rate = (metrics.verified_citations / metrics.total_citations 
                               if metrics.total_citations > 0 else 0)
            
            # Calculate high quality rate
            quality_rate = (metrics.high_quality_citations / metrics.total_citations 
                           if metrics.total_citations > 0 else 0)
            
            # Age factor (newer is better, but not too new)
            age_factor = max(0, 1 - (metrics.average_citation_age - 2) / 10)
            
            # Combined score
            quality_score = (verification_rate * 0.4 + quality_rate * 0.4 + age_factor * 0.2)
            
            return min(1.0, max(0.0, quality_score))
    
    def update_completeness_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """Update research completeness analysis"""
        with self._lock:
            self._completeness_analysis = CompletenessAnalysis(
                coverage_score=analysis_data["coverage_score"],
                identified_gaps=analysis_data["identified_gaps"],
                recommendations=analysis_data["recommendations"]
            )
    
    def get_completeness_analysis(self) -> Dict[str, Any]:
        """Get completeness analysis data"""
        with self._lock:
            if not self._completeness_analysis:
                return {}
            
            analysis = self._completeness_analysis
            return {
                "coverage_score": analysis.coverage_score,
                "identified_gaps": analysis.identified_gaps,
                "recommendations": analysis.recommendations
            }