from typing import Dict, List
from dataclasses import dataclass

from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.config import ValidationConfig

@dataclass
class BiasCheck:
    """Individual bias detection result."""
    bias_type: str
    detected: bool
    confidence: float
    evidence: List[str]

class BiasDetector:
    """Comprehensive bias detection validator."""

    def __init__(self, config: ValidationConfig):
        self.config = config
        self._name = "bias_detector"
        self.bias_types = [
            "confirmation_bias",
            "publication_bias",
            "selection_bias",
            "funding_bias",
            "reporting_bias",
        ]

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_data_types(self) -> List[type]:
        return [ResearchData]

    async def validate(self, data: ResearchData) -> ValidationResult:
        """Detect various types of research bias."""
        bias_checks: List[BiasCheck] = []
        total_bias_score = 0.0

        for bias_type in self.bias_types:
            bias_check = await self._detect_bias(bias_type, data)
            bias_checks.append(bias_check)
            total_bias_score += (1.0 - bias_check.confidence) if bias_check.detected else 1.0

        overall_score = total_bias_score / len(self.bias_types)
        passed = overall_score >= self.config.bias_detection_threshold

        return ValidationResult(
            validator_name=self.name,
            test_name="bias_detection",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            score=overall_score,
            details={
                "bias_checks": [
                    {
                        "type": check.bias_type,
                        "detected": check.detected,
                        "confidence": check.confidence,
                        "evidence": check.evidence,
                    }
                    for check in bias_checks
                ],
                "total_bias_types_checked": len(self.bias_types),
                "biases_detected": sum(1 for check in bias_checks if check.detected),
            },
        )

    async def _detect_bias(self, bias_type: str, data: ResearchData) -> BiasCheck:
        """Detect specific type of bias."""
        if bias_type == "confirmation_bias":
            return self._detect_confirmation_bias(data)
        elif bias_type == "publication_bias":
            return self._detect_publication_bias(data)
        elif bias_type == "selection_bias":
            return self._detect_selection_bias(data)
        elif bias_type == "funding_bias":
            return self._detect_funding_bias(data)
        elif bias_type == "reporting_bias":
            return self._detect_reporting_bias(data)
        else:
            return BiasCheck(
                bias_type=bias_type,
                detected=False,
                confidence=0.0,
                evidence=[f"Unknown bias type: {bias_type}"],
            )

    def _detect_confirmation_bias(self, data: ResearchData) -> BiasCheck:
        """Detect confirmation bias indicators."""
        evidence: List[str] = []
        bias_indicators = 0

        if data.abstract:
            cherry_pick_terms = ["only", "exclusively", "particularly", "specifically supports"]
            for term in cherry_pick_terms:
                if term in data.abstract.lower():
                    evidence.append(f"Potential cherry-picking language: '{term}'")
                    bias_indicators += 1

        if data.citations and len(data.citations) < 10:
            evidence.append("Limited citations may indicate selective referencing")
            bias_indicators += 1

        confidence = min(bias_indicators / 3.0, 1.0)

        return BiasCheck(
            bias_type="confirmation_bias",
            detected=confidence > 0.5,
            confidence=confidence,
            evidence=evidence,
        )

    def _detect_publication_bias(self, data: ResearchData) -> BiasCheck:
        """Detect publication bias indicators."""
        evidence: List[str] = []

        if data.abstract:
            positive_terms = ["significant", "effective", "successful", "improved"]
            positive_count = sum(1 for term in positive_terms if term in data.abstract.lower())
            if positive_count > 3:
                evidence.append("High frequency of positive outcome language")

        return BiasCheck(
            bias_type="publication_bias",
            detected=len(evidence) > 0,
            confidence=0.3 if evidence else 0.0,
            evidence=evidence,
        )

    def _detect_selection_bias(self, data: ResearchData) -> BiasCheck:
        """Detect selection bias indicators."""
        return BiasCheck(
            bias_type="selection_bias",
            detected=False,
            confidence=0.2,
            evidence=["Placeholder detection for selection bias"],
        )

    def _detect_funding_bias(self, data: ResearchData) -> BiasCheck:
        """Detect funding bias indicators."""
        return BiasCheck(
            bias_type="funding_bias",
            detected=False,
            confidence=0.1,
            evidence=["Placeholder detection for funding bias"],
        )

    def _detect_reporting_bias(self, data: ResearchData) -> BiasCheck:
        """Detect reporting bias indicators."""
        return BiasCheck(
            bias_type="reporting_bias",
            detected=False,
            confidence=0.15,
            evidence=["Placeholder detection for reporting bias"],
        )
