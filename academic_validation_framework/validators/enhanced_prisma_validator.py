from typing import Dict, List, Any
from dataclasses import dataclass
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.config.validation_constants import ValidationConstants
from academic_validation_framework.utils.input_validation import validate_input, InputValidator, ValidationError
import logging

logger = logging.getLogger(__name__)

@dataclass
class PRISMACheckpoint:
    """Individual PRISMA compliance checkpoint."""
    name: str
    description: str
    passed: bool
    score: float
    details: str

class EnhancedPRISMAValidator:
    """PRISMA systematic review compliance validator."""

    def __init__(self, config: 'ValidationConfig'):
        self.config = config
        self.constants = ValidationConstants.PRISMA
        self.checkpoints = self.constants.CHECKPOINTS

    @validate_input
    async def validate(self, data: ResearchData) -> ValidationResult:
        """Validate PRISMA compliance with comprehensive input validation."""
        try:
            # Additional validation specific to PRISMA
            InputValidator.validate_research_data(data)
            
            checkpoints = []
            total_score = 0.0

            for checkpoint_name in self.checkpoints:
                checkpoint = await self._validate_checkpoint(checkpoint_name, data)
                checkpoints.append(checkpoint)
                total_score += checkpoint.score

            overall_score = total_score / len(self.checkpoints)
            passed = overall_score >= self.config.prisma_compliance_threshold

            return ValidationResult(
                validator_name="enhanced_prisma",
                test_name="prisma_compliance_test",
                status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
                score=overall_score,
                details={
                    "checkpoints": [
                        {
                            "name": cp.name,
                            "passed": cp.passed,
                            "score": cp.score,
                            "details": cp.details
                        }
                        for cp in checkpoints
                    ],
                    "total_checkpoints": len(checkpoints),
                    "passed_checkpoints": sum(1 for cp in checkpoints if cp.passed)
                }
            )
        except ValidationError as e:
            logger.error(f"Validation error in PRISMA validator: {str(e)}")
            return ValidationResult(
                validator_name="enhanced_prisma",
                test_name="prisma_compliance_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "validation_error"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in PRISMA validator: {str(e)}")
            return ValidationResult(
                validator_name="enhanced_prisma",
                test_name="prisma_compliance_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "unexpected_error"
                }
            )

    async def _validate_checkpoint(self, checkpoint_name: str, data: ResearchData) -> PRISMACheckpoint:
        """Validate individual PRISMA checkpoint with comprehensive logic."""
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"
        
        # Special handling for specific checkpoints
        if checkpoint_name == "protocol_registration":
            protocol_keywords = ["protocol", "prospero", "registration", "registered", "crd", "protocol number"]
            has_protocol = any(keyword in combined_text for keyword in protocol_keywords)
            score = 1.0 if has_protocol else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Protocol was registered before study began (PROSPERO, etc.)",
                passed=has_protocol,
                score=score,
                details=f"Protocol registration {'found' if has_protocol else 'not found'} in title/abstract"
            )

        # 2. Search strategy check
        elif checkpoint_name == "search_strategy":
            search_keywords = ["search", "database", "pubmed", "embase", "cochrane", "medline", "scopus", "web of science"]
            has_search = any(keyword in combined_text for keyword in search_keywords)
            score = 1.0 if has_search else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Search strategy and databases are documented",
                passed=has_search,
                score=score,
                details=f"Search strategy {'documented' if has_search else 'not documented'} in abstract"
            )

        # 3. Eligibility criteria check
        elif checkpoint_name == "eligibility_criteria":
            criteria_keywords = ["inclusion", "exclusion", "criteria", "eligible", "eligibility", "included", "excluded"]
            has_criteria = any(keyword in combined_text for keyword in criteria_keywords)
            score = 1.0 if has_criteria else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Study selection criteria are clearly defined",
                passed=has_criteria,
                score=score,
                details=f"Eligibility criteria {'specified' if has_criteria else 'not specified'}"
            )

        # 4. Information sources check
        elif checkpoint_name == "information_sources":
            source_keywords = ["database", "source", "electronic", "grey literature", "reference", "hand search"]
            has_sources = any(keyword in combined_text for keyword in source_keywords)
            score = 1.0 if has_sources else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Information sources are documented",
                passed=has_sources,
                score=score,
                details=f"Information sources {'documented' if has_sources else 'not documented'}"
            )

        # 5. Study selection check
        elif checkpoint_name == "study_selection":
            selection_keywords = ["screening", "selection", "reviewer", "independent", "duplicate", "agreement"]
            has_selection = any(keyword in combined_text for keyword in selection_keywords)
            score = 1.0 if has_selection else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Study selection process is described",
                passed=has_selection,
                score=score,
                details=f"Study selection process {'described' if has_selection else 'not described'}"
            )

        # 6. Data extraction check
        elif checkpoint_name == "data_extraction":
            extraction_keywords = ["data extraction", "extracted", "extraction form", "standardized", "pilot"]
            has_extraction = any(keyword in combined_text for keyword in extraction_keywords)
            score = 1.0 if has_extraction else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Data extraction methods are described",
                passed=has_extraction,
                score=score,
                details=f"Data extraction {'described' if has_extraction else 'not described'}"
            )

        # 7. Risk of bias assessment check
        elif checkpoint_name == "risk_of_bias":
            bias_keywords = ["risk of bias", "quality assessment", "cochrane", "rob", "methodological quality", "bias assessment"]
            has_bias_assessment = any(keyword in combined_text for keyword in bias_keywords)
            score = 1.0 if has_bias_assessment else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Risk of bias assessment is performed",
                passed=has_bias_assessment,
                score=score,
                details=f"Risk of bias assessment {'performed' if has_bias_assessment else 'not performed'}"
            )

        # 8. Synthesis methods check
        elif checkpoint_name == "synthesis_methods":
            synthesis_keywords = ["meta-analysis", "synthesis", "pooled", "statistical", "heterogeneity", "fixed effect", "random effect"]
            has_synthesis = any(keyword in combined_text for keyword in synthesis_keywords)
            score = 1.0 if has_synthesis else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Data synthesis methods are described",
                passed=has_synthesis,
                score=score,
                details=f"Synthesis methods {'described' if has_synthesis else 'not described'}"
            )

        # 9. Reporting bias check
        elif checkpoint_name == "reporting_bias":
            reporting_keywords = ["publication bias", "funnel plot", "egger", "begg", "reporting bias", "selective reporting"]
            has_reporting_check = any(keyword in combined_text for keyword in reporting_keywords)
            score = 1.0 if has_reporting_check else 0.5  # Partial score as it's often not mentioned in abstract
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Reporting bias assessment is addressed",
                passed=has_reporting_check,
                score=score,
                details=f"Reporting bias {'assessed' if has_reporting_check else 'not explicitly mentioned'}"
            )

        # 10. Certainty assessment check
        elif checkpoint_name == "certainty_assessment":
            certainty_keywords = ["grade", "certainty", "confidence", "evidence quality", "grade assessment"]
            has_certainty = any(keyword in combined_text for keyword in certainty_keywords)
            score = 1.0 if has_certainty else 0.5  # Partial score as GRADE is not always mentioned in abstract
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Certainty of evidence is assessed",
                passed=has_certainty,
                score=score,
                details=f"Certainty assessment {'mentioned' if has_certainty else 'not explicitly mentioned'}"
            )

        # 11. Study characteristics check
        elif checkpoint_name == "study_characteristics":
            char_keywords = ["characteristics", "participant", "intervention", "outcome", "study design", "population"]
            has_characteristics = any(keyword in combined_text for keyword in char_keywords)
            score = 1.0 if has_characteristics else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Study characteristics are described",
                passed=has_characteristics,
                score=score,
                details=f"Study characteristics {'described' if has_characteristics else 'not described'}"
            )

        # 12. Results synthesis check
        elif checkpoint_name == "results_synthesis":
            results_keywords = ["result", "finding", "outcome", "effect", "significant", "association", "conclusion"]
            has_results = any(keyword in combined_text for keyword in results_keywords)
            score = 1.0 if has_results else 0.0
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Results of synthesis are presented",
                passed=has_results,
                score=score,
                details=f"Results synthesis {'presented' if has_results else 'not clearly presented'}"
            )

        # Default fallback
        else:
            return PRISMACheckpoint(
                name=checkpoint_name,
                description=f"Assessment of {checkpoint_name.replace('_', ' ')}",
                passed=False,
                score=0.0,
                details=f"Unknown checkpoint: {checkpoint_name}"
            )
