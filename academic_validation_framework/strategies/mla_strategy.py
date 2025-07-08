"""
MLA Citation Format Strategy Implementation

Comprehensive MLA 8th Edition citation validation strategy following
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


class MLAFormatStrategy(CitationFormatStrategy):
    """
    MLA 8th Edition citation format validation strategy.
    
    Provides comprehensive validation for MLA-style citations including
    journal articles, books, web sources, and other citation types.
    """
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self._citation_type_cache: Dict[str, str] = {}
    
    @property
    def format_name(self) -> str:
        return "MLA"
    
    @property
    def format_version(self) -> str:
        return "8th Edition"
    
    @property
    def supported_types(self) -> List[str]:
        return [
            "journal_article",
            "book",
            "book_chapter", 
            "web_source",
            "conference_paper",
            "thesis",
            "newspaper",
            "magazine",
            "anthology",
            "interview",
            "film",
            "artwork"
        ]
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Comprehensive MLA 8th Edition regex patterns.
        
        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            # Author patterns (MLA uses full names, not initials)
            "single_author": r"^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\.",
            "multiple_authors": r"^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*and\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\.",
            "et_al": r"[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*et\s*al\.",
            "corporate_author": r"^[A-Z][A-Za-z\s&,\.]+\.",
            
            # Title patterns (MLA uses title case, in quotes for articles)
            "article_title_quotes": r'"[A-Z][^"]*\.?"',
            "book_title_italics": r"\*[A-Z][^*]+\*",
            "title_case": r"[A-Z][A-Za-z\s]*(?:[A-Z][A-Za-z\s]*)*",
            "with_subtitle": r"[A-Z][A-Za-z\s]*:\s*[A-Z][A-Za-z\s]*",
            
            # Container patterns (italicized journals, websites, etc.)
            "container_italics": r"\*[A-Z][A-Za-z\s&:,-]+\*",
            "container_name": r"[A-Z][A-Za-z\s&:,-]+[A-Za-z]",
            
            # Date patterns (MLA: Day Month Year format)
            "full_date": r"\d{1,2}\s+[A-Za-z]+\s+\d{4}",  # 15 May 2020
            "month_year": r"[A-Za-z]+\s+\d{4}",  # May 2020
            "year_only": r"\d{4}",  # 2020
            
            # Page and location patterns
            "page_range": r"pp\.\s*\d+[-–]\d+",
            "single_page": r"p\.\s*\d+",
            "no_prefix_pages": r"\d+[-–]\d+",
            "volume_issue": r"vol\.\s*\d+,\s*no\.\s*\d+",
            
            # Web and digital patterns
            "url_pattern": r"https?://[^\s,]+",
            "doi_pattern": r"doi:10\.\d+/[^\s]+",
            "accessed_date": r"Accessed\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}",
            
            # Complete citation patterns for different types
            "journal_article": r"^[A-Z][a-z]+.*\.\s*\"[^\"]+\.?\"\s*\*[^*]+\*.*\d{4}.*pp?\.\s*\d+",
            "book_citation": r"^[A-Z][a-z]+.*\.\s*\*[^*]+\*\.",
            "web_source": r"^[A-Z][a-z]+.*\.\s*\"[^\"]+\.?\".*\d{4}.*[Ww]eb",
            
            # Structure patterns
            "proper_ending": r"\.$",
            "double_spaces": r"\s{2,}",
            "title_in_quotes": r'"[^"]+"',
            "container_in_italics": r"\*[^*]+\*"
        }
    
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """
        Validate a list of citations against MLA 8th Edition format.
        
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
            all_warnings.append("Low overall confidence - many citations may not follow MLA format")
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
        MLA-specific validation logic.
        
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
        
        # Validate title format
        title_valid, title_errors, title_evidence = self._validate_title_format(citation, components, citation_type)
        errors.extend(title_errors)
        evidence.extend(title_evidence)
        
        # Validate container format
        container_valid, container_errors, container_evidence = self._validate_container_format(citation, components, citation_type)
        errors.extend(container_errors)
        evidence.extend(container_evidence)
        
        # Validate publication info
        pub_valid, pub_errors, pub_evidence = self._validate_publication_info(citation, components, citation_type)
        errors.extend(pub_errors)
        evidence.extend(pub_evidence)
        
        # Validate structure
        structure_valid, structure_errors, structure_evidence = self._validate_structure(citation)
        errors.extend(structure_errors)
        evidence.extend(structure_evidence)
        
        # Overall validity
        is_valid = (author_valid and title_valid and container_valid and 
                   pub_valid and structure_valid and len(errors) == 0)
        
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
        if ('"' in citation and '*' in citation and 
            any(indicator in citation_lower for indicator in ["vol.", "volume", "pp.", "no."])):
            citation_type = "journal_article"
        # Book indicators
        elif ('*' in citation and 
              any(indicator in citation_lower for indicator in ["publisher", "press", "university"])):
            citation_type = "book"
        # Web source indicators
        elif (any(indicator in citation_lower for indicator in ["web", "accessed", "http", "www."])):
            citation_type = "web_source"
        # Newspaper/magazine indicators
        elif (any(indicator in citation_lower for indicator in ["times", "post", "magazine", "news"])):
            citation_type = "newspaper"
        else:
            citation_type = "unknown"
        
        self._citation_type_cache[citation] = citation_type
        return citation_type
    
    def _extract_citation_components(self, citation: str) -> Dict[str, Optional[str]]:
        """Extract key components from a citation."""
        components = {
            "author": None,
            "title": None,
            "container": None,
            "date": None,
            "pages": None,
            "url": None,
            "access_date": None
        }
        
        # Extract title in quotes
        title_match = re.search(r'"([^"]+)"', citation)
        if title_match:
            components["title"] = title_match.group(1)
        
        # Extract container in italics (represented by asterisks)
        container_match = re.search(r'\*([^*]+)\*', citation)
        if container_match:
            components["container"] = container_match.group(1)
        
        # Extract URL
        url_match = re.search(r'(https?://[^\s,]+)', citation)
        if url_match:
            components["url"] = url_match.group(1)
        
        # Extract date (various formats)
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{4}|\d{4})', citation)
        if date_match:
            components["date"] = date_match.group(1)
        
        # Extract access date
        access_match = re.search(r'Accessed\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', citation)
        if access_match:
            components["access_date"] = access_match.group(1)
        
        # Extract page information
        page_match = re.search(r'(pp?\.\s*\d+[-–]?\d*)', citation)
        if page_match:
            components["pages"] = page_match.group(1)
        
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
            errors.append("Author format does not match MLA style (should be: Last, First Middle.)")
            confidence = 0.0
        
        # Check for MLA-specific author issues
        if re.search(r'\b[A-Z]\.\s*[A-Z]\.', citation):
            errors.append("MLA uses full first names, not initials")
        
        if ' & ' in citation:
            errors.append("Use 'and' instead of '&' for multiple authors in MLA")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_title_format(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate title formatting based on citation type."""
        errors = []
        evidence = []
        
        if citation_type in ["journal_article", "web_source", "newspaper"]:
            # Articles should have titles in quotes
            if '"' not in citation:
                errors.append("Article titles should be in quotation marks")
            else:
                title_match = re.search(r'"([^"]+)"', citation)
                if title_match:
                    title = title_match.group(1)
                    # Check title case (MLA uses title case)
                    if title[0].isupper():
                        evidence.append(ValidationEvidence(
                            pattern_matched="title_case",
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
    
    def _validate_container_format(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate container formatting."""
        errors = []
        evidence = []
        
        # Check for container in italics
        if components.get("container"):
            evidence.append(ValidationEvidence(
                pattern_matched="container_name",
                confidence_score=0.8,
                rule_applied="container_format_validation",
                context={"container": components["container"]}
            ))
        else:
            errors.append("Container (journal, website, etc.) not found or not properly formatted")
        
        # Check for proper italicization
        if citation_type in ["journal_article", "book", "web_source"]:
            if '*' not in citation:
                errors.append("Container should be italicized (use asterisks)")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_publication_info(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate publication information."""
        errors = []
        evidence = []
        
        # Check for date information
        if components.get("date"):
            date_pattern = self.get_compiled_pattern("full_date")
            if date_pattern and date_pattern.search(citation):
                evidence.append(ValidationEvidence(
                    pattern_matched="full_date",
                    confidence_score=0.9,
                    rule_applied="publication_info_validation",
                    context={"date": components["date"]}
                ))
            else:
                # Check other date formats
                month_year = self.get_compiled_pattern("month_year")
                year_only = self.get_compiled_pattern("year_only")
                if month_year and month_year.search(citation):
                    evidence.append(ValidationEvidence(
                        pattern_matched="month_year",
                        confidence_score=0.7,
                        rule_applied="publication_info_validation",
                        context={"date": components["date"]}
                    ))
                elif year_only and year_only.search(citation):
                    evidence.append(ValidationEvidence(
                        pattern_matched="year_only",
                        confidence_score=0.6,
                        rule_applied="publication_info_validation",
                        context={"date": components["date"]}
                    ))
        
        # Check for page information
        if citation_type == "journal_article" and components.get("pages"):
            evidence.append(ValidationEvidence(
                pattern_matched="page_range",
                confidence_score=0.7,
                rule_applied="publication_info_validation",
                context={"pages": components["pages"]}
            ))
        
        # Check for web access date
        if citation_type == "web_source":
            if components.get("access_date"):
                evidence.append(ValidationEvidence(
                    pattern_matched="accessed_date",
                    confidence_score=0.8,
                    rule_applied="publication_info_validation",
                    context={"access_date": components["access_date"]}
                ))
            elif components.get("url") and not components.get("access_date"):
                errors.append("Web sources should include access date")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_structure(self, citation: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate overall citation structure."""
        errors = []
        evidence = []
        
        # Check for proper ending
        if citation.endswith('.'):
            evidence.append(ValidationEvidence(
                pattern_matched="proper_ending",
                confidence_score=0.6,
                rule_applied="structure_validation",
                context={"has_proper_ending": True}
            ))
        else:
            errors.append("Citation should end with a period")
        
        # Check for double spaces
        double_spaces = self.get_compiled_pattern("double_spaces")
        if double_spaces and double_spaces.search(citation):
            errors.append("Citation contains double spaces")
        
        # Check for proper punctuation sequence
        if re.search(r'[,;:]{2,}', citation):
            errors.append("Citation contains improper punctuation sequence")
        
        return len(errors) == 0, errors, evidence
    
    def generate_suggestions(self, errors: List[str]) -> List[str]:
        """Generate suggestions based on validation errors."""
        suggestions = []
        
        if any("author" in error.lower() for error in errors):
            suggestions.append("Use format: Last, First Middle. for authors")
            suggestions.append("Use 'and' instead of '&' between multiple authors")
        
        if any("title" in error.lower() for error in errors):
            suggestions.append("Put article titles in quotation marks")
            suggestions.append("Italicize book and journal titles")
            suggestions.append("Use title case for all titles")
        
        if any("container" in error.lower() for error in errors):
            suggestions.append("Italicize container names (journals, websites, books)")
        
        if any("date" in error.lower() for error in errors):
            suggestions.append("Use format: Day Month Year, Month Year, or Year")
            suggestions.append("Include access date for web sources")
        
        if any("structure" in error.lower() for error in errors):
            suggestions.append("End citation with a period")
            suggestions.append("Check for proper punctuation throughout")
        
        return suggestions[:3]  # Return top 3 suggestions