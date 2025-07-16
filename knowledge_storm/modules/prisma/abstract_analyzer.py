"""
Abstract Analysis Module for PRISMA Data Extraction.

Specialized module for analyzing research paper abstracts to extract
study characteristics, sample sizes, and other key information.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .core import Paper


@dataclass
class AbstractAnalysisResult:
    """Result of abstract analysis."""
    sample_size: Optional[int] = None
    study_design: Optional[str] = None
    study_indicators: List[str] = None
    outcome_measures: List[str] = None
    analysis_summary: str = ""
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.study_indicators is None:
            self.study_indicators = []
        if self.outcome_measures is None:
            self.outcome_measures = []


class AbstractAnalyzer:
    """
    Specialized analyzer for research paper abstracts.
    
    Extracts study characteristics, sample sizes, design types,
    and outcome measures from abstract text using pattern matching
    and domain-specific heuristics.
    """
    
    def __init__(self):
        """Initialize the analyzer with predefined patterns."""
        self.sample_size_patterns = [
            r'n\s*=?\s*(\d+)',
            r'(\d+)\s+participants?',
            r'(\d+)\s+subjects?',
            r'(\d+)\s+patients?',
            r'sample\s+size\s*:?\s*(\d+)',
            r'total\s+of\s+(\d+)'
        ]
        
        self.study_design_patterns = {
            'randomized_controlled_trial': [
                r'randomized controlled trial',
                r'\brct\b',
                r'randomized\s+clinical\s+trial',
                r'randomized\s+trial'
            ],
            'cohort_study': [
                r'cohort\s+study',
                r'prospective\s+cohort',
                r'retrospective\s+cohort',
                r'longitudinal\s+study'
            ],
            'case_control': [
                r'case.?control\s+study',
                r'case.?control\s+design',
                r'matched\s+case.?control'
            ],
            'cross_sectional': [
                r'cross.?sectional\s+study',
                r'cross.?sectional\s+design',
                r'survey\s+study'
            ],
            'systematic_review': [
                r'systematic\s+review',
                r'meta.?analysis',
                r'literature\s+review'
            ],
            'case_series': [
                r'case\s+series',
                r'case\s+report',
                r'case\s+study'
            ]
        }
        
        self.outcome_measure_patterns = {
            'pain': [
                r'\bpain\b',
                r'pain\s+score',
                r'visual\s+analog\s+scale',
                r'vas\s+score',
                r'numeric\s+rating\s+scale'
            ],
            'quality_of_life': [
                r'quality\s+of\s+life',
                r'qol\s+score',
                r'sf.?36',
                r'eq.?5d'
            ],
            'functional_outcome': [
                r'functional\s+outcome',
                r'disability\s+index',
                r'functional\s+assessment',
                r'activity\s+limitation'
            ],
            'mortality': [
                r'mortality',
                r'death\s+rate',
                r'survival',
                r'mortality\s+rate'
            ],
            'adverse_events': [
                r'adverse\s+events?',
                r'side\s+effects?',
                r'complications?',
                r'safety\s+outcomes?'
            ]
        }
    
    def analyze_abstract(self, paper: Paper) -> AbstractAnalysisResult:
        """
        Analyze paper abstract to extract study characteristics.
        
        Args:
            paper: Paper object containing abstract text
            
        Returns:
            AbstractAnalysisResult with extracted information
        """
        if not paper.abstract:
            return AbstractAnalysisResult(
                analysis_summary=f"No abstract available for {paper.title}",
                confidence_score=0.0
            )
        
        abstract_text = paper.abstract.lower()
        result = AbstractAnalysisResult()
        
        # Extract sample size
        result.sample_size = self._extract_sample_size(abstract_text)
        
        # Identify study design
        result.study_design = self._identify_study_design(abstract_text)
        if result.study_design:
            result.study_indicators.append(result.study_design)
        
        # Extract outcome measures
        result.outcome_measures = self._extract_outcome_measures(abstract_text)
        
        # Generate analysis summary
        result.analysis_summary = self._generate_analysis_summary(result)
        
        # Calculate confidence score
        result.confidence_score = self._calculate_confidence_score(result, paper)
        
        return result
    
    def _extract_sample_size(self, abstract_text: str) -> Optional[int]:
        """Extract sample size from abstract text."""
        for pattern in self.sample_size_patterns:
            match = re.search(pattern, abstract_text, re.IGNORECASE)
            if match:
                try:
                    # Get the first capturing group that contains digits
                    for group in match.groups():
                        if group and group.isdigit():
                            sample_size = int(group)
                            # Validate reasonable sample size (between 1 and 1,000,000)
                            if 1 <= sample_size <= 1000000:
                                return sample_size
                except ValueError:
                    continue
        return None
    
    def _identify_study_design(self, abstract_text: str) -> Optional[str]:
        """Identify study design from abstract text."""
        for design_type, patterns in self.study_design_patterns.items():
            for pattern in patterns:
                if re.search(pattern, abstract_text, re.IGNORECASE):
                    return design_type
        return None
    
    def _extract_outcome_measures(self, abstract_text: str) -> List[str]:
        """Extract outcome measures from abstract text."""
        found_measures = []
        
        for measure_type, patterns in self.outcome_measure_patterns.items():
            for pattern in patterns:
                if re.search(pattern, abstract_text, re.IGNORECASE):
                    found_measures.append(measure_type)
                    break  # Only add each measure type once
        
        return found_measures
    
    def _generate_analysis_summary(self, result: AbstractAnalysisResult) -> str:
        """Generate human-readable analysis summary."""
        summary_parts = []
        
        if result.sample_size:
            summary_parts.append(f"sample size: {result.sample_size}")
        
        if result.study_design:
            summary_parts.append(result.study_design.replace('_', ' '))
        
        if result.outcome_measures:
            summary_parts.extend(result.outcome_measures)
        
        if summary_parts:
            return f"Analysis extracted: {', '.join(summary_parts)}"
        else:
            return "Contains study information"
    
    def _calculate_confidence_score(self, result: AbstractAnalysisResult, paper: Paper) -> float:
        """Calculate confidence score based on extracted information."""
        confidence = 0.0
        
        # Base confidence for having an abstract
        if paper.abstract:
            confidence += 0.3
        
        # Add confidence for extracted elements
        if result.sample_size:
            confidence += 0.3
        
        if result.study_design:
            confidence += 0.2
        
        if result.outcome_measures:
            confidence += 0.1 * min(len(result.outcome_measures), 2)  # Max 0.2 for outcomes
        
        # Additional confidence for longer abstracts (more information)
        if paper.abstract and len(paper.abstract) > 200:
            confidence += 0.1
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def get_supported_study_designs(self) -> List[str]:
        """Get list of supported study design types."""
        return list(self.study_design_patterns.keys())
    
    def get_supported_outcome_measures(self) -> List[str]:
        """Get list of supported outcome measure types."""
        return list(self.outcome_measure_patterns.keys())


# Export classes
__all__ = ['AbstractAnalyzer', 'AbstractAnalysisResult']