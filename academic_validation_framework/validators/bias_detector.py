import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.config.validation_constants import ValidationConstants
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.utils.input_validation import validate_input, InputValidator, ValidationError
from academic_validation_framework.validators.config_validator import ConfigValidator
from academic_validation_framework.validators.strategies.bias_detection_strategies import (
    ConfirmationBiasStrategy, PublicationBiasStrategy, SelectionBiasStrategy,
    FundingBiasStrategy, ReportingBiasStrategy
)

logger = logging.getLogger(__name__)

@dataclass
class BiasCheck:
    """
    Result of individual bias detection analysis.
    
    Contains the findings for a specific type of bias detection,
    including detection status, confidence level, and supporting evidence.
    
    Attributes:
        bias_type: Type of bias analyzed (e.g., "confirmation_bias", "publication_bias")
        detected: Whether bias was detected in the research
        confidence: Confidence level of the detection (0.0 to 1.0)
        evidence: List of textual evidence supporting the bias detection
    """
    bias_type: str
    detected: bool
    confidence: float
    evidence: List[str]

class BiasDetector(ValidatorProtocol):
    """
    Comprehensive bias detection validator using Strategy pattern.
    
    This validator analyzes research data to detect various types of bias
    that may affect the validity and reliability of research findings.
    It uses multiple detection strategies to identify different bias types.
    
    Supported bias types:
    - Confirmation bias: Tendency to favor information that confirms existing beliefs
    - Publication bias: Tendency to publish positive results over negative ones
    - Selection bias: Bias in selecting participants or studies
    - Funding bias: Influence of funding sources on research outcomes
    - Reporting bias: Selective reporting of results
    
    The validator employs:
    - Text analysis algorithms
    - Pattern recognition
    - Statistical analysis
    - Contextual evaluation
    - Evidence aggregation
    
    Attributes:
        config: ValidationConfig instance with bias detection settings
        constants: Bias detection constants and patterns
        bias_types: List of bias types to check (configurable)
        strategies: Dictionary of detection strategies for each bias type
        
    Example:
        >>> config = ValidationConfig(bias_detection_threshold=0.85)
        >>> detector = BiasDetector(config)
        >>> result = await detector.validate(research_data)
        >>> print(f"Bias detection score: {result.score:.2f}")
    """

    def __init__(self, config: ValidationConfig):
        # Validate and fix config
        config_validation = ConfigValidator.validate_config(config)
        if not config_validation.is_valid:
            logger.warning(f"Configuration validation failed: {config_validation.errors}")
            self.config = ConfigValidator.validate_and_fix_config(config)
            logger.info("Configuration has been automatically corrected")
        else:
            self.config = config
        
        # Log configuration warnings
        if config_validation.warnings:
            for warning in config_validation.warnings:
                logger.warning(f"Configuration warning: {warning}")
        
        self.constants = ValidationConstants()
        self.bias_types = self.config.bias_types_to_check or self.constants.BIAS.BIAS_TYPES
        
        # Initialize strategies based on config
        self.strategies = {}
        if "confirmation_bias" in self.bias_types:
            self.strategies["confirmation_bias"] = ConfirmationBiasStrategy(self.constants)
        if "publication_bias" in self.bias_types:
            self.strategies["publication_bias"] = PublicationBiasStrategy(self.constants)
        if "selection_bias" in self.bias_types:
            self.strategies["selection_bias"] = SelectionBiasStrategy(self.constants)
        if "funding_bias" in self.bias_types:
            self.strategies["funding_bias"] = FundingBiasStrategy(self.constants)
        if "reporting_bias" in self.bias_types:
            self.strategies["reporting_bias"] = ReportingBiasStrategy(self.constants)
    
    @property
    def name(self) -> str:
        """Return the validator name."""
        return "bias_detector"
    
    @property
    def supported_data_types(self) -> List[type]:
        """Return the supported data types."""
        return [ResearchData]

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
                    "total_bias_types_checked": len(self.bias_types),
                    "biases_detected": sum(1 for check in bias_checks if check.detected)
                }
            )
        except ValidationError as e:
            logger.error(f"Validation error in BiasDetector: {str(e)}")
            return ValidationResult(
                validator_name="bias_detector",
                test_name="bias_detection_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "validation_error"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in BiasDetector: {str(e)}")
            return ValidationResult(
                validator_name="bias_detector",
                test_name="bias_detection_test",
                status=ValidationStatus.ERROR,
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": "unexpected_error"
                }
            )

    async def _run_bias_detection(self, data: ResearchData) -> List[BiasCheck]:
        """Run comprehensive bias detection across all bias types."""
        bias_checks = []
        
        for bias_type in self.bias_types:
            try:
                check = await self._detect_bias(bias_type, data)
                bias_checks.append(check)
            except Exception as e:
                logger.error(f"Error detecting {bias_type}: {str(e)}")
                # Create a failed check for this bias type
                bias_checks.append(BiasCheck(
                    bias_type=bias_type,
                    detected=False,
                    confidence=0.0,
                    evidence=[f"Error during detection: {str(e)}"]
                ))
        
        return bias_checks
    
    def _calculate_overall_score(self, bias_checks: List[BiasCheck]) -> float:
        """Calculate overall bias score from individual checks."""
        if not bias_checks:
            return 1.0  # No bias detected if no checks
        
        # Calculate score as inverse of bias detection
        # More bias detected = lower score
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

    def _detect_confirmation_bias(self, data: ResearchData) -> BiasCheck:
        """Detect confirmation bias indicators."""
        evidence = []
        bias_indicators = 0
        
        bias_config = self.constants.BIAS_KEYWORDS["confirmation_bias"]

        # Check for cherry-picking language
        if data.abstract:
            cherry_pick_terms = bias_config["cherry_picking"]
            for term in cherry_pick_terms:
                if term in data.abstract.lower():
                    evidence.append(f"Potential cherry-picking language: '{term}'")
                    bias_indicators += 1

        # Check citation patterns
        min_citations = bias_config["min_citations"]
        if data.citations and len(data.citations) < min_citations:
            evidence.append(f"Limited citations ({len(data.citations)} < {min_citations}) may indicate selective referencing")
            bias_indicators += 1

        # Calculate confidence using configured factor
        max_indicators = self.constants.CONFIDENCE_FACTORS["confirmation_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0)
        
        # Use configured threshold
        threshold = self.constants.DETECTION_THRESHOLDS["confirmation_bias"]

        return BiasCheck(
            bias_type="confirmation_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )

    def _detect_publication_bias(self, data: ResearchData) -> BiasCheck:
        """Detect publication bias indicators."""
        evidence = []

        # Check for positive results emphasis
        if data.abstract:
            positive_terms = ["significant", "effective", "successful", "improved"]
            positive_count = sum(1 for term in positive_terms if term in data.abstract.lower())

            if positive_count > 3:
                evidence.append("High frequency of positive outcome language")

        return BiasCheck(
            bias_type="publication_bias",
            detected=len(evidence) > 0,
            confidence=0.3 if evidence else 0.0,
            evidence=evidence
        )

    def _detect_selection_bias(self, data: ResearchData) -> BiasCheck:
        """Detect selection bias indicators."""
        evidence = []
        bias_indicators = 0
        
        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for convenience sampling indicators
            convenience_terms = ["convenience", "available", "volunteer", "self-selected", "convenience sample"]
            for term in convenience_terms:
                if term in abstract_lower:
                    evidence.append(f"Potential convenience sampling: '{term}'")
                    bias_indicators += 1
            
            # Check for missing randomization
            randomization_terms = ["random", "randomized", "randomisation", "random assignment"]
            has_randomization = any(term in abstract_lower for term in randomization_terms)
            
            if not has_randomization and any(term in abstract_lower for term in ["participants", "subjects", "patients"]):
                evidence.append("No mention of randomization in participant selection")
                bias_indicators += 1
            
            # Check for exclusion criteria that might introduce bias
            bias_exclusion_terms = ["excluded healthy", "excluded low-risk", "excluded mild cases"]
            for term in bias_exclusion_terms:
                if term in abstract_lower:
                    evidence.append(f"Potentially biased exclusion: '{term}'")
                    bias_indicators += 1
        
        confidence = min(bias_indicators / 3.0, 1.0)
        
        return BiasCheck(
            bias_type="selection_bias",
            detected=confidence > 0.3,
            confidence=confidence,
            evidence=evidence if evidence else ["No clear selection bias indicators detected"]
        )

    def _detect_funding_bias(self, data: ResearchData) -> BiasCheck:
        """Detect funding bias indicators."""
        evidence = []
        bias_indicators = 0
        
        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for industry funding mentions
            industry_terms = ["sponsored by", "funded by", "pharmaceutical", "company", "corporation", "industry funding"]
            for term in industry_terms:
                if term in abstract_lower:
                    evidence.append(f"Industry involvement mentioned: '{term}'")
                    bias_indicators += 1
            
            # Check for conflict of interest statements
            conflict_terms = ["conflict of interest", "competing interests", "disclosures", "financial relationships"]
            has_conflict_mention = any(term in abstract_lower for term in conflict_terms)
            
            # Check for overly positive language about commercial products
            commercial_positive = ["breakthrough", "revolutionary", "unprecedented", "superior", "optimal"]
            commercial_count = sum(1 for term in commercial_positive if term in abstract_lower)
            
            if commercial_count > 2:
                evidence.append("High frequency of commercial promotional language")
                bias_indicators += 1
            
            # Check for missing funding disclosure
            funding_terms = ["funding", "grant", "support", "sponsored"]
            has_funding_mention = any(term in abstract_lower for term in funding_terms)
            
            if not has_funding_mention:
                evidence.append("No funding source mentioned")
                bias_indicators += 0.5  # Partial indicator
        
        confidence = min(bias_indicators / 3.0, 1.0)
        
        return BiasCheck(
            bias_type="funding_bias",
            detected=confidence > 0.4,
            confidence=confidence,
            evidence=evidence if evidence else ["No clear funding bias indicators detected"]
        )

    def _detect_reporting_bias(self, data: ResearchData) -> BiasCheck:
        """Detect reporting bias indicators."""
        evidence = []
        bias_indicators = 0
        
        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for selective outcome reporting
            outcome_terms = ["primary outcome", "secondary outcome", "endpoint", "measured"]
            outcome_mentions = sum(1 for term in outcome_terms if term in abstract_lower)
            
            # Check for vague result reporting
            vague_terms = ["some", "several", "many", "various", "numerous", "certain"]
            vague_count = sum(1 for term in vague_terms if term in abstract_lower)
            
            if vague_count > 3:
                evidence.append("Vague reporting language used frequently")
                bias_indicators += 1
            
            # Check for emphasis on significant results only
            significance_terms = ["significant", "p <", "p<", "statistically significant"]
            significance_count = sum(1 for term in significance_terms if term in abstract_lower)
            
            # Check for non-significant results reporting
            non_sig_terms = ["non-significant", "not significant", "no difference", "no effect"]
            non_sig_count = sum(1 for term in non_sig_terms if term in abstract_lower)
            
            if significance_count > 2 and non_sig_count == 0:
                evidence.append("Only significant results emphasized, no mention of non-significant findings")
                bias_indicators += 1
            
            # Check for post-hoc analysis mentions
            post_hoc_terms = ["post-hoc", "post hoc", "exploratory", "unplanned analysis"]
            has_post_hoc = any(term in abstract_lower for term in post_hoc_terms)
            
            if has_post_hoc:
                evidence.append("Post-hoc analyses mentioned, potential for data mining")
                bias_indicators += 0.5
            
            # Check for missing effect sizes
            effect_size_terms = ["effect size", "cohen's d", "odds ratio", "confidence interval", "95% ci"]
            has_effect_size = any(term in abstract_lower for term in effect_size_terms)
            
            if not has_effect_size and significance_count > 0:
                evidence.append("Statistical significance reported without effect sizes")
                bias_indicators += 0.5
        
        confidence = min(bias_indicators / 3.0, 1.0)
        
        return BiasCheck(
            bias_type="reporting_bias",
            detected=confidence > 0.3,
            confidence=confidence,
            evidence=evidence if evidence else ["No clear reporting bias indicators detected"]
        )
