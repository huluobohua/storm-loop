"""
Bias detector using Strategy pattern for cleaner, more maintainable code.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.config.validation_constants import ValidationConstants
from academic_validation_framework.utils.input_validation import validate_input, InputValidator, ValidationError
from academic_validation_framework.validators.strategies.bias_detection_strategies import (
    ConfirmationBiasStrategy, PublicationBiasStrategy, SelectionBiasStrategy,
    FundingBiasStrategy, ReportingBiasStrategy
)
import logging

logger = logging.getLogger(__name__)

@dataclass
class BiasCheck:
    """Individual bias detection result."""
    bias_type: str
    detected: bool
    confidence: float
    evidence: List[str]

class BiasDetector:
    """Comprehensive bias detection validator using Strategy pattern."""

    def __init__(self, config: 'ValidationConfig'):
        self.config = config
        self.constants = ValidationConstants()
        self.bias_types = self.constants.BIAS.BIAS_TYPES
        
        # Initialize strategies
        self.strategies = {
            "confirmation_bias": ConfirmationBiasStrategy(self.constants),
            "publication_bias": PublicationBiasStrategy(self.constants),
            "selection_bias": SelectionBiasStrategy(self.constants),
            "funding_bias": FundingBiasStrategy(self.constants),
            "reporting_bias": ReportingBiasStrategy(self.constants)
        }

    @validate_input
    async def validate(self, data: ResearchData) -> ValidationResult:
        """Detect various types of research bias with comprehensive input validation."""
        try:
            # Validate input data
            InputValidator.validate_research_data(data)
            
            bias_checks = await self._run_bias_detection(data)
            overall_score = self._calculate_overall_score(bias_checks)
            passed = overall_score >= self.config.bias_detection_threshold

            return ValidationResult(
                validator_name="bias_detector",
                test_name="bias_detection_test",
                status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
                score=overall_score,
                details={
                    "bias_checks": [
                        {
                            "type": check.bias_type,
                            "detected": check.detected,
                            "confidence": check.confidence,
                            "evidence": check.evidence
                        }
                        for check in bias_checks
                    ],
                    "overall_score": overall_score,
                    "threshold": self.config.bias_detection_threshold,
                    "passed": passed
                }
            )
        except ValidationError as e:
            # Handle validation errors gracefully
            logger.error(f"Validation error in BiasDetector: {str(e)}")
            return ValidationResult(
                validator_name="bias_detector",
                test_name="bias_detection_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "ValidationError"
                }
            )
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error in BiasDetector: {str(e)}")
            return ValidationResult(
                validator_name="bias_detector",
                test_name="bias_detection_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

    async def _run_bias_detection(self, data: ResearchData) -> List[BiasCheck]:
        """Run all bias detection checks using strategies."""
        bias_checks = []
        
        for bias_type in self.bias_types:
            try:
                check = await self._detect_bias(bias_type, data)
                bias_checks.append(check)
            except Exception as e:
                logger.warning(f"Error detecting {bias_type}: {str(e)}")
                # Create a failed check for this bias type
                bias_checks.append(BiasCheck(
                    bias_type=bias_type,
                    detected=False,
                    confidence=0.0,
                    evidence=[f"Error during detection: {str(e)}"]
                ))
        
        return bias_checks

    def _calculate_overall_score(self, bias_checks: List[BiasCheck]) -> float:
        """Calculate overall bias score (1.0 = no bias, 0.0 = maximum bias)."""
        if not bias_checks:
            return 1.0
        
        # Calculate weighted bias score based on confidence
        total_bias_confidence = sum(check.confidence for check in bias_checks if check.detected)
        max_possible_bias = len(bias_checks)  # If all biases were detected with confidence 1.0
        
        # Normalize to 0-1 scale where 1 = no bias, 0 = maximum bias
        bias_ratio = total_bias_confidence / max_possible_bias if max_possible_bias > 0 else 0
        
        # Return inverted score (1 - bias_ratio) so higher score = less bias
        return max(0.0, min(1.0, 1.0 - bias_ratio))

    async def _detect_bias(self, bias_type: str, data: ResearchData) -> BiasCheck:
        """Detect specific type of bias using strategy pattern."""
        strategy = self.strategies.get(bias_type)
        if strategy:
            return strategy.detect(data)
        else:
            return BiasCheck(
                bias_type=bias_type,
                detected=False,
                confidence=0.0,
                evidence=[f"Unknown bias type: {bias_type}"]
            )