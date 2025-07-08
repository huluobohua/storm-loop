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

    def __init__(self, config: 'ValidationConfig'):
        self.config = config
        self.bias_types = [
            "confirmation_bias",
            "publication_bias",
            "selection_bias",
            "funding_bias",
            "reporting_bias"
        ]

    async def validate(self, data: ResearchData) -> ValidationResult:
        """Detect various types of research bias."""
        bias_checks = []
        total_bias_score = 0.0

        for bias_type in self.bias_types:
            bias_check = await self._detect_bias(bias_type, data)
            bias_checks.append(bias_check)
            # Higher confidence in bias detection = lower quality score
            total_bias_score += (1.0 - bias_check.confidence) if bias_check.detected else 1.0

        overall_score = total_bias_score / len(self.bias_types)
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
                evidence=[f"Unknown bias type: {bias_type}"]
            )

    def _detect_confirmation_bias(self, data: ResearchData) -> BiasCheck:
        """Detect confirmation bias indicators."""
        evidence = []
        bias_indicators = 0

        # Check for cherry-picking language
        if data.abstract:
            cherry_pick_terms = ["only", "exclusively", "particularly", "specifically supports"]
            for term in cherry_pick_terms:
                if term in data.abstract.lower():
                    evidence.append(f"Potential cherry-picking language: '{term}'")
                    bias_indicators += 1

        # Check citation patterns
        if data.citations and len(data.citations) < 10:
            evidence.append("Limited citations may indicate selective referencing")
            bias_indicators += 1

        confidence = min(bias_indicators / 3.0, 1.0)  # Max 3 indicators

        return BiasCheck(
            bias_type="confirmation_bias",
            detected=confidence > 0.5,
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
