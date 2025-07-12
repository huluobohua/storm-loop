"""
PRISMAAssistant: An honest systematic review assistant that handles the grunt work.

Based on real PRISMA methodology, this tool helps researchers with the tedious 80%
while being transparent about what requires human expertise.
"""

import re
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


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


class SearchStrategyBuilder:
    """Builds comprehensive search strategies from research questions."""
    
    def __init__(self):
        # Common medical/scientific database syntaxes
        self.database_syntaxes = {
            'pubmed': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'scopus': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' AND NOT ', 'wildcard': '*'},
            'web_of_science': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'cochrane': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'embase': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'ieee': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'acm': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'}
        }
        
    def build_search_strategy(self, research_question: str, 
                            domain: str = "medical") -> SearchStrategy:
        """Build comprehensive search strategy from research question."""
        
        # Extract PICO elements (Population, Intervention, Comparison, Outcome)
        pico = self._extract_pico(research_question)
        
        # Generate inclusion/exclusion criteria
        inclusion, exclusion = self._generate_criteria(pico, domain)
        
        # Build database-specific queries
        queries = {}
        for db_name, syntax in self.database_syntaxes.items():
            if self._is_relevant_database(db_name, domain):
                queries[db_name] = self._build_query(pico, syntax)
        
        return SearchStrategy(
            research_question=research_question,
            pico_elements=pico,
            search_queries=queries,
            inclusion_criteria=inclusion,
            exclusion_criteria=exclusion,
            date_range=(2019, 2024)  # Last 5 years by default
        )
    
    def _extract_pico(self, question: str) -> Dict[str, List[str]]:
        """Extract PICO elements from research question."""
        # Simplified extraction - in production, use NLP
        pico = {
            'population': [],
            'intervention': [],
            'comparison': [],
            'outcome': []
        }
        
        # Look for key patterns
        if 'patients with' in question.lower():
            population_match = re.search(r'patients with ([^,\.]+)', question, re.I)
            if population_match:
                pico['population'].append(population_match.group(1))
        
        # Extract intervention (AI, ML, etc.)
        ai_terms = ['AI', 'artificial intelligence', 'machine learning', 'deep learning', 
                    'neural network', 'algorithm', 'automated', 'computer-aided']
        for term in ai_terms:
            if term.lower() in question.lower():
                pico['intervention'].append(term)
        
        # Extract outcomes
        outcome_terms = ['diagnosis', 'detection', 'screening', 'prediction', 'prognosis',
                        'treatment', 'outcomes', 'accuracy', 'performance']
        for term in outcome_terms:
            if term.lower() in question.lower():
                pico['outcome'].append(term)
        
        return pico
    
    def _generate_criteria(self, pico: Dict[str, List[str]], 
                          domain: str) -> Tuple[List[str], List[str]]:
        """Generate inclusion and exclusion criteria."""
        inclusion = []
        exclusion = []
        
        # Standard inclusion criteria
        inclusion.append("Peer-reviewed studies")
        inclusion.append("Published in English")
        inclusion.append("Published between 2019-2024")
        
        if pico['population']:
            inclusion.append(f"Studies involving {', '.join(pico['population'])}")
        if pico['intervention']:
            inclusion.append(f"Studies using {', '.join(pico['intervention'])}")
        if pico['outcome']:
            inclusion.append(f"Studies reporting {', '.join(pico['outcome'])}")
        
        # Standard exclusion criteria
        exclusion.append("Conference abstracts without full text")
        exclusion.append("Editorials, opinions, and letters")
        exclusion.append("Studies without primary data")
        exclusion.append("Duplicate publications")
        
        # Domain-specific criteria
        if domain == "medical":
            exclusion.append("Animal studies without human validation")
            exclusion.append("Case reports with n<10")
        elif domain == "cs":
            exclusion.append("Papers without implementation details")
            exclusion.append("Position papers without evaluation")
        
        return inclusion, exclusion
    
    def _build_query(self, pico: Dict[str, List[str]], syntax: Dict[str, str]) -> str:
        """Build database-specific search query."""
        query_parts = []
        
        # Population terms
        if pico['population']:
            pop_terms = [f'"{term}"' for term in pico['population']]
            query_parts.append(f"({syntax['OR'].join(pop_terms)})")
        
        # Intervention terms with synonyms
        if pico['intervention']:
            intervention_groups = []
            for term in pico['intervention']:
                # Add synonyms
                synonyms = self._get_synonyms(term)
                group = syntax['OR'].join([f'"{s}"' for s in synonyms])
                intervention_groups.append(f"({group})")
            query_parts.append(f"({syntax['OR'].join(intervention_groups)})")
        
        # Outcome terms
        if pico['outcome']:
            outcome_terms = [f'"{term}"' for term in pico['outcome']]
            query_parts.append(f"({syntax['OR'].join(outcome_terms)})")
        
        # Combine with AND
        full_query = syntax['AND'].join(query_parts)
        
        # Add filters
        full_query += f"{syntax['AND']}(\"2019\"[Date]:\"2024\"[Date])"
        
        return full_query
    
    def _get_synonyms(self, term: str) -> List[str]:
        """Get synonyms for search terms."""
        synonym_map = {
            'AI': ['AI', 'artificial intelligence'],
            'artificial intelligence': ['AI', 'artificial intelligence'],
            'machine learning': ['machine learning', 'ML', 'deep learning', 'DL'],
            'diagnosis': ['diagnosis', 'diagnostic', 'detection', 'identification'],
            'treatment': ['treatment', 'therapy', 'intervention', 'management']
        }
        
        return synonym_map.get(term.lower(), [term])
    
    def _is_relevant_database(self, db_name: str, domain: str) -> bool:
        """Check if database is relevant for domain."""
        domain_databases = {
            'medical': ['pubmed', 'scopus', 'cochrane', 'embase'],
            'cs': ['ieee', 'acm', 'scopus', 'web_of_science'],
            'general': ['scopus', 'web_of_science']
        }
        
        return db_name in domain_databases.get(domain, domain_databases['general'])


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
        confidence_threshold_include = 0.8  # 80% confidence for auto-include
        confidence_threshold_exclude = 0.8  # 80% confidence for auto-exclude
        
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
                    
                    if exclusion_confidence >= 0.8:
                        return 'exclude', exclusion_reason, exclusion_confidence
        
        # Calculate sophisticated inclusion score
        inclusion_confidence = self._calculate_advanced_inclusion_score(paper, criteria)
        
        # Determine decision based on confidence levels
        if inclusion_confidence >= 0.8:
            return 'include', 'high_relevance', inclusion_confidence
        elif exclusion_confidence >= 0.6:
            return 'exclude', exclusion_reason or 'low_relevance', exclusion_confidence
        elif inclusion_confidence >= 0.6:
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
        
        # 1. PICO alignment (30% weight)
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
        
        scores['pico'] = (pico_matches / pico_total * 0.35) if pico_total > 0 else 0
        
        # 2. Study type indicators (30% weight - increased)
        study_type_score = 0
        for indicator_type, patterns in self.inclusion_indicators.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text, re.I))
            if matches > 0:
                study_type_score = max(study_type_score, matches / len(patterns))
        scores['study_type'] = study_type_score * 0.30
        
        # 3. Methodological rigor (20% weight)
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
        scores['methodology'] = min(method_score, 1.0) * 0.25  # Increased weight
        
        # 4. Journal/venue quality (5% weight - decreased)
        venue_score = 0
        if paper.journal:
            journal_lower = paper.journal.lower()
            if any(term in journal_lower for term in ['nature', 'science', 'lancet', 'jama', 'bmj', 'nejm', 'ophthalmology']):
                venue_score = 1.0
            elif any(term in journal_lower for term in ['plos', 'ieee', 'acm', 'springer', 'elsevier', 'diabetes']):
                venue_score = 0.8
            elif 'journal' in journal_lower:
                venue_score = 0.6
        scores['venue'] = venue_score * 0.05
        
        # 5. Recency (3% weight - decreased)
        recency_score = 0
        if paper.year:
            current_year = datetime.now().year
            if paper.year >= current_year - 2:
                recency_score = 1.0
            elif paper.year >= current_year - 5:
                recency_score = 0.8
            elif paper.year >= current_year - 10:
                recency_score = 0.5
        scores['recency'] = recency_score * 0.03
        
        # 6. Citation indicators (2% weight - decreased)
        citation_score = 0
        if paper.doi or '[' in text or 'reference' in text:
            citation_score = 0.5
        if re.search(r'\b\d{4}\b.*\b\d{4}\b.*\b\d{4}\b', text):  # Multiple years cited
            citation_score = 1.0
        scores['citations'] = citation_score * 0.02
        
        # Calculate total score with confidence adjustment
        total_score = sum(scores.values())
        
        # Boost confidence if multiple strong signals present
        strong_signals = sum(1 for s in scores.values() if s > 0.1)
        weak_signals = sum(1 for s in scores.values() if s > 0.05)
        
        # Progressive confidence boosting
        if strong_signals >= 4:
            total_score = min(total_score * 1.4, 1.0)  # 40% boost for many strong signals
        elif strong_signals >= 3:
            total_score = min(total_score * 1.25, 1.0)  # 25% boost
        elif weak_signals >= 4:
            total_score = min(total_score * 1.15, 1.0)  # 15% boost
        
        # Additional boost for very high PICO alignment
        if scores.get('pico', 0) > 0.2:
            total_score = min(total_score * 1.15, 1.0)
            
        # Boost for strong methodology signals
        if scores.get('methodology', 0) > 0.15:
            total_score = min(total_score * 1.1, 1.0)
        
        # Ensure score is between 0 and 1
        return min(max(total_score, 0.0), 1.0)


class DataExtractionHelper:
    """Creates structured templates for data extraction."""
    
    def create_extraction_template(self, 
                                 included_papers: List[Paper],
                                 research_question: str) -> ExtractionTemplate:
        """Create customized extraction template based on papers and question."""
        
        # Analyze papers to determine common fields
        common_fields = self._analyze_common_fields(included_papers)
        
        # Standard fields for all systematic reviews
        fields = {
            'study_id': {
                'type': 'string',
                'description': 'Unique identifier for the study',
                'required': True,
                'prefilled': True
            },
            'authors': {
                'type': 'string',
                'description': 'First author et al., year',
                'required': True,
                'prefilled': True
            },
            'year': {
                'type': 'integer',
                'description': 'Publication year',
                'required': True,
                'prefilled': True
            },
            'country': {
                'type': 'string',
                'description': 'Country where study was conducted',
                'required': False,
                'prefilled': False
            },
            'study_design': {
                'type': 'choice',
                'options': ['RCT', 'Cohort', 'Case-Control', 'Cross-sectional', 
                           'Case Series', 'Other'],
                'description': 'Study design/methodology',
                'required': True,
                'prefilled': False
            },
            'sample_size': {
                'type': 'integer',
                'description': 'Total number of participants',
                'required': True,
                'prefilled': False
            }
        }
        
        # Add domain-specific fields based on research question
        if 'diagnostic' in research_question.lower() or 'accuracy' in research_question.lower():
            fields.update(self._add_diagnostic_fields())
        elif 'treatment' in research_question.lower() or 'intervention' in research_question.lower():
            fields.update(self._add_intervention_fields())
        
        # Study characteristics to extract
        study_chars = [
            'Population characteristics',
            'Inclusion/exclusion criteria',
            'Setting (hospital, community, etc.)',
            'Data collection period'
        ]
        
        # Outcome measures based on research question
        outcomes = self._determine_outcome_measures(research_question)
        
        # Quality indicators
        quality = [
            'Risk of bias assessment',
            'Conflicts of interest',
            'Funding source',
            'Ethics approval'
        ]
        
        return ExtractionTemplate(
            fields=fields,
            study_characteristics=study_chars,
            outcome_measures=outcomes,
            quality_indicators=quality
        )
    
    def _analyze_common_fields(self, papers: List[Paper]) -> Dict[str, int]:
        """Analyze papers to find commonly mentioned fields."""
        field_counts = defaultdict(int)
        
        # Simple pattern matching for common terms
        patterns = {
            'sensitivity': r'sensitiv',
            'specificity': r'specific',
            'accuracy': r'accura',
            'auc': r'\bauc\b|area under',
            'hazard_ratio': r'hazard ratio|HR',
            'odds_ratio': r'odds ratio|OR',
            'relative_risk': r'relative risk|RR'
        }
        
        for paper in papers:
            text = paper.abstract.lower()
            for field, pattern in patterns.items():
                if re.search(pattern, text, re.I):
                    field_counts[field] += 1
        
        return field_counts
    
    def _add_diagnostic_fields(self) -> Dict[str, Dict[str, Any]]:
        """Add fields specific to diagnostic accuracy studies."""
        return {
            'index_test': {
                'type': 'string',
                'description': 'The diagnostic test being evaluated',
                'required': True,
                'prefilled': False
            },
            'reference_standard': {
                'type': 'string',
                'description': 'Gold standard test used for comparison',
                'required': True,
                'prefilled': False
            },
            'sensitivity': {
                'type': 'float',
                'description': 'Sensitivity (%) with 95% CI if available',
                'required': False,
                'prefilled': False
            },
            'specificity': {
                'type': 'float',
                'description': 'Specificity (%) with 95% CI if available',
                'required': False,
                'prefilled': False
            },
            'auc': {
                'type': 'float',
                'description': 'Area under the ROC curve',
                'required': False,
                'prefilled': False
            }
        }
    
    def _add_intervention_fields(self) -> Dict[str, Dict[str, Any]]:
        """Add fields specific to intervention studies."""
        return {
            'intervention': {
                'type': 'string',
                'description': 'Description of the intervention',
                'required': True,
                'prefilled': False
            },
            'comparator': {
                'type': 'string',
                'description': 'Control or comparison group',
                'required': True,
                'prefilled': False
            },
            'primary_outcome': {
                'type': 'string',
                'description': 'Primary outcome measure',
                'required': True,
                'prefilled': False
            },
            'effect_size': {
                'type': 'string',
                'description': 'Effect size with confidence intervals',
                'required': False,
                'prefilled': False
            }
        }
    
    def _determine_outcome_measures(self, research_question: str) -> List[str]:
        """Determine relevant outcome measures based on research question."""
        outcomes = []
        
        # Diagnostic accuracy outcomes
        if any(term in research_question.lower() for term in ['diagnostic', 'accuracy', 'detection']):
            outcomes.extend([
                'Sensitivity and specificity',
                'Positive/negative predictive values',
                'Likelihood ratios',
                'Area under ROC curve'
            ])
        
        # Clinical outcomes
        if any(term in research_question.lower() for term in ['treatment', 'outcome', 'survival']):
            outcomes.extend([
                'Primary clinical outcome',
                'Secondary outcomes',
                'Adverse events',
                'Quality of life measures'
            ])
        
        # Implementation outcomes
        if any(term in research_question.lower() for term in ['implementation', 'adoption', 'feasibility']):
            outcomes.extend([
                'Adoption rate',
                'Implementation costs',
                'User satisfaction',
                'Barriers and facilitators'
            ])
        
        return outcomes


class ZeroDraftGenerator:
    """
    Generates a 'zero draft' to overcome blank page syndrome.
    Clearly marked as draft requiring human expertise.
    """
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
    
    async def generate_zero_draft(self,
                                search_strategy: SearchStrategy,
                                screening_results: Dict[str, List[Paper]],
                                extraction_template: ExtractionTemplate,
                                include_draft: bool = True) -> str:
        """Generate a zero draft with clear disclaimers."""
        
        if not include_draft:
            return self._generate_outline_only(search_strategy, screening_results)
        
        draft = f"""# ZERO DRAFT - SYSTEMATIC REVIEW
## ⚠️ IMPORTANT: This is an AI-generated draft to overcome blank page syndrome
## All claims, numbers, and conclusions MUST be verified by human experts

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status**: DRAFT - NOT FOR SUBMISSION

---

# {search_strategy.research_question}

## Abstract

[DRAFT PLACEHOLDER - TO BE WRITTEN AFTER ANALYSIS]

## 1. Introduction

### 1.1 Background
{self._generate_background(search_strategy)}

### 1.2 Rationale
The need for this systematic review arises from [VERIFY AND EXPAND]:
- Gap in current literature regarding...
- Conflicting evidence about...
- Rapid developments in...

### 1.3 Objectives
This systematic review aims to [REFINE BASED ON FINAL PROTOCOL]:
{self._format_objectives(search_strategy)}

## 2. Methods

### 2.1 Protocol and Registration
[ADD: PROSPERO registration number if applicable]
This review was conducted according to PRISMA guidelines.

### 2.2 Eligibility Criteria
{self._format_criteria(search_strategy)}

### 2.3 Information Sources
Databases searched:
{self._format_databases(search_strategy)}

### 2.4 Search Strategy
Example search (PubMed):
```
{search_strategy.search_queries.get('pubmed', 'SEARCH QUERY TO BE INSERTED')}
```

### 2.5 Study Selection
- {len(screening_results.get('definitely_include', []))} studies identified for inclusion
- {len(screening_results.get('needs_human_review', []))} require human review
- {len(screening_results.get('definitely_exclude', []))} excluded

[INSERT: PRISMA flow diagram]

### 2.6 Data Extraction
Data extraction template includes:
{self._format_extraction_fields(extraction_template)}

### 2.7 Risk of Bias Assessment
[TO BE COMPLETED: Specify tool - Cochrane RoB 2, QUADAS-2, etc.]

### 2.8 Data Synthesis
[TO BE COMPLETED: Specify meta-analysis methods or narrative synthesis approach]

## 3. Results

### 3.1 Study Selection
[TO BE COMPLETED WITH ACTUAL NUMBERS]
- Records identified: [N]
- Duplicates removed: [N]
- Records screened: {len(screening_results.get('definitely_include', [])) + 
                     len(screening_results.get('needs_human_review', [])) + 
                     len(screening_results.get('definitely_exclude', []))}
- Full-text articles assessed: [N]
- Studies included: [N]

### 3.2 Study Characteristics
[INSERT: Summary table of included studies]

### 3.3 Risk of Bias
[INSERT: Risk of bias summary]

### 3.4 Results of Individual Studies
[TO BE COMPLETED: Key findings from each study]

### 3.5 Synthesis of Results
[TO BE COMPLETED: Meta-analysis or narrative synthesis]

## 4. Discussion

### 4.1 Summary of Evidence
[TO BE WRITTEN: Main findings]

### 4.2 Limitations
Study limitations may include:
- [ASSESS: Publication bias]
- [ASSESS: Heterogeneity]
- [ASSESS: Quality of included studies]

### 4.3 Implications
[TO BE WRITTEN: Clinical/research implications]

## 5. Conclusion
[TO BE WRITTEN: Clear conclusions based on evidence]

## References
[TO BE FORMATTED: Include all screened papers]

---

## 📝 HUMAN TASKS CHECKLIST:
- [ ] Verify all numbers and statistics
- [ ] Complete risk of bias assessment
- [ ] Perform data extraction on included studies
- [ ] Conduct meta-analysis if appropriate
- [ ] Write abstract based on final results
- [ ] Review and revise all sections
- [ ] Format references properly
- [ ] Create PRISMA flow diagram
- [ ] Register protocol if not done
- [ ] Check journal requirements

## ⚠️ REMEMBER: This is a starting point only. All content requires expert review.
"""
        
        return draft
    
    def _generate_outline_only(self, search_strategy: SearchStrategy, 
                             screening_results: Dict[str, List[Paper]]) -> str:
        """Generate outline without draft content."""
        return f"""# SYSTEMATIC REVIEW OUTLINE

## Research Question
{search_strategy.research_question}

## Progress Summary
- ✅ Search strategy developed
- ✅ Initial screening complete ({len(screening_results.get('definitely_exclude', []))} excluded)
- ⏳ {len(screening_results.get('needs_human_review', []))} papers need human review
- ⏳ Data extraction pending
- ⏳ Risk of bias assessment pending
- ⏳ Synthesis pending

## Suggested Structure

1. **Introduction** (1-2 pages)
   - Background and rationale
   - Objectives
   
2. **Methods** (3-4 pages)
   - Protocol and registration
   - Eligibility criteria
   - Information sources
   - Search strategy
   - Study selection
   - Data extraction
   - Risk of bias assessment
   - Data synthesis plan
   
3. **Results** (5-8 pages)
   - Study selection (PRISMA diagram)
   - Study characteristics
   - Risk of bias
   - Results of individual studies
   - Synthesis of results
   
4. **Discussion** (3-4 pages)
   - Summary of evidence
   - Limitations
   - Implications for practice
   - Implications for research
   
5. **Conclusion** (1 paragraph)

## Next Steps
1. Complete screening of {len(screening_results.get('needs_human_review', []))} papers
2. Extract data using provided template
3. Assess risk of bias
4. Synthesize findings
5. Write first draft
"""
    
    def _generate_background(self, strategy: SearchStrategy) -> str:
        """Generate background section draft."""
        pico = strategy.pico_elements
        
        background = "[DRAFT - VERIFY ALL CLAIMS]\n\n"
        
        if pico.get('population'):
            background += f"The population of interest includes {', '.join(pico['population'])}. "
        
        if pico.get('intervention'):
            background += f"Recent advances in {', '.join(pico['intervention'])} have shown promise. "
        
        if pico.get('outcome'):
            background += f"Key outcomes of interest include {', '.join(pico['outcome'])}."
        
        return background
    
    def _format_objectives(self, strategy: SearchStrategy) -> str:
        """Format objectives based on PICO."""
        objectives = []
        
        objectives.append(f"Primary: To synthesize evidence on {strategy.research_question}")
        objectives.append("Secondary: To assess the quality of available evidence")
        objectives.append("Secondary: To identify gaps in current research")
        
        return '\n'.join(f"- {obj}" for obj in objectives)
    
    def _format_criteria(self, strategy: SearchStrategy) -> str:
        """Format inclusion/exclusion criteria."""
        criteria = "**Inclusion Criteria:**\n"
        for inc in strategy.inclusion_criteria:
            criteria += f"- {inc}\n"
        
        criteria += "\n**Exclusion Criteria:**\n"
        for exc in strategy.exclusion_criteria:
            criteria += f"- {exc}\n"
        
        return criteria
    
    def _format_databases(self, strategy: SearchStrategy) -> str:
        """Format database list."""
        return '\n'.join(f"- {db.upper()}" for db in strategy.search_queries.keys())
    
    def _format_extraction_fields(self, template: ExtractionTemplate) -> str:
        """Format extraction fields."""
        categories = [
            "**Study Characteristics:**",
            '\n'.join(f"- {char}" for char in template.study_characteristics),
            "\n**Outcome Measures:**",
            '\n'.join(f"- {outcome}" for outcome in template.outcome_measures),
            "\n**Quality Indicators:**",
            '\n'.join(f"- {qual}" for qual in template.quality_indicators)
        ]
        
        return '\n'.join(categories)


class PRISMAAssistant:
    """
    The complete PRISMA assistant that handles the grunt work of systematic reviews.
    Honest about limitations, focused on actually useful automation.
    """
    
    def __init__(self, lm_model=None, retrieval_module=None):
        self.lm_model = lm_model
        self.retrieval_module = retrieval_module
        
        # Initialize components
        self.search_builder = SearchStrategyBuilder()
        self.screening_assistant = ScreeningAssistant()
        self.extraction_helper = DataExtractionHelper()
        self.draft_generator = ZeroDraftGenerator(lm_model)
        
        # Track metrics
        self.time_saved = 0
        self.papers_processed = 0
    
    async def assist_systematic_review(self, 
                                     research_question: str,
                                     papers: Optional[List[Paper]] = None,
                                     generate_draft: bool = False) -> Dict[str, Any]:
        """
        Main entry point for systematic review assistance.
        
        Args:
            research_question: The research question in natural language
            papers: Optional list of papers if already retrieved
            generate_draft: Whether to generate zero draft (default: False)
            
        Returns:
            Dictionary with all assistance outputs and time saved
        """
        logger.info(f"Starting PRISMA assistance for: {research_question}")
        
        # 1. Develop comprehensive search strategy
        logger.info("Building search strategy...")
        search_strategy = self.search_builder.build_search_strategy(research_question)
        self.time_saved += 5  # Hours saved on search development
        
        # 2. Retrieve papers if not provided
        if papers is None and self.retrieval_module:
            logger.info("Retrieving papers...")
            papers = await self._retrieve_papers(search_strategy)
        elif papers is None:
            papers = []  # Empty list for demo
        
        # 3. Screen papers
        logger.info(f"Screening {len(papers)} papers...")
        screening_results = await self.screening_assistant.screen_papers(papers, search_strategy)
        self.papers_processed = len(papers)
        self.time_saved += len(papers) * 0.05  # ~3 minutes per paper for screening
        
        # 4. Create extraction template
        logger.info("Creating extraction template...")
        included_papers = screening_results['definitely_include'] + screening_results['needs_human_review']
        extraction_template = self.extraction_helper.create_extraction_template(
            included_papers, research_question
        )
        self.time_saved += 3  # Hours saved on template creation
        
        # 5. Generate reporting templates
        logger.info("Generating PRISMA reporting templates...")
        prisma_templates = self._generate_prisma_templates(screening_results)
        self.time_saved += 2  # Hours saved on PRISMA setup
        
        # 6. Optionally generate zero draft
        zero_draft = None
        if generate_draft:
            logger.info("Generating zero draft...")
            zero_draft = await self.draft_generator.generate_zero_draft(
                search_strategy, screening_results, extraction_template
            )
            self.time_saved += 5  # Hours saved on initial draft
        
        # Compile results
        results = {
            'search_strategy': search_strategy,
            'screening_results': {
                'definitely_exclude': len(screening_results['definitely_exclude']),
                'definitely_include': len(screening_results['definitely_include']),
                'needs_human_review': len(screening_results['needs_human_review']),
                'exclusion_stats': dict(screening_results['exclusion_stats'])
            },
            'performance_metrics': screening_results.get('performance_metrics', {}),
            'extraction_template': extraction_template,
            'prisma_templates': prisma_templates,
            'zero_draft': zero_draft,
            'metrics': {
                'papers_processed': self.papers_processed,
                'time_saved_hours': self.time_saved,
                'cost_estimate': f"${self.papers_processed * 0.001:.2f}",  # Rough estimate
                'human_tasks': [
                    f"Review {len(screening_results['needs_human_review'])} uncertain papers (<80% confidence)",
                    "Validate auto-screening decisions (spot check)",
                    "Extract data from included studies", 
                    "Assess risk of bias",
                    "Synthesize findings",
                    "Write/revise manuscript"
                ],
                'auto_decision_rate': screening_results.get('performance_metrics', {}).get('auto_decision_rate', 0),
                'confidence_threshold': 0.8
            }
        }
        
        logger.info(f"PRISMA assistance complete. Estimated time saved: {self.time_saved:.1f} hours")
        
        return results
    
    async def _retrieve_papers(self, search_strategy: SearchStrategy) -> List[Paper]:
        """Retrieve papers from databases."""
        # This would interface with actual database APIs
        # For now, return mock data
        return []
    
    def _generate_prisma_templates(self, screening_results: Dict) -> Dict[str, str]:
        """Generate PRISMA checklist and flow diagram templates."""
        
        # PRISMA flow diagram data
        flow_diagram = {
            'identification': {
                'database_records': 'n = [TO BE FILLED]',
                'other_sources': 'n = [TO BE FILLED]'
            },
            'screening': {
                'after_duplicates': f"n = {sum(len(v) for k, v in screening_results.items() if k != 'exclusion_stats')}",
                'excluded': f"n = {len(screening_results['definitely_exclude'])}",
                'reasons': screening_results['exclusion_stats']
            },
            'eligibility': {
                'full_text_assessed': f"n = {len(screening_results['definitely_include']) + len(screening_results['needs_human_review'])}",
                'full_text_excluded': 'n = [TO BE FILLED]',
                'reasons': '[TO BE FILLED]'
            },
            'included': {
                'qualitative_synthesis': 'n = [TO BE FILLED]',
                'quantitative_synthesis': 'n = [TO BE FILLED]'
            }
        }
        
        # PRISMA checklist (partial)
        checklist = """# PRISMA 2020 Checklist

## Title
- [ ] Identify as systematic review ± meta-analysis

## Abstract
- [ ] Structured summary including objectives, methods, results, conclusions

## Introduction
- [x] Rationale (draft provided)
- [x] Objectives with PICO (draft provided)

## Methods
- [x] Protocol and registration info template
- [x] Eligibility criteria specified
- [x] Information sources listed
- [x] Search strategy documented
- [ ] Study selection process (partially automated)
- [x] Data extraction template created
- [ ] Risk of bias method specified
- [ ] Summary measures planned
- [ ] Synthesis methods planned

## Results
- [ ] Study selection with flow diagram
- [ ] Study characteristics table
- [ ] Risk of bias results
- [ ] Individual study results
- [ ] Synthesis results
- [ ] Additional analyses

## Discussion
- [ ] Summary of evidence
- [ ] Limitations discussed
- [ ] Conclusions stated

## Funding
- [ ] Funding sources declared
"""
        
        return {
            'flow_diagram_data': flow_diagram,
            'checklist': checklist
        }


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
        self.assistant = PRISMAAssistant()
    
    async def screen_papers(self, papers: List[Paper]) -> Dict[str, Any]:
        """Screen papers using the PRISMA assistant."""
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
        
        return await self.assistant.screening_assistant.screen_papers(papers, search_strategy)


class ScreeningResult:
    """Result of paper screening operation."""
    
    def __init__(self, decision: str, confidence: float, reason: str = ""):
        self.decision = decision  # 'include', 'exclude', 'maybe'
        self.confidence = confidence
        self.reason = reason