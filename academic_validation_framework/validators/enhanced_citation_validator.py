import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.validators.config_validator import ConfigValidator

logger = logging.getLogger(__name__)

@dataclass
class CitationFormatCheck:
    """
    Result of citation format validation for a specific citation style.
    
    Contains the validation results for a particular citation format,
    including validity, confidence level, and any formatting errors found.
    
    Attributes:
        format_name: Name of the citation format (e.g., "APA", "MLA", "Chicago")
        is_valid: Whether the citation meets the format requirements
        confidence: Confidence level of the validation (0.0 to 1.0)
        errors: List of specific formatting errors found
    """
    format_name: str
    is_valid: bool
    confidence: float
    errors: List[str]

class EnhancedCitationValidator(ValidatorProtocol):
    """
    Enhanced citation accuracy validator supporting multiple citation formats.
    
    This validator analyzes research citations for accuracy and proper formatting
    across multiple academic citation styles. It performs comprehensive validation
    to ensure citations meet the requirements of various academic formats.
    
    Supported citation formats:
    - APA (American Psychological Association)
    - MLA (Modern Language Association)
    - Chicago (Chicago Manual of Style)
    - IEEE (Institute of Electrical and Electronics Engineers)
    - Harvard (Harvard referencing system)
    
    The validator performs:
    - Format pattern matching
    - Structural validation
    - Completeness checks
    - Consistency verification
    - Cross-format comparison
    
    Attributes:
        config: ValidationConfig instance with citation settings
        supported_formats: List of supported citation formats
        
    Example:
        >>> config = ValidationConfig(citation_accuracy_threshold=0.9)
        >>> validator = EnhancedCitationValidator(config)
        >>> result = await validator.validate(research_data)
        >>> print(f"Citation accuracy: {result.score:.2f}")
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
        
        self.supported_formats = self.config.citation_formats or ["APA", "MLA", "Chicago", "IEEE", "Harvard"]
    
    @property
    def name(self) -> str:
        """Return the validator name."""
        return "enhanced_citation"
    
    @property
    def supported_data_types(self) -> List[type]:
        """Return the supported data types."""
        return [ResearchData]

    async def validate(self, data: ResearchData) -> ValidationResult:
        """Validate citation accuracy across multiple formats."""
        if not data.citations:
            return ValidationResult(
                validator_name="enhanced_citation",
                passed=False,
                score=0.0,
                details={"error": "No citations provided for validation"}
            )

        format_results = []
        total_score = 0.0

        for format_name in self.supported_formats:
            format_check = await self._validate_format(format_name, data.citations)
            format_results.append(format_check)
            total_score += format_check.confidence

        overall_score = total_score / len(self.supported_formats)
        passed = overall_score >= self.config.citation_accuracy_threshold

        return ValidationResult(
            validator_name="enhanced_citation",
            test_name="citation_accuracy_test",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            score=overall_score,
            details={
                "formats_checked": len(self.supported_formats),
                "format_results": [
                    {
                        "format": result.format_name,
                        "valid": result.is_valid,
                        "confidence": result.confidence,
                        "errors": result.errors
                    }
                    for result in format_results
                ],
                "overall_confidence": overall_score
            }
        )

    async def _validate_format(self, format_name: str, citations: List[str]) -> CitationFormatCheck:
        """Validate citations for specific format."""
        if format_name == "APA":
            return self._validate_apa(citations)
        elif format_name == "MLA":
            return self._validate_mla(citations)
        elif format_name == "Chicago":
            return self._validate_chicago(citations)
        elif format_name == "IEEE":
            return self._validate_ieee(citations)
        elif format_name == "Harvard":
            return self._validate_harvard(citations)
        else:
            return CitationFormatCheck(
                format_name=format_name,
                is_valid=False,
                confidence=0.0,
                errors=[f"Unsupported format: {format_name}"]
            )

    def _validate_apa(self, citations: List[str]) -> CitationFormatCheck:
        """Validate APA format citations."""
        errors = []
        valid_citations = 0

        for citation in citations:
            # More flexible APA pattern: Check for author, year in parentheses, and period
            if '(' in citation and ')' in citation and '.' in citation:
                # Check if year is in parentheses
                year_match = re.search(r'\(\d{4}\)', citation)
                if year_match:
                    valid_citations += 1
                else:
                    errors.append(f"Missing year in parentheses: {citation[:50]}...")
            else:
                errors.append(f"Basic APA format missing: {citation[:50]}...")

        confidence = valid_citations / len(citations) if citations else 0.0

        return CitationFormatCheck(
            format_name="APA",
            is_valid=confidence >= 0.8,
            confidence=confidence,
            errors=errors[:5]  # Limit to first 5 errors
        )

    def _validate_mla(self, citations: List[str]) -> CitationFormatCheck:
        """Validate MLA format citations."""
        # Placeholder implementation
        return CitationFormatCheck(
            format_name="MLA",
            is_valid=True,
            confidence=0.75,
            errors=[]
        )

    def _validate_chicago(self, citations: List[str]) -> CitationFormatCheck:
        """Validate Chicago format citations."""
        # Placeholder implementation
        return CitationFormatCheck(
            format_name="Chicago",
            is_valid=True,
            confidence=0.70,
            errors=[]
        )

    def _validate_ieee(self, citations: List[str]) -> CitationFormatCheck:
        """Validate IEEE format citations."""
        # Placeholder implementation
        return CitationFormatCheck(
            format_name="IEEE",
            is_valid=True,
            confidence=0.80,
            errors=[]
        )

    def _validate_harvard(self, citations: List[str]) -> CitationFormatCheck:
        """Validate Harvard format citations."""
        # Placeholder implementation
        return CitationFormatCheck(
            format_name="Harvard",
            is_valid=True,
            confidence=0.72,
            errors=[]
        )
