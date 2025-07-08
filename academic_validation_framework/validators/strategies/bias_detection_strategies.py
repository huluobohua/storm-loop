"""
Bias detection strategies using Strategy pattern.
Reduces complexity by separating each bias type into its own strategy.
"""
from abc import ABC, abstractmethod
from typing import List
from academic_validation_framework.validators.bias_detector import BiasCheck
from academic_validation_framework.models import ResearchData
from academic_validation_framework.config.validation_constants import ValidationConstants


class BiasDetectionStrategy(ABC):
    """Abstract base class for bias detection strategies."""

    def __init__(self, constants: ValidationConstants):
        self.constants = constants

    @abstractmethod
    def detect(self, data: ResearchData) -> BiasCheck:
        """Detect specific type of bias."""
        pass


class ConfirmationBiasStrategy(BiasDetectionStrategy):
    """Strategy for detecting confirmation bias."""

    def detect(self, data: ResearchData) -> BiasCheck:
        evidence = []
        bias_indicators = 0

        bias_config = self.constants.BIAS.BIAS_KEYWORDS["confirmation_bias"]

        # Check for cherry-picking language
        if data.abstract:
            cherry_pick_terms = bias_config["cherry_picking"]
            for term in cherry_pick_terms:
                if term in data.abstract.lower():
                    evidence.append(f"Potential cherry-picking language: '{term}'")
                    bias_indicators += 1

        # Check for hypothesis-confirming language
        if data.abstract:
            confirming_terms = bias_config["hypothesis_confirming"]
            for term in confirming_terms:
                if term in data.abstract.lower():
                    evidence.append(f"Hypothesis-confirming language: '{term}'")
                    bias_indicators += 1

        # Check citation patterns
        min_citations = bias_config["min_citations"]
        if data.citations is None or len(data.citations) == 0:
            evidence.append("No citations provided")
            bias_indicators += 2
        elif len(data.citations) < min_citations:
            evidence.append(f"Limited citations ({len(data.citations)} < {min_citations}) may indicate selective referencing")
            bias_indicators += 1

        # Calculate confidence
        max_indicators = self.constants.BIAS.CONFIDENCE_FACTORS["confirmation_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0) if max_indicators > 0 else 0.0
        threshold = self.constants.BIAS.DETECTION_THRESHOLDS["confirmation_bias"]

        return BiasCheck(
            bias_type="confirmation_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )


class PublicationBiasStrategy(BiasDetectionStrategy):
    """Strategy for detecting publication bias."""

    def detect(self, data: ResearchData) -> BiasCheck:
        evidence = []
        bias_indicators = 0
        
        bias_config = self.constants.BIAS.BIAS_KEYWORDS["publication_bias"]

        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for positive outcome emphasis
            positive_terms = bias_config["positive_terms"]
            positive_count = sum(1 for term in positive_terms if term in abstract_lower)

            if positive_count > bias_config["positive_threshold"]:
                evidence.append(f"High frequency of positive outcome language ({positive_count} terms)")
                bias_indicators += 2
            elif positive_count > 0:
                evidence.append("Some positive outcome language detected")
                bias_indicators += 1

            # Check for significance emphasis
            significance_terms = bias_config["significance_terms"]
            significance_count = sum(1 for term in significance_terms if term in abstract_lower)
            
            if significance_count >= 2:
                evidence.append("Multiple mentions of statistical significance")
                bias_indicators += 1

        # Check title for positive bias
        if data.title:
            title_lower = data.title.lower()
            positive_in_title = any(term in title_lower for term in ["effective", "significant", "successful"])
            if positive_in_title:
                evidence.append("Positive outcome language in title")
                bias_indicators += 1

        # Calculate confidence
        max_indicators = self.constants.BIAS.CONFIDENCE_FACTORS["publication_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0) if max_indicators > 0 else 0.0
        threshold = self.constants.BIAS.DETECTION_THRESHOLDS["publication_bias"]

        return BiasCheck(
            bias_type="publication_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )


class SelectionBiasStrategy(BiasDetectionStrategy):
    """Strategy for detecting selection bias."""

    def detect(self, data: ResearchData) -> BiasCheck:
        evidence = []
        bias_indicators = 0
        
        bias_config = self.constants.BIAS.BIAS_KEYWORDS["selection_bias"]

        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for poor sampling methods
            poor_sampling = bias_config["poor_sampling"]
            for term in poor_sampling:
                if term in abstract_lower:
                    evidence.append(f"Poor sampling method detected: '{term}'")
                    bias_indicators += 2

            # Check for lack of randomization
            randomization_terms = bias_config["randomization_terms"]
            has_randomization = any(term in abstract_lower for term in randomization_terms)
            
            if not has_randomization and "random" not in abstract_lower:
                evidence.append("No mention of randomization")
                bias_indicators += 1

            # Check for exclusion criteria issues
            exclusion_terms = bias_config["exclusion_issues"]
            for term in exclusion_terms:
                if term in abstract_lower:
                    evidence.append(f"Potential exclusion issue: '{term}'")
                    bias_indicators += 1

        # Calculate confidence
        max_indicators = self.constants.BIAS.CONFIDENCE_FACTORS["selection_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0) if max_indicators > 0 else 0.0
        threshold = self.constants.BIAS.DETECTION_THRESHOLDS["selection_bias"]

        return BiasCheck(
            bias_type="selection_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )


class FundingBiasStrategy(BiasDetectionStrategy):
    """Strategy for detecting funding bias."""

    def detect(self, data: ResearchData) -> BiasCheck:
        evidence = []
        bias_indicators = 0
        
        bias_config = self.constants.BIAS.BIAS_KEYWORDS["funding_bias"]

        combined_text = ""
        if data.title:
            combined_text += data.title.lower() + " "
        if data.abstract:
            combined_text += data.abstract.lower()

        if combined_text:
            # Check for industry funding
            industry_terms = bias_config["industry_terms"]
            for term in industry_terms:
                if term in combined_text:
                    evidence.append(f"Industry funding indicator: '{term}'")
                    bias_indicators += 2

            # Check for conflict of interest terms
            conflict_terms = bias_config["conflict_terms"]
            has_conflict_disclosure = any(term in combined_text for term in conflict_terms)
            
            # Check for specific funding disclosures
            if "funded by" in combined_text or "funding from" in combined_text:
                evidence.append("Funding source mentioned")
                if any(term in combined_text for term in ["pharmaceutical", "industry", "company"]):
                    evidence.append("Commercial funding detected")
                    bias_indicators += 2
                elif not has_conflict_disclosure:
                    evidence.append("Funding mentioned but no conflict of interest statement")
                    bias_indicators += 1

        # Calculate confidence
        max_indicators = self.constants.BIAS.CONFIDENCE_FACTORS["funding_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0) if max_indicators > 0 else 0.0
        threshold = self.constants.BIAS.DETECTION_THRESHOLDS["funding_bias"]

        return BiasCheck(
            bias_type="funding_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )


class ReportingBiasStrategy(BiasDetectionStrategy):
    """Strategy for detecting reporting bias."""

    def detect(self, data: ResearchData) -> BiasCheck:
        evidence = []
        bias_indicators = 0
        
        bias_config = self.constants.BIAS.BIAS_KEYWORDS["reporting_bias"]

        if data.abstract:
            abstract_lower = data.abstract.lower()
            
            # Check for selective reporting indicators
            selective_terms = bias_config["selective_reporting"]
            for term in selective_terms:
                if term in abstract_lower:
                    evidence.append(f"Selective reporting indicator: '{term}'")
                    bias_indicators += 1

            # Check for outcome switching
            outcome_terms = bias_config["outcome_switching"]
            outcome_mentions = sum(1 for term in outcome_terms if term in abstract_lower)
            
            if outcome_mentions >= 2 and "primary" in abstract_lower and "secondary" in abstract_lower:
                if "not significant" in abstract_lower or "no difference" in abstract_lower:
                    evidence.append("Possible outcome switching (primary outcomes not significant)")
                    bias_indicators += 2

            # Check for incomplete reporting
            incomplete_terms = bias_config["incomplete_reporting"]
            for term in incomplete_terms:
                if term in abstract_lower:
                    evidence.append(f"Incomplete reporting indicator: '{term}'")
                    bias_indicators += 1

        # Calculate confidence
        max_indicators = self.constants.BIAS.CONFIDENCE_FACTORS["reporting_bias"]
        confidence = min(bias_indicators / max_indicators, 1.0) if max_indicators > 0 else 0.0
        threshold = self.constants.BIAS.DETECTION_THRESHOLDS["reporting_bias"]

        return BiasCheck(
            bias_type="reporting_bias",
            detected=confidence > threshold,
            confidence=confidence,
            evidence=evidence
        )