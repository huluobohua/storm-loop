"""
IEEE Citation Format Strategy Implementation

Comprehensive IEEE citation validation strategy following
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


class IEEEFormatStrategy(CitationFormatStrategy):
    """
    IEEE citation format validation strategy.
    
    Provides comprehensive validation for IEEE-style citations commonly used
    in engineering and computer science publications.
    """
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self._citation_type_cache: Dict[str, str] = {}
    
    @property
    def format_name(self) -> str:
        return "IEEE"
    
    @property
    def format_version(self) -> str:
        return "IEEE Standard"
    
    @property
    def supported_types(self) -> List[str]:
        return [
            "journal_article",
            "conference_paper",
            "book",
            "book_chapter", 
            "thesis",
            "technical_report",
            "patent",
            "standard",
            "web_source",
            "manual"
        ]
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """
        Comprehensive IEEE citation regex patterns.
        
        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            # Author patterns (IEEE uses initials)
            "single_author": r"^[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+",
            "multiple_authors": r"^[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+(?:,\s*[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+)*",
            "et_al": r"[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+\s*et\s*al\.",
            "corporate_author": r"^[A-Z][A-Za-z\s&,\.]+",
            
            # Title patterns (IEEE uses quotes for articles, italics for books)
            "article_title_quotes": r'"[^"]+\.?"',
            "book_title_italics": r"\*[^*]+\*",
            "sentence_case": r"[A-Z][a-z][^.]*",
            
            # Journal/conference patterns
            "journal_name_italics": r"\*[A-Z][^*]+\*",
            "conference_name": r"[A-Z][A-Za-z\s&]+(Conference|Symposium|Workshop)",
            "abbreviated_journal": r"\*[A-Z][A-Za-z\.\s]+\*",
            
            # Volume/issue/page patterns
            "volume_issue_pages": r"vol\.\s*\d+,\s*no\.\s*\d+,\s*pp\.\s*\d+[-–]\d+",
            "volume_pages": r"vol\.\s*\d+,\s*pp\.\s*\d+[-–]\d+",
            "page_range": r"pp\.\s*\d+[-–]\d+",
            "single_page": r"p\.\s*\d+",
            
            # Date patterns (IEEE: Month Year or Year)
            "month_year": r"[A-Z][a-z]+\.?\s+\d{4}",
            "year_only": r"\d{4}",
            "month_abbreviated": r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4}",
            
            # Technical patterns
            "doi_pattern": r"doi:\s*10\.\d+/[^\s]+",
            "url_pattern": r"https?://[^\s,]+",
            "tech_report": r"Tech\.\s*Rep\.",
            "patent_number": r"U\.S\.\s*Patent\s+\d+",
            
            # Complete citation patterns
            "journal_article": r"^[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+.*\"[^\"]+\".*\*[^*]+\*.*vol\.\s*\d+.*\d{4}",
            "conference_paper": r"^[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+.*\"[^\"]+\".*[Cc]onf\.",
            "book_citation": r"^[A-Z]\.\s*[A-Z]?\.\s*[A-Z][a-z]+.*\*[^*]+\*.*\d{4}",
            
            # Structure patterns
            "proper_ending": r"\.$",
            "double_spaces": r"\s{2,}",
            "numbered_reference": r"^\[\d+\]",
            "in_text_citation": r"\[\d+\]"
        }
    
    def validate(self, citations: List[str]) -> FormatValidationResult:
        """
        Validate a list of citations against IEEE format.
        
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
            all_warnings.append("Low overall confidence - many citations may not follow IEEE format")
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
        IEEE-specific validation logic.
        
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
        
        # Validate publication info
        pub_valid, pub_errors, pub_evidence = self._validate_publication_info(citation, components, citation_type)
        errors.extend(pub_errors)
        evidence.extend(pub_evidence)
        
        # Validate technical details
        tech_valid, tech_errors, tech_evidence = self._validate_technical_details(citation, components, citation_type)
        errors.extend(tech_errors)
        evidence.extend(tech_evidence)
        
        # Validate structure
        structure_valid, structure_errors, structure_evidence = self._validate_structure(citation)
        errors.extend(structure_errors)
        evidence.extend(structure_evidence)
        
        # Overall validity
        is_valid = (author_valid and title_valid and pub_valid and 
                   tech_valid and structure_valid and len(errors) == 0)
        
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
        """Detect the type of citation (journal, conference, book, etc.)."""
        if citation in self._citation_type_cache:
            return self._citation_type_cache[citation]
        
        citation_lower = citation.lower()
        
        # Conference paper indicators
        if any(indicator in citation_lower for indicator in ["conf.", "proc.", "symposium", "workshop"]):
            citation_type = "conference_paper"
        # Journal article indicators
        elif ('"' in citation and '*' in citation and 
              any(indicator in citation_lower for indicator in ["vol.", "no.", "pp."])):
            citation_type = "journal_article"
        # Technical report indicators
        elif any(indicator in citation_lower for indicator in ["tech. rep.", "technical report"]):
            citation_type = "technical_report"
        # Patent indicators
        elif any(indicator in citation_lower for indicator in ["patent", "u.s. patent"]):
            citation_type = "patent"
        # Book indicators
        elif ('*' in citation and not '"' in citation):
            citation_type = "book"
        # Web source indicators
        elif any(indicator in citation_lower for indicator in ["http", "www.", "url"]):
            citation_type = "web_source"
        else:
            citation_type = "unknown"
        
        self._citation_type_cache[citation] = citation_type
        return citation_type
    
    def _extract_citation_components(self, citation: str) -> Dict[str, Optional[str]]:
        """Extract key components from a citation."""
        components = {
            "author": None,
            "title": None,
            "journal": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "year": None,
            "doi": None,
            "url": None
        }
        
        # Extract title in quotes
        title_match = re.search(r'"([^"]+)"', citation)
        if title_match:
            components["title"] = title_match.group(1)
        
        # Extract journal/publication in italics
        journal_match = re.search(r'\*([^*]+)\*', citation)
        if journal_match:
            components["journal"] = journal_match.group(1)
        
        # Extract volume, issue, pages
        vol_issue_pages = re.search(r'vol\.\s*(\d+),\s*no\.\s*(\d+),\s*pp\.\s*(\d+[-–]\d+)', citation)
        if vol_issue_pages:
            components["volume"] = vol_issue_pages.group(1)
            components["issue"] = vol_issue_pages.group(2)
            components["pages"] = vol_issue_pages.group(3)
        else:
            # Try volume and pages only
            vol_pages = re.search(r'vol\.\s*(\d+),\s*pp\.\s*(\d+[-–]\d+)', citation)
            if vol_pages:
                components["volume"] = vol_pages.group(1)
                components["pages"] = vol_pages.group(2)
        
        # Extract year
        year_match = re.search(r'(\d{4})', citation)
        if year_match:
            components["year"] = year_match.group(1)
        
        # Extract DOI
        doi_match = re.search(r'doi:\s*(10\.\d+/[^\s]+)', citation)
        if doi_match:
            components["doi"] = doi_match.group(1)
        
        # Extract URL
        url_match = re.search(r'(https?://[^\s,]+)', citation)
        if url_match:
            components["url"] = url_match.group(1)
        
        return components
    
    def _validate_author_format(self, citation: str, components: Dict[str, Optional[str]]) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate author formatting."""
        errors = []
        evidence = []
        
        # Check for basic author pattern (IEEE uses initials)
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
            errors.append("Author format does not match IEEE style (should use initials: F. M. Last)")
            confidence = 0.0
        
        # Check for IEEE-specific author issues
        if re.search(r'[A-Z][a-z]+,\s*[A-Z][a-z]+', citation):
            errors.append("IEEE uses initials, not full first names")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_title_format(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate title formatting based on citation type."""
        errors = []
        evidence = []
        
        if citation_type in ["journal_article", "conference_paper"]:
            # Articles and papers should have titles in quotes
            if '"' not in citation:
                errors.append("Article/paper titles should be in quotation marks")
            else:
                title_match = re.search(r'"([^"]+)"', citation)
                if title_match:
                    title = title_match.group(1)
                    evidence.append(ValidationEvidence(
                        pattern_matched="article_title_quotes",
                        confidence_score=0.8,
                        rule_applied="title_format_validation",
                        context={"title": title, "type": citation_type}
                    ))
        
        elif citation_type == "book":
            # Books should have titles in italics
            if '*' not in citation:
                errors.append("Book titles should be in italics")
            else:
                title_match = re.search(r'\*([^*]+)\*', citation)
                if title_match:
                    title = title_match.group(1)
                    evidence.append(ValidationEvidence(
                        pattern_matched="book_title_italics",
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
                    pattern_matched="journal_name_italics",
                    confidence_score=0.8,
                    rule_applied="publication_info_validation",
                    context={"journal": components["journal"]}
                ))
            else:
                errors.append("Journal name not found or not properly italicized")
            
            # Check for volume/issue/page information
            if components.get("volume") and components.get("pages"):
                evidence.append(ValidationEvidence(
                    pattern_matched="volume_pages",
                    confidence_score=0.9,
                    rule_applied="publication_info_validation",
                    context={"volume": components["volume"], "pages": components["pages"]}
                ))
            else:
                errors.append("Volume and page information missing or improperly formatted")
        
        elif citation_type == "conference_paper":
            # Check for conference name
            if "conf" in citation.lower() or "proc" in citation.lower():
                evidence.append(ValidationEvidence(
                    pattern_matched="conference_name",
                    confidence_score=0.7,
                    rule_applied="publication_info_validation",
                    context={"type": "conference"}
                ))
            else:
                errors.append("Conference information not clearly indicated")
        
        # Check for year
        if components.get("year"):
            evidence.append(ValidationEvidence(
                pattern_matched="year_only",
                confidence_score=0.7,
                rule_applied="publication_info_validation",
                context={"year": components["year"]}
            ))
        else:
            errors.append("Publication year not found")
        
        return len(errors) == 0, errors, evidence
    
    def _validate_technical_details(self, citation: str, components: Dict[str, Optional[str]], citation_type: str) -> Tuple[bool, List[str], List[ValidationEvidence]]:
        """Validate technical aspects specific to IEEE format."""
        errors = []
        evidence = []
        
        # Check for DOI (encouraged in IEEE)
        if components.get("doi"):
            evidence.append(ValidationEvidence(
                pattern_matched="doi_pattern",
                confidence_score=0.8,
                rule_applied="technical_validation",
                context={"doi": components["doi"]}
            ))
        
        # Check for proper abbreviations
        if citation_type == "journal_article":
            # IEEE encourages abbreviated journal names
            if re.search(r'\b(IEEE|ACM|ASME|AIAA)\b', citation):
                evidence.append(ValidationEvidence(
                    pattern_matched="technical_abbreviation",
                    confidence_score=0.7,
                    rule_applied="technical_validation",
                    context={"type": "standard_abbreviation"}
                ))
        
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
        
        # IEEE specific: Check for numbered reference style (optional)
        if re.match(r'^\[\d+\]', citation):
            evidence.append(ValidationEvidence(
                pattern_matched="numbered_reference",
                confidence_score=0.5,
                rule_applied="structure_validation",
                context={"numbered_style": True}
            ))
        
        return len(errors) == 0, errors, evidence
    
    def generate_suggestions(self, errors: List[str]) -> List[str]:
        """Generate suggestions based on validation errors."""
        suggestions = []
        
        if any("author" in error.lower() for error in errors):
            suggestions.append("Use initials format: F. M. Last for authors")
            suggestions.append("Separate multiple authors with commas")
        
        if any("title" in error.lower() for error in errors):
            suggestions.append("Put article/paper titles in quotation marks")
            suggestions.append("Italicize book and journal titles")
        
        if any("journal" in error.lower() for error in errors):
            suggestions.append("Italicize journal names")
            suggestions.append("Use standard abbreviations when possible")
        
        if any("volume" in error.lower() or "page" in error.lower() for error in errors):
            suggestions.append("Use format: vol. X, no. Y, pp. Z-W")
            suggestions.append("Include volume and page information for journal articles")
        
        if any("year" in error.lower() for error in errors):
            suggestions.append("Include publication year")
        
        if any("structure" in error.lower() for error in errors):
            suggestions.append("End citation with a period")
            suggestions.append("Check for proper spacing throughout")
        
        return suggestions[:3]  # Return top 3 suggestions