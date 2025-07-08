"""
Abstract Base Strategy for Citation Format Validation

Defines the core interfaces and base functionality for citation format validation
following the Strategy pattern and SOLID principles.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Pattern
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationEvidence:
    """Evidence supporting a validation decision."""
    pattern_matched: Optional[str] = None
    confidence_score: float = 0.0
    rule_applied: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormatValidationResult:
    """Comprehensive result of citation format validation."""
    format_name: str
    is_valid: bool
    confidence: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    evidence: List[ValidationEvidence] = field(default_factory=list)
    
    # Detailed breakdown
    total_citations: int = 0
    valid_citations: int = 0
    processed_citations: int = 0
    
    # Error categorization
    format_errors: List[str] = field(default_factory=list)
    structure_errors: List[str] = field(default_factory=list)
    content_errors: List[str] = field(default_factory=list)
    
    # Performance metrics
    processing_time_ms: float = 0.0
    validation_timestamp: datetime = field(default_factory=datetime.now)


class CitationFormatStrategy(ABC):
    """
    Abstract strategy for citation format validation.
    
    Implements the Strategy pattern for different citation formats,
    providing a consistent interface while allowing format-specific
    validation logic.
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._validation_cache: Dict[str, FormatValidationResult] = {}
        
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of the citation format (e.g., 'APA', 'MLA')."""
        pass
    
    @property
    @abstractmethod
    def format_version(self) -> str:
        """Version of the format specification (e.g., '7th edition')."""
        pass
    
    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        """List of supported citation types (e.g., ['journal', 'book', 'web'])."""
        pass
    
    @abstractmethod
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """
        Validate a list of citations against this format.
        
        Args:
            citations: List of citation strings to validate
            
        Returns:
            FormatValidationResult containing validation details
        """
        pass
    
    @abstractmethod
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Get regex patterns used for validation.
        
        Returns:
            Dictionary mapping pattern names to regex strings
        """
        pass
    
    def get_compiled_pattern(self, pattern_name: str) -> Optional[Pattern]:
        """
        Get a compiled regex pattern, caching for performance.
        
        Args:
            pattern_name: Name of the pattern to retrieve
            
        Returns:
            Compiled regex pattern or None if not found
        """
        if pattern_name not in self._compiled_patterns:
            patterns = self.get_validation_patterns()
            if pattern_name in patterns:
                try:
                    self._compiled_patterns[pattern_name] = re.compile(
                        patterns[pattern_name], 
                        re.IGNORECASE | re.MULTILINE
                    )
                except re.error as e:
                    self._log_error(f"Failed to compile pattern {pattern_name}: {e}")
                    return None
        
        return self._compiled_patterns.get(pattern_name)
    
    def validate_single_citation(self, citation: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """
        Validate a single citation string.
        
        Args:
            citation: Single citation string to validate
            
        Returns:
            Tuple of (is_valid, errors, evidence)
        """
        if not citation.strip():
            return False, ["Empty citation"], []
        
        # Basic structure validation
        errors = []
        evidence = []
        
        # Check minimum length
        if len(citation.strip()) < 10:
            errors.append("Citation appears too short")
            
        # Check for basic punctuation
        if not any(punct in citation for punct in ['.', ',', ';']):
            errors.append("Missing basic punctuation")
            
        # Format-specific validation (to be implemented by subclasses)
        format_valid, format_errors, format_evidence = self._validate_format_specific(citation)
        
        errors.extend(format_errors)
        evidence.extend(format_evidence)
        
        return format_valid and len(errors) == 0, errors, evidence
    
    @abstractmethod
    def _validate_format_specific(self, citation: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """
        Format-specific validation logic to be implemented by subclasses.
        
        Args:
            citation: Single citation string to validate
            
        Returns:
            Tuple of (is_valid, errors, evidence)
        """
        pass
    
    def calculate_confidence(self, validation_results: List[Tuple[bool, List[str], List[ValidationEvidence]]]) -> float:
        """
        Calculate confidence score based on validation results.
        
        Args:
            validation_results: List of validation results for individual citations
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not validation_results:
            return 0.0
        
        valid_count = sum(1 for result in validation_results if result[0])
        total_count = len(validation_results)
        
        base_confidence = valid_count / total_count
        
        # Adjust confidence based on evidence quality
        evidence_scores = []
        for _, _, evidence_list in validation_results:
            if evidence_list:
                avg_evidence_score = sum(e.confidence_score for e in evidence_list) / len(evidence_list)
                evidence_scores.append(avg_evidence_score)
        
        if evidence_scores:
            evidence_factor = sum(evidence_scores) / len(evidence_scores)
            return (base_confidence + evidence_factor) / 2
        
        return base_confidence
    
    def generate_suggestions(self, errors: List[str]) -> List[str]:
        """
        Generate helpful suggestions based on validation errors.
        
        Args:
            errors: List of validation errors
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        error_text = " ".join(errors).lower()
        
        if "author" in error_text:
            suggestions.append(f"Ensure author names follow {self.format_name} format guidelines")
        
        if "year" in error_text or "date" in error_text:
            suggestions.append("Check that publication year is properly formatted and positioned")
        
        if "title" in error_text:
            suggestions.append("Verify title formatting, including capitalization and quotation marks")
        
        if "journal" in error_text or "publication" in error_text:
            suggestions.append("Check journal/publication name formatting and abbreviations")
        
        if "punctuation" in error_text:
            suggestions.append(f"Review {self.format_name} punctuation guidelines")
        
        if not suggestions:
            suggestions.append(f"Consult the {self.format_name} {self.format_version} style guide")
        
        return suggestions
    
    def _log_error(self, message: str) -> None:
        """Log an error message."""
        # In a production system, this would use proper logging
        print(f"ERROR [{self.format_name}]: {message}")
    
    def _log_warning(self, message: str) -> None:
        """Log a warning message."""
        # In a production system, this would use proper logging
        print(f"WARNING [{self.format_name}]: {message}")
    
    def get_format_info(self) -> Dict[str, Any]:
        """
        Get metadata about this format strategy.
        
        Returns:
            Dictionary containing format metadata
        """
        return {
            "name": self.format_name,
            "version": self.format_version,
            "supported_types": self.supported_types,
            "strict_mode": self.strict_mode,
            "pattern_count": len(self.get_validation_patterns()),
            "cache_size": len(self._validation_cache)
        }