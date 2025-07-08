"""
Harvard Citation Format Strategy Implementation

Simplified Harvard author-date citation validation strategy following
the Strategy pattern and providing detailed validation evidence.
"""

import re
import time
from typing import List, Dict, Any, Tuple, Optional

from .base import (
    CitationFormatStrategy, 
    FormatValidationResult, 
    ValidationEvidence,
    ErrorSeverity
)


class HarvardFormatStrategy(CitationFormatStrategy):
    """
    Harvard author-date citation format validation strategy.
    
    Provides validation for Harvard-style citations commonly used
    in humanities and social sciences.
    """
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self._citation_type_cache: Dict[str, str] = {}
    
    @property
    def format_name(self) -> str:
        return "Harvard"
    
    @property
    def format_version(self) -> str:
        return "Author-Date"
    
    @property
    def supported_types(self) -> List[str]:
        return [
            "journal_article",
            "book",
            "book_chapter", 
            "web_source",
            "thesis",
            "report"
        ]
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Harvard author-date citation regex patterns.
        
        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            # Author patterns (Harvard uses full names)
            "single_author": r"^[A-Z][a-z]+,\s*[A-Z]\.",
            "multiple_authors": r"^[A-Z][a-z]+,\s*[A-Z]\..*and\s*[A-Z][a-z]+,\s*[A-Z]\.",
            "et_al": r"[A-Z][a-z]+,\s*[A-Z]\.\s*et\s*al\.",
            
            # Year patterns (Harvard emphasizes year)
            "year_pattern": r"\(\d{4}[a-z]?\)",
            "year_only": r"\d{4}[a-z]?",
            
            # Title patterns
            "title_italics": r"\*[^*]+\*",
            "title_quotes": r"'[^']+'",
            
            # Journal patterns
            "journal_italics": r"\*[A-Z][^*]+\*",
            
            # Structure patterns
            "proper_ending": r"\.$",
            "available_at": r"Available at:",
            "accessed": r"Accessed:"
        }
    
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """Validate citations against Harvard format."""
        start_time = time.time()
        
        if not citations:
            return FormatValidationResult(
                format_name=self.format_name,
                is_valid=False,
                confidence=0.0,
                errors=["No citations provided"],
                total_citations=0,
                valid_citations=0,
                processed_citations=0,
                processing_time_ms=0.0
            )
        
        validation_results = []
        all_errors = []
        all_warnings = []
        all_suggestions = []
        all_evidence = []
        
        valid_count = 0
        
        for i, citation in enumerate(citations):
            if not citation.strip():
                validation_results.append((False, [f"Citation {i+1} is empty"], []))
                continue
            
            # Simplified validation
            is_valid, errors, evidence = self.validate_single_citation(citation)
            validation_results.append((is_valid, errors, evidence))
            
            if is_valid:
                valid_count += 1
            
            all_errors.extend([f"Citation {i+1}: {error}" for error in errors])
            all_evidence.extend(evidence)
        
        # Calculate confidence
        confidence = self.calculate_confidence(validation_results)
        
        # Processing time
        processing_time = (time.time() - start_time) * 1000
        
        return FormatValidationResult(
            format_name=self.format_name,
            is_valid=len(all_errors) == 0,
            confidence=confidence,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            evidence=all_evidence,
            total_citations=len(citations),
            valid_citations=valid_count,
            processed_citations=len([c for c in citations if c.strip()]),
            format_errors=all_errors,
            structure_errors=[],
            content_errors=[],
            processing_time_ms=processing_time
        )
    
    def _validate_format_specific(self, citation: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Harvard-specific validation logic."""
        errors = []
        evidence = []
        
        # Check for year in parentheses (key Harvard feature)
        year_pattern = self.get_compiled_pattern("year_pattern")
        if year_pattern and year_pattern.search(citation):
            evidence.append(ValidationEvidence(
                pattern_matched="year_pattern",
                confidence_score=0.8,
                rule_applied="harvard_year_validation",
                context={"has_year_parentheses": True}
            ))
        else:
            errors.append("Harvard format requires year in parentheses")
        
        # Check for author format
        single_author = self.get_compiled_pattern("single_author")
        if single_author and single_author.match(citation):
            evidence.append(ValidationEvidence(
                pattern_matched="single_author",
                confidence_score=0.7,
                rule_applied="author_format_validation",
                context={"type": "single_author"}
            ))
        
        # Check for italics (common in Harvard)
        if '*' in citation:
            evidence.append(ValidationEvidence(
                pattern_matched="title_italics",
                confidence_score=0.6,
                rule_applied="title_format_validation",
                context={"has_italics": True}
            ))
        
        # Basic structure check
        if citation.endswith('.'):
            evidence.append(ValidationEvidence(
                pattern_matched="proper_ending",
                confidence_score=0.5,
                rule_applied="structure_validation",
                context={"proper_ending": True}
            ))
        
        is_valid = len(errors) == 0
        return is_valid, errors, evidence
    
    def generate_suggestions(self, errors: List[str]) -> List[str]:
        """Generate suggestions based on validation errors."""
        suggestions = []
        
        if any("year" in error.lower() for error in errors):
            suggestions.append("Include year in parentheses: (2023)")
        
        suggestions.append("Use author-date format: Author, A. (Year)")
        suggestions.append("Italicize book and journal titles")
        
        return suggestions[:3]