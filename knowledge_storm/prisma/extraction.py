"""
Data extraction helper for PRISMA systematic reviews.

Creates structured templates for systematic data extraction based on 
research questions and included papers.
"""

import re
from collections import defaultdict
from typing import Dict, List, Any
from .models import Paper, ExtractionTemplate


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