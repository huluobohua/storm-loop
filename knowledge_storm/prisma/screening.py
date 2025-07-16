"""
Paper screening functionality for PRISMA systematic reviews.

Implements the 80/20 rule: automated screening for 80% of papers with 80% confidence,
leaving 20% for human review.
"""

import re
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Any
from .models import Paper, SearchStrategy, ScreeningResult

logger = logging.getLogger(__name__)


# Scoring weights and thresholds as named constants
class ScoringWeights:
    """Scoring weights for different components of inclusion score."""
    PICO_ALIGNMENT = 0.35
    STUDY_TYPE = 0.30
    METHODOLOGY = 0.25
    VENUE_QUALITY = 0.05
    RECENCY = 0.03
    CITATIONS = 0.02

class ConfidenceThresholds:
    """Confidence thresholds for decision making."""
    AUTO_INCLUDE = 0.8
    AUTO_EXCLUDE = 0.8
    HIGH_CONFIDENCE_EXCLUSION = 0.92
    MODERATE_CONFIDENCE = 0.6
    
class BoostFactors:
    """Multipliers for confidence boosting."""
    STRONG_SIGNALS_4_PLUS = 1.4
    STRONG_SIGNALS_3_PLUS = 1.25
    WEAK_SIGNALS_4_PLUS = 1.15
    HIGH_PICO_ALIGNMENT = 1.15
    STRONG_METHODOLOGY = 1.1

class QualityThresholds:
    """Quality thresholds for signals."""
    STRONG_SIGNAL = 0.1
    WEAK_SIGNAL = 0.05
    HIGH_PICO = 0.2
    STRONG_METHODOLOGY = 0.15


class ScreeningAssistant:
    """
    Targets 80/20 rule: Identify 80% of relevant sources, exclude 80% of irrelevant ones,
    with ~80% confidence. Remaining 20% goes to human review.
    """
    
    def __init__(self):
        # High-confidence exclusion patterns (>90% confidence)
        self.exclusion_patterns = {
            'wrong_population': [
                r'\b(animal|mice|mouse|rat|rats|bovine|canine|feline)\b',
                r'\b(in vitro|cell line|cell culture)\b(?!.*\bhuman\b)',
                r'\b(zebrafish|drosophila|c\. elegans|yeast)\b'
            ],
            'wrong_study_type': [
                r'^(editorial|comment|letter to|opinion|book review)',
                r'\b(conference abstract|poster presentation)\b',
                r'erratum|correction|retraction',
                r'^(news|interview|biography)'
            ],
            'wrong_language': [
                r'(chinese|spanish|french|german|japanese) language',
                r'not available in english',
                r'non-english article'
            ],
            'duplicate': [
                r'duplicate publication',
                r'previously published',
                r'republished from'
            ]
        }
        
        # High-confidence inclusion indicators
        self.inclusion_indicators = {
            'study_type': [
                r'\b(randomized controlled trial|RCT)\b',
                r'\b(systematic review|meta-analysis)\b',
                r'\b(cohort study|prospective study)\b',
                r'\b(case-control study)\b',
                r'\b(cross-sectional study)\b'
            ],
            'methodology': [
                r'\b(participants?|subjects?|patients?)\s+were\s+(recruited|enrolled|included)',
                r'\b(sample size|n\s*=\s*\d+)\b',
                r'\b(statistical analysis|regression|correlation)\b',
                r'\b(primary outcome|secondary outcome)\b'
            ],
            'quality_indicators': [
                r'\b(double-blind|triple-blind|single-blind)\b',
                r'\b(intention-to-treat|per-protocol)\b',
                r'\b(confidence interval|CI\s*95%|p\s*[<=]\s*0\.0\d+)\b',
                r'\b(ethics approval|institutional review board|IRB)\b'
            ]
        }
    
    async def screen_papers(self, papers: List[Paper], 
                          criteria: SearchStrategy) -> Dict[str, Any]:
        """
        Screen papers targeting 80/20 rule:
        - Identify ~80% of relevant papers with high confidence
        - Exclude ~80% of irrelevant papers with high confidence
        - Leave ~20% for human review where confidence is lower
        """
        results = {
            'definitely_exclude': [],
            'definitely_include': [],
            'needs_human_review': [],
            'exclusion_stats': defaultdict(int),
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'performance_metrics': {}
        }
        
        # Track for 80/20 metrics
        total_papers = len(papers)
        confidence_threshold_include = ConfidenceThresholds.AUTO_INCLUDE
        confidence_threshold_exclude = ConfidenceThresholds.AUTO_EXCLUDE
        
        for paper in papers:
            decision, reason, confidence = self._screen_single_paper(paper, criteria)
            
            paper.screening_decision = decision
            paper.exclusion_reason = reason
            paper.confidence_score = confidence
            
            # Apply 80% confidence thresholds
            if decision == 'exclude' and confidence >= confidence_threshold_exclude:
                results['definitely_exclude'].append(paper)
                results['exclusion_stats'][reason] += 1
                results['confidence_distribution']['high'] += 1
            elif decision == 'include' and confidence >= confidence_threshold_include:
                results['definitely_include'].append(paper)
                results['confidence_distribution']['high'] += 1
            else:
                results['needs_human_review'].append(paper)
                if confidence >= 0.6:
                    results['confidence_distribution']['medium'] += 1
                else:
                    results['confidence_distribution']['low'] += 1
        
        # Calculate 80/20 performance metrics
        auto_decided = len(results['definitely_exclude']) + len(results['definitely_include'])
        auto_decision_rate = auto_decided / total_papers if total_papers > 0 else 0
        
        results['performance_metrics'] = {
            'total_papers': total_papers,
            'auto_decided': auto_decided,
            'auto_decision_rate': auto_decision_rate,
            'human_review_rate': len(results['needs_human_review']) / total_papers if total_papers > 0 else 0,
            'target_achieved': auto_decision_rate >= 0.8,
            'confidence_threshold': confidence_threshold_include
        }
        
        # Log screening summary with 80/20 metrics
        logger.info(f"Screening complete (80/20 target):")
        logger.info(f"  - Auto-excluded: {len(results['definitely_exclude'])} ({len(results['definitely_exclude'])/total_papers*100:.1f}%)")
        logger.info(f"  - Auto-included: {len(results['definitely_include'])} ({len(results['definitely_include'])/total_papers*100:.1f}%)")
        logger.info(f"  - Human review: {len(results['needs_human_review'])} ({len(results['needs_human_review'])/total_papers*100:.1f}%)")
        logger.info(f"  - Auto-decision rate: {auto_decision_rate:.1%} (target: 80%)")
        
        return results
    
    def _screen_single_paper(self, paper: Paper, 
                           criteria: SearchStrategy) -> Tuple[str, str, float]:
        """
        Screen a single paper with sophisticated confidence scoring.
        Targets 80% confidence threshold for automated decisions.
        """
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Check high-confidence exclusions first
        exclusion_confidence = 0.0
        exclusion_reason = None
        
        for reason, patterns in self.exclusion_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.I):
                    # High confidence exclusion (90-95%)
                    exclusion_confidence = 0.92
                    exclusion_reason = reason
                    
                    # Check for exceptions that might lower confidence
                    if reason == 'wrong_population' and 'human' in text:
                        exclusion_confidence = 0.75  # Could be comparative study
                    elif reason == 'wrong_study_type' and any(term in text for term in ['systematic', 'meta-analysis', 'review']):
                        exclusion_confidence = 0.70  # Might reference these in abstract
                    
                    if exclusion_confidence >= ConfidenceThresholds.AUTO_EXCLUDE:
                        return 'exclude', exclusion_reason, exclusion_confidence
        
        # Calculate sophisticated inclusion score
        inclusion_confidence = self._calculate_advanced_inclusion_score(paper, criteria)
        
        # Determine decision based on confidence levels
        if inclusion_confidence >= ConfidenceThresholds.AUTO_INCLUDE:
            return 'include', 'high_relevance', inclusion_confidence
        elif exclusion_confidence >= ConfidenceThresholds.MODERATE_CONFIDENCE:
            return 'exclude', exclusion_reason or 'low_relevance', exclusion_confidence
        elif inclusion_confidence >= ConfidenceThresholds.MODERATE_CONFIDENCE:
            return 'maybe', 'moderate_relevance', inclusion_confidence
        else:
            # Low confidence - needs human review
            confidence = max(inclusion_confidence, exclusion_confidence)
            return 'maybe', 'unclear_relevance', confidence
    
    def _calculate_inclusion_score(self, paper: Paper, criteria: SearchStrategy) -> float:
        """Calculate basic inclusion score - kept for backward compatibility."""
        return self._calculate_advanced_inclusion_score(paper, criteria)
    
    def _calculate_advanced_inclusion_score(self, paper: Paper, criteria: SearchStrategy) -> float:
        """
        Advanced inclusion scoring targeting 80% confidence threshold.
        Uses multiple signals to achieve reliable automated decisions.
        """
        text = f"{paper.title} {paper.abstract}".lower()
        scores = {}
        
        # Calculate individual scoring components
        scores['pico'] = self._calculate_pico_alignment_score(text, criteria)
        scores['study_type'] = self._calculate_study_type_score(text)
        scores['methodology'] = self._calculate_methodology_score(text)
        scores['venue'] = self._calculate_venue_quality_score(paper)
        scores['recency'] = self._calculate_recency_score(paper)
        scores['citations'] = self._calculate_citation_score(text, paper)
        
        # Calculate base score
        total_score = sum(scores.values())
        
        # Apply confidence boosting based on signal strength
        boosted_score = self._apply_confidence_boosting(total_score, scores)
        
        # Ensure score is between 0 and 1
        return min(max(boosted_score, 0.0), 1.0)
    
    def _calculate_pico_alignment_score(self, text: str, criteria: SearchStrategy) -> float:
        """Calculate PICO alignment score component."""
        pico_matches = 0
        pico_total = 0
        
        for element, terms in criteria.pico_elements.items():
            if terms:
                pico_total += len(terms)
                # Check for exact and fuzzy matches
                for term in terms:
                    if term.lower() in text:
                        pico_matches += 1.0
                    elif any(word in text for word in term.lower().split()):
                        pico_matches += 0.5  # Partial credit for partial matches
        
        return (pico_matches / pico_total * ScoringWeights.PICO_ALIGNMENT) if pico_total > 0 else 0
    
    def _calculate_study_type_score(self, text: str) -> float:
        """Calculate study type indicators score component."""
        study_type_score = 0
        for indicator_type, patterns in self.inclusion_indicators.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text, re.I))
            if matches > 0:
                study_type_score = max(study_type_score, matches / len(patterns))
        return study_type_score * ScoringWeights.STUDY_TYPE
    
    def _calculate_methodology_score(self, text: str) -> float:
        """Calculate methodological rigor score component."""
        # Methodology indicators with individual weights
        method_indicators = [
            (r'\b(sample size|n\s*=\s*\d+)\b', 0.15),
            (r'\b(statistical|significance|p\s*[<=]\s*0\.\d+)\b', 0.15),
            (r'\b(randomized|controlled|prospective|retrospective)\b', 0.15),
            (r'\b(inclusion criteria|exclusion criteria)\b', 0.1),
            (r'\b(primary outcome|secondary outcome)\b', 0.15),
            (r'\b(confidence interval|95%\s*CI)\b', 0.1),
            (r'\b(ethics|ethical approval|consent)\b', 0.1),
            (r'\b(limitations|bias|confounding)\b', 0.1)
        ]
        
        method_score = sum(weight for pattern, weight in method_indicators 
                          if re.search(pattern, text, re.I))
        return min(method_score, 1.0) * ScoringWeights.METHODOLOGY
    
    def _calculate_venue_quality_score(self, paper: Paper) -> float:
        """Calculate journal/venue quality score component."""
        venue_score = 0
        if paper.journal:
            journal_lower = paper.journal.lower()
            if any(term in journal_lower for term in ['nature', 'science', 'lancet', 'jama', 'bmj', 'nejm']):
                venue_score = 1.0
            elif any(term in journal_lower for term in ['plos', 'ieee', 'acm', 'springer', 'elsevier']):
                venue_score = 0.8
            elif 'journal' in journal_lower:
                venue_score = 0.6
        return venue_score * ScoringWeights.VENUE_QUALITY
    
    def _calculate_recency_score(self, paper: Paper) -> float:
        """Calculate publication recency score component."""
        recency_score = 0
        if paper.year:
            current_year = datetime.now().year
            if paper.year >= current_year - 2:
                recency_score = 1.0
            elif paper.year >= current_year - 5:
                recency_score = 0.8
            elif paper.year >= current_year - 10:
                recency_score = 0.5
        return recency_score * ScoringWeights.RECENCY
    
    def _calculate_citation_score(self, text: str, paper: Paper) -> float:
        """Calculate citation indicators score component."""
        citation_score = 0
        if paper.doi or '[' in text or 'reference' in text:
            citation_score = 0.5
        if re.search(r'\b\d{4}\b.*\b\d{4}\b.*\b\d{4}\b', text):  # Multiple years cited
            citation_score = 1.0
        return citation_score * ScoringWeights.CITATIONS
    
    def _apply_confidence_boosting(self, base_score: float, scores: Dict[str, float]) -> float:
        """Apply confidence boosting based on signal strength."""
        # Count strong and weak signals
        strong_signals = sum(1 for s in scores.values() if s > QualityThresholds.STRONG_SIGNAL)
        weak_signals = sum(1 for s in scores.values() if s > QualityThresholds.WEAK_SIGNAL)
        
        # Progressive confidence boosting
        if strong_signals >= 4:
            base_score = min(base_score * BoostFactors.STRONG_SIGNALS_4_PLUS, 1.0)
        elif strong_signals >= 3:
            base_score = min(base_score * BoostFactors.STRONG_SIGNALS_3_PLUS, 1.0)
        elif weak_signals >= 4:
            base_score = min(base_score * BoostFactors.WEAK_SIGNALS_4_PLUS, 1.0)
        
        # Additional boost for high PICO alignment
        if scores.get('pico', 0) > QualityThresholds.HIGH_PICO:
            base_score = min(base_score * BoostFactors.HIGH_PICO_ALIGNMENT, 1.0)
            
        # Boost for strong methodology signals
        if scores.get('methodology', 0) > QualityThresholds.STRONG_METHODOLOGY:
            base_score = min(base_score * BoostFactors.STRONG_METHODOLOGY, 1.0)
        
        return base_score


class PRISMAScreener:
    """
    Interface wrapper for PRISMA Assistant that matches the expected API.
    Provides simplified screening interface for CLI integration.
    """
    
    def __init__(self, include_patterns=None, exclude_patterns=None, threshold=0.8):
        """Initialize screener with patterns and confidence threshold."""
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.threshold = threshold
        self.screening_assistant = ScreeningAssistant()
    
    async def screen_papers(self, papers: List[Paper]) -> Dict[str, Any]:
        """Screen papers using the screening assistant."""
        # Create a basic search strategy for screening
        search_strategy = SearchStrategy(
            research_question="Screening based on provided patterns",
            pico_elements={
                'population': self.include_patterns[:3] if self.include_patterns else [],
                'intervention': [],
                'comparison': [],
                'outcome': []
            },
            search_queries={},
            inclusion_criteria=self.include_patterns,
            exclusion_criteria=self.exclude_patterns
        )
        
        return await self.screening_assistant.screen_papers(papers, search_strategy)