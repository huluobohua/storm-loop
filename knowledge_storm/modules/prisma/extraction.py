"""
PRISMA Data Extraction Helper.

Focused module for systematic data extraction with standardized templates
for different study types in systematic reviews.
"""

import re
from typing import Dict, Any

from .core import Paper, ExtractionTemplate


class DataExtractionHelper:
    """Helper for systematic data extraction with standardized templates."""
    
    def __init__(self):
        self.standard_templates = {
            'clinical_trial': ExtractionTemplate(
                fields={
                    'study_design': {'type': 'categorical', 'description': 'Type of clinical trial', 'required': True},
                    'sample_size': {'type': 'numeric', 'description': 'Number of participants', 'required': True},
                    'intervention': {'type': 'text', 'description': 'Description of intervention', 'required': True},
                    'primary_outcome': {'type': 'text', 'description': 'Primary outcome measure', 'required': True},
                    'follow_up': {'type': 'numeric', 'description': 'Follow-up period in months', 'required': False}
                },
                study_characteristics=['randomization', 'blinding', 'control_group'],
                outcome_measures=['efficacy', 'safety', 'quality_of_life'],
                quality_indicators=['jadad_score', 'risk_of_bias', 'funding_source']
            ),
            'observational': ExtractionTemplate(
                fields={
                    'study_type': {'type': 'categorical', 'description': 'Cohort, case-control, cross-sectional', 'required': True},
                    'population': {'type': 'text', 'description': 'Study population', 'required': True},
                    'exposure': {'type': 'text', 'description': 'Exposure or risk factor', 'required': True},
                    'outcome': {'type': 'text', 'description': 'Outcome of interest', 'required': True}
                },
                study_characteristics=['selection_criteria', 'matching', 'confounders'],
                outcome_measures=['relative_risk', 'odds_ratio', 'hazard_ratio'],
                quality_indicators=['newcastle_ottawa_scale', 'selection_bias', 'information_bias']
            )
        }
    
    def get_template(self, study_type: str) -> ExtractionTemplate:
        """Get standardized extraction template for study type."""
        return self.standard_templates.get(study_type, self.standard_templates['observational'])
    
    def extract_data(self, paper: Paper, template: ExtractionTemplate) -> Dict[str, Any]:
        """Extract data from paper using template (placeholder implementation)."""
        # In production, this would use NLP/ML to extract structured data
        extracted = {}
        
        for field_name, field_info in template.fields.items():
            # Simple pattern-based extraction (would use NLP in production)
            if field_name == 'sample_size':
                match = re.search(r'n\s*=\s*(\d+)', paper.abstract, re.IGNORECASE)
                extracted[field_name] = int(match.group(1)) if match else None
            else:
                # Placeholder - would extract based on field type
                extracted[field_name] = f"Extract {field_name} from: {paper.title[:50]}..."
        
        return extracted


# Export classes
__all__ = ['DataExtractionHelper']