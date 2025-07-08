"""
Enhanced PRISMA Validator with configuration-based approach.
"""
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
    """PRISMA systematic review compliance validator using configuration constants."""

    def __init__(self, config: 'ValidationConfig'):
        self.config = config
        self.constants = ValidationConstants.PRISMA
        self.checkpoints = self.constants.CHECKPOINTS
        
        # Checkpoint descriptions for reporting
        self.checkpoint_descriptions = {
            "protocol_registration": "Protocol was registered before study began (PROSPERO, etc.)",
            "search_strategy": "Comprehensive search strategy documented",
            "eligibility_criteria": "Clear inclusion and exclusion criteria specified",
            "information_sources": "Multiple databases and information sources searched",
            "study_selection": "Study selection process clearly described",
            "data_extraction": "Data extraction methods detailed",
            "risk_of_bias": "Risk of bias assessment performed",
            "synthesis_methods": "Appropriate synthesis methods used",
            "reporting_bias": "Publication bias assessment conducted",
            "certainty_assessment": "Evidence certainty/quality assessed (e.g., GRADE)",
            "study_characteristics": "Study characteristics comprehensively reported",
            "results_synthesis": "Results synthesized appropriately"
        }

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
                validator_name="enhanced_prisma_validator",
                test_name="prisma_compliance_test",
                status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
                score=overall_score,
                details={
                    "checkpoints": [
                        {
                            "name": cp.name,
                            "description": cp.description,
                            "passed": cp.passed,
                            "score": cp.score,
                            "details": cp.details
                        }
                        for cp in checkpoints
                    ],
                    "checkpoints_passed": sum(1 for cp in checkpoints if cp.passed),
                    "total_checkpoints": len(self.checkpoints)
                }
            )
        except ValidationError as e:
            logger.error(f"Validation error in PRISMA validator: {str(e)}")
            return ValidationResult(
                validator_name="enhanced_prisma_validator",
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
                validator_name="enhanced_prisma_validator",
                test_name="prisma_compliance_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "unexpected_error"
                }
            )

    async def _validate_checkpoint(self, checkpoint_name: str, data: ResearchData) -> PRISMACheckpoint:
        """Validate individual PRISMA checkpoint using configuration."""
        # Prepare text for analysis
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"
        
        # Get keywords for this checkpoint
        keywords = self.constants.CHECKPOINT_KEYWORDS.get(checkpoint_name, [])
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in combined_text)
        
        # Calculate score based on matches
        if keyword_matches >= self.constants.MIN_KEYWORDS_FOR_PASS:
            score = self.constants.FULL_SCORE
            passed = True
        elif keyword_matches >= self.constants.PARTIAL_SCORE_THRESHOLD:
            score = self.constants.PARTIAL_SCORE
            passed = False
        else:
            score = self.constants.NO_SCORE
            passed = False
        
        # Get description
        description = self.checkpoint_descriptions.get(
            checkpoint_name, 
            f"Validation for {checkpoint_name}"
        )
        
        # Build details
        if keyword_matches > 0:
            matched_keywords = [kw for kw in keywords if kw in combined_text]
            details = f"Found {keyword_matches} keywords: {', '.join(matched_keywords[:3])}"
            if len(matched_keywords) > 3:
                details += f" (+{len(matched_keywords) - 3} more)"
        else:
            details = f"No relevant keywords found (looked for: {', '.join(keywords[:3])}...)"
        
        return PRISMACheckpoint(
            name=checkpoint_name,
            description=description,
            passed=passed,
            score=score,
            details=details
        )