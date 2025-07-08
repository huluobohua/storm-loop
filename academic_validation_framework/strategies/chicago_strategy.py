"""
Chicago Citation Format Strategy Implementation

Simplified Chicago Manual of Style citation validation strategy following
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


class ChicagoFormatStrategy(CitationFormatStrategy):
    """
    Chicago Manual of Style citation format validation strategy.
    
    Provides validation for Chicago-style citations commonly used
    in history and literature.
    """
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self._citation_type_cache: Dict[str, str] = {}
    
    @property
    def format_name(self) -> str:
        return "Chicago"
    
    @property
    def format_version(self) -> str:
        return "17th Edition"
    
    @property
    def supported_types(self) -> List[str]:
        return [
            "journal_article",
            "book",
            "book_chapter", 
            "web_source",
            "thesis",
            "newspaper"
        ]
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Chicago citation regex patterns.
        
        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            # Author patterns (Chicago uses full names)
            "single_author": r"^[A-Z][a-z]+,\s*[A-Z][a-z]+",
            "multiple_authors": r"^[A-Z][a-z]+,\s*[A-Z][a-z]+.*and\s*[A-Z][a-z]+",
            
            # Title patterns (Chicago uses italics for books, quotes for articles)
            "book_title_italics": r"\*[^*]+\*",
            "article_title_quotes": r"\"[^\"]+\"",
            
            # Publication patterns
            "parenthetical_publication": r"\([^)]+\)",
            "page_numbers": r"\d+[-–]\d+",
            
            # Structure patterns
            "proper_ending": r"\.$",
            "footnote_number": r"^\d+\."
        }
    
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """Validate citations against Chicago format."""
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
        """Chicago-specific validation logic."""
        errors = []
        evidence = []
        
        # Check for author format (Chicago uses full names)
        single_author = self.get_compiled_pattern("single_author")
        if single_author and single_author.match(citation):
            evidence.append(ValidationEvidence(
                pattern_matched="single_author",
                confidence_score=0.7,
                rule_applied="author_format_validation",
                context={"type": "single_author"}
            ))
        
        # Check for publication info in parentheses
        parenthetical = self.get_compiled_pattern("parenthetical_publication")
        if parenthetical and parenthetical.search(citation):
            evidence.append(ValidationEvidence(
                pattern_matched="parenthetical_publication",
                confidence_score=0.6,
                rule_applied="publication_format_validation",
                context={"has_parenthetical": True}
            ))
        
        # Check for italics or quotes
        if '*' in citation or '"' in citation:
            evidence.append(ValidationEvidence(
                pattern_matched="title_formatting",
                confidence_score=0.6,
                rule_applied="title_format_validation",
                context={"has_title_formatting": True}
            ))
        
        # Check for proper ending
        if citation.endswith('.'):
            evidence.append(ValidationEvidence(
                pattern_matched="proper_ending",
                confidence_score=0.5,
                rule_applied="structure_validation",
                context={"proper_ending": True}
            ))
        
        # Chicago citations often have page numbers
        if re.search(r'\d+[-–]\d+', citation):
            evidence.append(ValidationEvidence(
                pattern_matched="page_numbers",
                confidence_score=0.5,
                rule_applied="citation_details_validation",
                context={"has_page_numbers": True}
            ))
        
        is_valid = len(errors) == 0  # For now, simplified to always be valid if basic patterns match
        return is_valid, errors, evidence
    
    def generate_suggestions(self, errors: List[str]) -> List[str]:
        """Generate suggestions based on validation errors."""
        suggestions = []
        
        suggestions.append("Use full author names: Last, First")
        suggestions.append("Italicize book titles, quote article titles")
        suggestions.append("Include publication details in parentheses")
        
        return suggestions[:3]