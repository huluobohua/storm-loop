"""
APA Citation Format Strategy Implementation

Comprehensive APA 7th Edition citation validation strategy following
the Strategy pattern and providing detailed validation evidence.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import time

from .base import (
    CitationFormatStrategy, 
    FormatValidationResult, 
    ValidationEvidence,
    ErrorSeverity
)


class APAFormatStrategy(CitationFormatStrategy):
    """
    APA 7th Edition citation format validation strategy.
    
    Provides comprehensive validation for APA-style citations including
    journal articles, books, web sources, and other citation types.
    """
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self._citation_type_cache: Dict[str, str] = {}
    
    @property
    def format_name(self) -> str:
        return "APA"
    
    @property
    def format_version(self) -> str:
        return "7th Edition"
    
    @property
    def supported_types(self) -> List[str]:
        return [
            "journal_article",
            "book",
            "book_chapter", 
            "web_source",
            "conference_paper",
            "thesis",
            "report",
            "newspaper",
            "magazine",
            "government_document",
            "personal_communication",
            "software"
        ]
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Comprehensive APA 7th Edition regex patterns.
        
        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            # Author patterns
            "single_author": r"^[A-Z][a-z]+,\s+[A-Z]\.\s*[A-Z]?\.\s*",
            "multiple_authors": r"^[A-Z][a-z]+,\s+[A-Z]\.\s*[A-Z]?\.\s*,?\s*(&\s+[A-Z][a-z]+,\s+[A-Z]\.\s*[A-Z]?\.\s*)*",
            "et_al": r"[A-Z][a-z]+,\s+[A-Z]\.\s*[A-Z]?\.\s*,?\s*et\s+al\.",
            "corporate_author": r"^[A-Z][A-Za-z\s&,\.]+\.",
            
            # Year patterns
            "year_parentheses": r"\((\d{4}[a-z]?|in\s+press|n\.d\.)\)",
            "year_range": r"\((\d{4})-(\d{4})\)",
            "no_date": r"\(n\.d\.\)",
            "in_press": r"\(in\s+press\)",
            
            # Title patterns
            "sentence_case_title": r'"[A-Z][^"]*\."',
            "book_title_italics": r"\*[^*]+\*",
            "article_title": r'"[^"]+"',
            
            # Journal patterns
            "journal_name": r"\*[A-Z][^*,]+\*",
            "volume_issue": r"(\*[^*]+\*),?\s*(\d+)(\(\d+\))?,?\s*(\d+-\d+|\d+)",
            "journal_abbreviation": r"\*[A-Z][A-Za-z\.\s]+\*",
            
            # Publisher patterns
            "publisher": r"[A-Z][A-Za-z\s&]+\.",
            "location_publisher": r"[A-Z][a-z]+(?:,\s+[A-Z]{2})?\s*:\s*[A-Z][A-Za-z\s&]+\.",
            
            # DOI and URL patterns
            "doi_pattern": r"(doi:|https?://doi\.org/)10\.\d+/[^\s]+",
            "url_pattern": r"https?://[^\s]+",
            "retrieved_from": r"Retrieved\s+from\s+https?://[^\s]+",
            "retrieved_date": r"Retrieved\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4},\s+from",
            
            # Page patterns
            "page_numbers": r"pp?\.\s*\d+(-\d+)?",
            "article_number": r"Article\s+\d+",
            
            # Complete citation patterns for different types
            "journal_article": r"^[A-Z][a-z]+,\s+[A-Z]\.\s*.*\(\d{4}[a-z]?\)\.\s*[^.]+\.\s*\*[^*]+\*,?\s*\d+(\(\d+\))?,?\s*(\d+-\d+|\d+|Article\s+\d+)",
            "book_citation": r"^[A-Z][a-z]+,\s+[A-Z]\.\s*.*\(\d{4}[a-z]?\)\.\s*\*[^*]+\*\.\s*[A-Z][a-z]+",
            "web_source": r"^[A-Z][a-z]+,\s+[A-Z]\.\s*.*\(\d{4}[a-z]?\)\.\s*[^.]+\.\s*(Retrieved|https?://)",
            
            # Special elements
            "edition": r"\(\d+(st|nd|rd|th)\s+ed\.\)",
            "editor": r"\([A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+,\s*(Ed\.|Eds\.)\)",
            "translator": r"\([A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+,\s*Trans\.\)",
            
            # Error detection patterns
            "common_errors": r"(,\s*&\s*[a-z]|[a-z],\s+[A-Z]|[\.,]{2,}|\s{2,})",
            "missing_period": r"[^\.]\s*$",
        }
    
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """
        Validate a list of citations against APA 7th Edition format.
        
        Args:
            citations: List of citation strings to validate
            
        Returns:
            FormatValidationResult with comprehensive validation details
        """
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
        
        format_errors = []
        structure_errors = []
        content_errors = []
        
        valid_count = 0
        
        for i, citation in enumerate(citations):
            if not citation.strip():
                structure_errors.append(f"Citation {i+1}: Empty citation")
                validation_results.append((False, [f"Citation {i+1} is empty"], []))
                continue
            
            # Validate single citation
            is_valid, errors, evidence = self.validate_single_citation(citation)
            validation_results.append((is_valid, errors, evidence))
            
            if is_valid:
                valid_count += 1
            else:
                # Categorize errors
                for error in errors:
                    if any(keyword in error.lower() for keyword in ["format", "pattern", "style"]):
                        format_errors.append(f"Citation {i+1}: {error}")
                    elif any(keyword in error.lower() for keyword in ["structure", "order", "missing"]):
                        structure_errors.append(f"Citation {i+1}: {error}")
                    else:
                        content_errors.append(f"Citation {i+1}: {error}")
            
            all_errors.extend([f"Citation {i+1}: {error}" for error in errors])
            all_evidence.extend(evidence)
            
            # Generate citation-specific suggestions
            if errors:
                citation_suggestions = self.generate_suggestions(errors)
                all_suggestions.extend([f"Citation {i+1}: {suggestion}" for suggestion in citation_suggestions])
        
        # Calculate confidence
        confidence = self.calculate_confidence(validation_results)
        
        # Generate overall warnings
        if confidence < 0.5:
            all_warnings.append("Low overall confidence - many citations may not follow APA format")
        elif confidence < 0.8:
            all_warnings.append("Medium confidence - some citations may need formatting improvements")
        
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
            format_errors=format_errors,
            structure_errors=structure_errors,
            content_errors=content_errors,
            processing_time_ms=processing_time
        )
    
    def _validate_format_specific(self, citation: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """
        APA-specific validation logic.
        
        Args:
            citation: Single citation string to validate
            
        Returns:
            Tuple of (is_valid, errors, evidence)
        """
        errors = []
        evidence = []
        
        # Detect citation type
        citation_type = self._detect_citation_type(citation)
        
        # Extract and validate components
        components = self._extract_citation_components(citation)
        
        # Validate author format
        author_valid, author_errors, author_evidence = self._validate_author_format(citation, components)
        errors.extend(author_errors)
        evidence.extend(author_evidence)
        
        # Validate year format
        year_valid, year_errors, year_evidence = self._validate_year_format(citation, components)
        errors.extend(year_errors)
        evidence.extend(year_evidence)
        
        # Validate title format
        title_valid, title_errors, title_evidence = self._validate_title_format(citation, components, citation_type)
        errors.extend(title_errors)
        evidence.extend(title_evidence)
        
        # Validate publication info
        pub_valid, pub_errors, pub_evidence = self._validate_publication_info(citation, components, citation_type)
        errors.extend(pub_errors)
        evidence.extend(pub_evidence)
        
        # Validate DOI/URL if present
        doi_valid, doi_errors, doi_evidence = self._validate_doi_url(citation, components)
        errors.extend(doi_errors)
        evidence.extend(doi_evidence)
        
        # Overall validity
        is_valid = (author_valid and year_valid and title_valid and 
                   pub_valid and doi_valid and len(errors) == 0)
        
        # Add type detection evidence
        if citation_type != "unknown":
            evidence.append(ValidationEvidence(
                pattern_matched=citation_type,
                confidence_score=0.8,
                rule_applied="citation_type_detection",
                context={"detected_type": citation_type}
            ))
        
        return is_valid, errors, evidence
    
    def _detect_citation_type(self, citation: str) -> str:
        """Detect the type of citation (journal, book, web, etc.)."""
        if citation in self._citation_type_cache:
            return self._citation_type_cache[citation]
        
        citation_lower = citation.lower()
        
        # Journal article indicators
        if (self.get_compiled_pattern("journal_article") and 
            self.get_compiled_pattern("journal_article").search(citation)):
            citation_type = "journal_article"
        elif "*" in citation and any(indicator in citation_lower for indicator in ["vol.", "volume", "pp.", "article"]):
            citation_type = "journal_article"
        # Book indicators
        elif (self.get_compiled_pattern("book_citation") and 
              self.get_compiled_pattern("book_citation").search(citation)):
            citation_type = "book"
        elif any(indicator in citation_lower for indicator in ["publisher", "press", "edition"]):
            citation_type = "book"
        # Web source indicators
        elif (self.get_compiled_pattern("web_source") and 
              self.get_compiled_pattern("web_source").search(citation)):
            citation_type = "web_source"
        elif any(indicator in citation_lower for indicator in ["retrieved", "http", "www.", "doi:"]):
            citation_type = "web_source"
        else:
            citation_type = "unknown"
        
        self._citation_type_cache[citation] = citation_type
        return citation_type
    
    def _extract_citation_components(self, citation: str) -> Dict[str, Optional[str]]:
        """Extract key components from a citation."""
        components = {
            "author": None,
            "year": None,
            "title": None,
            "journal": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "doi": None,
            "url": None,
            "publisher": None
        }
        
        # Extract year
        year_pattern = self.get_compiled_pattern("year_parentheses")
        if year_pattern:
            year_match = year_pattern.search(citation)
            if year_match:
                components["year"] = year_match.group(1)
        
        # Extract DOI
        doi_pattern = self.get_compiled_pattern("doi_pattern")
        if doi_pattern:
            doi_match = doi_pattern.search(citation)
            if doi_match:
                components["doi"] = doi_match.group(0)
        
        # Extract URL
        url_pattern = self.get_compiled_pattern("url_pattern")
        if url_pattern:
            url_match = url_pattern.search(citation)
            if url_match:
                components["url"] = url_match.group(0)
        
        # Extract journal name (text between asterisks)
        journal_match = re.search(r'\*([^*]+)\*', citation)
        if journal_match:
            components["journal"] = journal_match.group(1)
        
        # Extract title (text in quotes)
        title_match = re.search(r'"([^"]+)"', citation)
        if title_match:
            components["title"] = title_match.group(1)
        
        return components
    
    def _validate_author_format(self, citation: str, components: Dict[str, Optional[str]]) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate author formatting."""
        errors = []
        evidence = []
        
        # Check for basic author pattern
        single_author = self.get_compiled_pattern("single_author")
        multiple_authors = self.get_compiled_pattern("multiple_authors")
        et_al = self.get_compiled_pattern("et_al")
        corporate = self.get_compiled_pattern("corporate_author")
        
        author_found = False
        confidence = 0.0
        
        if single_author and single_author.match(citation):
            author_found = True
            confidence = 0.9
            evidence.append(ValidationEvidence(
                pattern_matched="single_author",
                confidence_score=confidence,
                rule_applied="author_format_validation",
                context={"type": "single_author"}
            ))
        elif multiple_authors and multiple_authors.match(citation):
            author_found = True
            confidence = 0.85
            evidence.append(ValidationEvidence(
                pattern_matched="multiple_authors",
                confidence_score=confidence,
                rule_applied="author_format_validation",
                context={"type": "multiple_authors"}
            ))
        elif et_al and et_al.search(citation):
            author_found = True
            confidence = 0.8
            evidence.append(ValidationEvidence(
                pattern_matched="et_al",
                confidence_score=confidence,
                rule_applied="author_format_validation",
                context={"type": "et_al"}
            ))
        elif corporate and corporate.match(citation):
            author_found = True
            confidence = 0.75
            evidence.append(ValidationEvidence(
                pattern_matched="corporate_author",
                confidence_score=confidence,
                rule_applied="author_format_validation",
                context={"type": "corporate_author"}
            ))
        
        if not author_found:
            errors.append("Author format does not match APA style (should be: Last, F. M.)")
            confidence = 0.0
        
        # Check for common author errors
        if ", and " in citation:
            errors.append("Use '&' instead of 'and' for multiple authors")
        
        if re.search(r'[a-z],\s+[A-Z]', citation):
            errors.append("Author names should be properly capitalized")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_year_format(self, citation: str, components: Dict[str, Optional[str]]) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate year formatting."""
        errors = []
        evidence = []
        
        year_pattern = self.get_compiled_pattern("year_parentheses")
        if not year_pattern:
            errors.append("Year pattern not available")
            return False, errors, evidence
        
        year_match = year_pattern.search(citation)
        if year_match:
            year = year_match.group(1)
            confidence = 0.9
            
            # Validate year format
            if re.match(r'\d{4}[a-z]?', year):
                evidence.append(ValidationEvidence(
                    pattern_matched="standard_year",
                    confidence_score=confidence,
                    rule_applied="year_format_validation",
                    context={"year": year}
                ))
            elif year in ["n.d.", "in press"]:
                confidence = 0.8
                evidence.append(ValidationEvidence(
                    pattern_matched="special_year",
                    confidence_score=confidence,
                    rule_applied="year_format_validation",
                    context={"year": year}
                ))
            else:
                errors.append(f"Invalid year format: {year}")
                confidence = 0.0
        else:
            errors.append("Year in parentheses not found")
            confidence = 0.0
        
        return len(errors) == 0, errors, evidence
    
    def _validate_title_format(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate title formatting based on citation type."""
        errors = []
        evidence = []
        
        if citation_type == "journal_article":
            # Articles should have titles in quotes
            if '"' not in citation:
                errors.append("Article titles should be in quotation marks")
            else:
                title_match = re.search(r'"([^"]+)"', citation)
                if title_match:
                    title = title_match.group(1)
                    # Check sentence case (first word and proper nouns capitalized)
                    if title[0].isupper():
                        evidence.append(ValidationEvidence(
                            pattern_matched="sentence_case_title",
                            confidence_score=0.8,
                            rule_applied="title_format_validation",
                            context={"title": title, "type": "article"}
                        ))
                    else:
                        errors.append("Article title should start with capital letter")
        
        elif citation_type == "book":
            # Books should have titles in italics (represented by asterisks)
            if '*' not in citation:
                errors.append("Book titles should be in italics")
            else:
                title_match = re.search(r'\*([^*]+)\*', citation)
                if title_match:
                    title = title_match.group(1)
                    evidence.append(ValidationEvidence(
                        pattern_matched="italicized_title",
                        confidence_score=0.8,
                        rule_applied="title_format_validation",
                        context={"title": title, "type": "book"}
                    ))
        
        return len(errors) == 0, errors, evidence
    
    def _validate_publication_info(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate publication information."""
        errors = []
        evidence = []
        
        if citation_type == "journal_article":
            # Check for journal name in italics
            if components.get("journal"):
                evidence.append(ValidationEvidence(
                    pattern_matched="journal_name",
                    confidence_score=0.8,
                    rule_applied="publication_info_validation",
                    context={"journal": components["journal"]}
                ))
            else:
                errors.append("Journal name not found or not properly formatted")
            
            # Check for volume/issue/page information
            volume_issue_pattern = self.get_compiled_pattern("volume_issue")
            if volume_issue_pattern and volume_issue_pattern.search(citation):
                evidence.append(ValidationEvidence(
                    pattern_matched="volume_issue",
                    confidence_score=0.7,
                    rule_applied="publication_info_validation",
                    context={"found": "volume_issue_pages"}
                ))
            else:
                errors.append("Volume, issue, or page information missing or improperly formatted")
        
        elif citation_type == "book":
            # Check for publisher information
            if re.search(r'[A-Z][A-Za-z\s&]+\.', citation):
                evidence.append(ValidationEvidence(
                    pattern_matched="publisher",
                    confidence_score=0.7,
                    rule_applied="publication_info_validation",
                    context={"type": "publisher"}
                ))
            else:
                errors.append("Publisher information missing or improperly formatted")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_doi_url(self, citation: str, components: Dict[str, Optional[str]]) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate DOI or URL formatting."""
        errors = []
        evidence = []
        
        # Check DOI format
        if components.get("doi"):
            doi_pattern = self.get_compiled_pattern("doi_pattern")
            if doi_pattern and doi_pattern.search(citation):
                evidence.append(ValidationEvidence(
                    pattern_matched="doi_pattern",
                    confidence_score=0.9,
                    rule_applied="doi_url_validation",
                    context={"doi": components["doi"]}
                ))
            else:
                errors.append("DOI format is invalid")
        
        # Check URL format
        elif components.get("url"):
            url_pattern = self.get_compiled_pattern("url_pattern")
            if url_pattern and url_pattern.search(citation):
                # Check for "Retrieved" statement for web sources
                if "retrieved" in citation.lower():
                    evidence.append(ValidationEvidence(
                        pattern_matched="retrieved_from",
                        confidence_score=0.8,
                        rule_applied="doi_url_validation",
                        context={"url": components["url"], "has_retrieved": True}
                    ))
                else:
                    evidence.append(ValidationEvidence(
                        pattern_matched="url_pattern",
                        confidence_score=0.6,
                        rule_applied="doi_url_validation",
                        context={"url": components["url"], "has_retrieved": False}
                    ))
                    if self.strict_mode:
                        errors.append("Web sources should include 'Retrieved from' statement")
        
        return len(errors) == 0, errors, evidence