"""
Real citation format validation with actual implementation for multiple styles.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from ..interfaces import BaseValidator
from ..models import (
    ValidationResult,
    ValidationStatus,
    ResearchData,
    CitationResult,
    CitationStyle
)

logger = logging.getLogger(__name__)


class RealCitationValidator(BaseValidator):
    """Real implementation of citation format validation for multiple academic styles."""
    
    def __init__(self):
        super().__init__(
            name="Real Citation Format Validator",
            version="2.0.0"
        )
        self._config = {
            "strict_mode": False,
            "check_doi": True,
            "check_urls": True,
            "validate_dates": True,
            "check_completeness": True
        }
        
        # Citation style patterns and rules
        self._style_patterns = {
            CitationStyle.APA: self._get_apa_patterns(),
            CitationStyle.MLA: self._get_mla_patterns(),
            CitationStyle.CHICAGO: self._get_chicago_patterns(),
            CitationStyle.IEEE: self._get_ieee_patterns(),
            CitationStyle.HARVARD: self._get_harvard_patterns()
        }
        
    def _get_apa_patterns(self) -> Dict[str, Any]:
        """Get APA 7th edition citation patterns."""
        return {
            # Author patterns
            "single_author": r"^([A-Z][a-z\-\']+),\s+([A-Z]\.(?:\s*[A-Z]\.)*)",
            "multiple_authors": r"^([A-Z][a-z\-\']+),\s+([A-Z]\.(?:\s*[A-Z]\.)*),?\s*(?:&|,)\s*",
            "et_al": r",?\s+et\s+al\.",
            
            # Year pattern
            "year": r"\((\d{4}[a-z]?)\)",
            "in_press": r"\(in\s+press\)",
            "no_date": r"\(n\.d\.\)",
            
            # Title patterns
            "article_title": r"\.\s+([A-Z][^.?!]+[.?!])\s+",
            "book_title": r"\.\s+_([^_]+)_",
            "italics": r"_([^_]+)_|\*([^*]+)\*",
            
            # Journal/Publisher patterns
            "journal": r"_([^_,]+)_,?\s*_?(\d+)?_?\(?(\d+)?\)?,?\s*(\d+[-–]\d+|\d+)",
            "publisher": r"\.\s+([A-Z][^:]+):\s*([^.]+)\.",
            
            # DOI/URL patterns
            "doi": r"https?://doi\.org/(10\.\d{4,}/[-._;()/:\w]+)",
            "url": r"https?://[^\s]+",
            
            # Page numbers
            "pages": r"(\d+)[-–](\d+)",
            "single_page": r"p\.\s*(\d+)",
            "multiple_pages": r"pp\.\s*(\d+[-–]\d+)",
            
            # Volume/Issue
            "volume_issue": r"(\d+)\((\d+)\)",
            
            # Required elements by type
            "required": {
                "journal": ["authors", "year", "title", "journal_name", "volume", "pages"],
                "book": ["authors", "year", "title", "publisher", "location"],
                "chapter": ["authors", "year", "chapter_title", "book_title", "editors", "publisher", "location", "pages"],
                "web": ["authors", "year", "title", "url", "access_date"]
            }
        }
    
    def _get_mla_patterns(self) -> Dict[str, Any]:
        """Get MLA 9th edition citation patterns."""
        return {
            # Author patterns  
            "single_author": r"^([A-Z][a-z\-\']+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.)?)",
            "multiple_authors": r"^([A-Z][a-z\-\']+),\s+([A-Z][a-z]+),?\s+(?:and|,)\s+",
            "et_al": r",?\s+et\s+al\.",
            
            # Title patterns
            "article_title": r'"\s*([^"]+)\s*"',
            "book_title": r"_([^_]+)_|\*([^*]+)\*",
            "container_title": r",\s*_([^_,]+)_,?",
            
            # Publication info
            "publisher": r",\s*([^,]+),\s*(\d{4})",
            "journal_info": r",\s*vol\.\s*(\d+),\s*no\.\s*(\d+),\s*(\d{4}),\s*pp?\.\s*(\d+[-–]\d+)",
            
            # Page numbers
            "pages": r"pp?\.\s*(\d+[-–]\d+|\d+)",
            
            # Web sources
            "web_publisher": r"\.\s*([^,]+),\s*(\d{1,2}\s+\w+\.?\s+\d{4})",
            "access_date": r"Accessed\s+(\d{1,2}\s+\w+\.?\s+\d{4})",
            
            # Required elements
            "required": {
                "journal": ["authors", "article_title", "journal_name", "volume", "issue", "year", "pages"],
                "book": ["authors", "title", "publisher", "year"],
                "web": ["authors", "title", "website", "publisher", "date", "url"]
            }
        }
    
    def _get_chicago_patterns(self) -> Dict[str, Any]:
        """Get Chicago Manual of Style patterns."""
        return {
            # Author patterns (notes style)
            "notes_author": r"^([A-Z][a-z\-\']+)\s+([A-Z][a-z]+(?:\s+[A-Z]\.)?)",
            "bibliography_author": r"^([A-Z][a-z\-\']+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.)?)",
            
            # Title patterns
            "article_title": r'"\s*([^"]+)\s*"',
            "book_title": r"_([^_]+)_|\*([^*]+)\*",
            
            # Publication info
            "publisher_location": r"\(([^:]+):\s*([^,]+),\s*(\d{4})\)",
            "journal_info": r"(\d+),?\s*no\.\s*(\d+)\s*\(([^)]+)\):\s*(\d+[-–]\d+)",
            
            # Notes numbers
            "note_number": r"^\d+\.\s+",
            "ibid": r"^Ibid\.",
            
            # Required elements
            "required": {
                "book_note": ["authors", "title", "location", "publisher", "year", "page"],
                "book_bib": ["authors", "title", "location", "publisher", "year"],
                "journal_note": ["authors", "article_title", "journal", "volume", "issue", "year", "page"],
                "journal_bib": ["authors", "article_title", "journal", "volume", "issue", "year", "pages"]
            }
        }
    
    def _get_ieee_patterns(self) -> Dict[str, Any]:
        """Get IEEE citation patterns."""
        return {
            # Numbered references
            "ref_number": r"^\[(\d+)\]\s*",
            
            # Author patterns
            "authors": r"([A-Z]\.\s*(?:[A-Z]\.\s*)?[A-Z][a-z\-\']+)",
            "and_separator": r"\s+and\s+",
            
            # Title patterns
            "article_title": r'"\s*([^"]+)\s*,"',
            "book_title": r",\s*_([^_]+)_,",
            
            # Publication info
            "journal": r"_([^_]+)_,\s*vol\.\s*(\d+),\s*(?:no\.\s*(\d+),\s*)?pp\.\s*(\d+[-–]\d+),\s*(\w+\.?\s*\d{4})",
            "conference": r"in\s+_([^_]+)_,\s*(\d{4}),\s*pp\.\s*(\d+[-–]\d+)",
            
            # Date formats
            "date": r"(\w+\.?\s+\d{4})",
            
            # Required elements
            "required": {
                "journal": ["ref_number", "authors", "title", "journal", "volume", "pages", "date"],
                "conference": ["ref_number", "authors", "title", "conference", "year", "pages"],
                "book": ["ref_number", "authors", "title", "location", "publisher", "year"]
            }
        }
    
    def _get_harvard_patterns(self) -> Dict[str, Any]:
        """Get Harvard citation patterns."""
        return {
            # Author-date patterns
            "author_date": r"^([A-Z][a-z\-\']+(?:,\s*[A-Z]\.)?(?:\s+(?:&|and)\s+[A-Z][a-z\-\']+(?:,\s*[A-Z]\.)?)*)\s+(\d{4}[a-z]?)",
            "et_al": r"\s+et\s+al\.\s+",
            
            # Title patterns
            "article_title": r",\s*['\"]([^'\"]+)['\"]\s*,",
            "book_title": r",\s*_([^_]+)_",
            
            # Publication info
            "journal": r"_([^_]+)_,\s*(\d+)\((\d+)\),\s*pp?\.\s*(\d+[-–]\d+)",
            "publisher": r",\s*([^,]+),\s*([^.]+)\.",
            
            # Online sources
            "available_at": r"Available\s+at:\s*<([^>]+)>",
            "accessed": r"\[Accessed\s+(\d{1,2}\s+\w+\s+\d{4})\]",
            
            # Required elements
            "required": {
                "journal": ["authors", "year", "title", "journal", "volume", "issue", "pages"],
                "book": ["authors", "year", "title", "publisher", "location"],
                "online": ["authors", "year", "title", "url", "access_date"]
            }
        }
    
    async def validate(self, data: ResearchData) -> ValidationResult:
        """
        Validate citations in research data with real format checking.
        
        Args:
            data: Research data containing citations
            
        Returns:
            Comprehensive validation result
        """
        try:
            if not data.citations:
                return self._create_empty_citations_result()
            
            # Analyze each citation
            citation_results = []
            style_counts = {style: 0 for style in CitationStyle}
            total_score = 0.0
            
            for citation in data.citations:
                result = self._analyze_citation(citation)
                citation_results.append(result)
                
                if result.style != CitationStyle.APA:  # Default if not detected
                    style_counts[result.style] += 1
                
                # Calculate weighted score
                score = (
                    result.format_compliance * 0.4 +
                    result.completeness_score * 0.4 +
                    result.accuracy_score * 0.2
                )
                total_score += score
            
            # Determine dominant style
            dominant_style = max(style_counts.items(), key=lambda x: x[1])[0]
            consistency_score = self._calculate_consistency_score(citation_results, dominant_style)
            
            # Calculate overall metrics
            avg_score = total_score / len(citation_results) if citation_results else 0.0
            
            # Generate detailed analysis
            format_issues = self._analyze_format_issues(citation_results)
            completeness_issues = self._analyze_completeness_issues(citation_results)
            consistency_issues = self._analyze_consistency_issues(citation_results, dominant_style)
            
            # Determine validation status
            if avg_score >= 0.9 and consistency_score >= 0.8:
                status = ValidationStatus.PASSED
            elif avg_score >= 0.7:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            return ValidationResult(
                validator_name=self.name,
                test_name="Citation Format Validation",
                status=status,
                score=avg_score,
                details={
                    "total_citations": len(citation_results),
                    "dominant_style": dominant_style.value,
                    "style_consistency": consistency_score,
                    "format_compliance": sum(r.format_compliance for r in citation_results) / len(citation_results),
                    "completeness_average": sum(r.completeness_score for r in citation_results) / len(citation_results),
                    "accuracy_average": sum(r.accuracy_score for r in citation_results) / len(citation_results),
                    "format_issues": format_issues,
                    "completeness_issues": completeness_issues,
                    "consistency_issues": consistency_issues,
                    "citation_analysis": [self._format_citation_result(r) for r in citation_results[:10]]  # First 10
                },
                recommendations=self._generate_recommendations(
                    citation_results, dominant_style, consistency_score
                ),
                metadata={
                    "validator_version": self.version,
                    "styles_checked": [s.value for s in CitationStyle],
                    "strict_mode": self._config["strict_mode"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Citation validation error: {str(e)}", exc_info=True)
            return self._create_error_result(str(e))
    
    def _analyze_citation(self, citation: str) -> CitationResult:
        """Analyze a single citation for format, completeness, and accuracy."""
        # Detect citation style
        detected_style, confidence = self._detect_citation_style(citation)
        
        # Get patterns for detected style
        patterns = self._style_patterns.get(detected_style, self._style_patterns[CitationStyle.APA])
        
        # Extract components
        components = self._extract_components(citation, patterns)
        
        # Check format compliance
        format_compliance = self._check_format_compliance(citation, detected_style, components)
        
        # Check completeness
        completeness_score = self._check_completeness(components, detected_style, patterns)
        
        # Check accuracy (dates, DOIs, etc.)
        accuracy_score = self._check_accuracy(components, citation)
        
        # Find specific issues
        issues = self._identify_issues(citation, detected_style, components, patterns)
        
        # Generate corrections
        corrections = self._generate_corrections(citation, detected_style, components, issues)
        
        # Format citation correctly
        formatted_citation = self._format_citation(components, detected_style) if corrections else None
        
        return CitationResult(
            citation_text=citation,
            style=detected_style,
            format_compliance=format_compliance,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            issues_found=issues,
            corrections=corrections,
            formatted_citation=formatted_citation
        )
    
    def _detect_citation_style(self, citation: str) -> Tuple[CitationStyle, float]:
        """Detect the citation style used."""
        style_scores = {}
        
        # APA detection
        apa_score = 0.0
        if re.search(r"\(\d{4}[a-z]?\)", citation):  # Year in parentheses
            apa_score += 0.3
        if re.search(r"\.\s+[A-Z][^.]+\.\s+_", citation):  # Title followed by italics
            apa_score += 0.2
        if re.search(r"https?://doi\.org/", citation):  # DOI format
            apa_score += 0.2
        if re.search(r"_\d+_\(\d+\),\s*\d+[-–]\d+", citation):  # Volume(issue), pages
            apa_score += 0.3
        style_scores[CitationStyle.APA] = apa_score
        
        # MLA detection
        mla_score = 0.0
        if re.search(r'"\s*[^"]+\s*"', citation):  # Quoted article title
            mla_score += 0.3
        if re.search(r"pp?\.\s*\d+[-–]\d+", citation):  # pp. or p. before pages
            mla_score += 0.2
        if re.search(r"vol\.\s*\d+,\s*no\.\s*\d+", citation):  # vol. X, no. Y
            mla_score += 0.3
        if re.search(r"Accessed\s+\d{1,2}\s+\w+\.?\s+\d{4}", citation):  # Access date
            mla_score += 0.2
        style_scores[CitationStyle.MLA] = mla_score
        
        # Chicago detection
        chicago_score = 0.0
        if re.search(r"^\d+\.\s+", citation):  # Numbered note
            chicago_score += 0.3
        if re.search(r"\([^:]+:\s*[^,]+,\s*\d{4}\)", citation):  # (Location: Publisher, Year)
            chicago_score += 0.3
        if re.search(r"Ibid\.", citation, re.IGNORECASE):  # Ibid reference
            chicago_score += 0.4
        style_scores[CitationStyle.CHICAGO] = chicago_score
        
        # IEEE detection
        ieee_score = 0.0
        if re.search(r"^\[\d+\]\s*", citation):  # [1] reference number
            ieee_score += 0.4
        if re.search(r"vol\.\s*\d+,\s*(?:no\.\s*\d+,\s*)?pp\.\s*\d+[-–]\d+", citation):  # IEEE volume format
            ieee_score += 0.3
        if re.search(r"in\s+_[^_]+_,\s*\d{4}", citation):  # in Conference Name
            ieee_score += 0.3
        style_scores[CitationStyle.IEEE] = ieee_score
        
        # Harvard detection
        harvard_score = 0.0
        if re.search(r"^[A-Z][a-z\-\']+(?:\s+(?:&|and)\s+[A-Z][a-z\-\']+)*\s+\d{4}[a-z]?", citation):
            harvard_score += 0.4
        if re.search(r"Available\s+at:\s*<[^>]+>", citation):  # Available at: <URL>
            harvard_score += 0.3
        if re.search(r"\[Accessed\s+\d{1,2}\s+\w+\s+\d{4}\]", citation):  # [Accessed date]
            harvard_score += 0.3
        style_scores[CitationStyle.HARVARD] = harvard_score
        
        # Find best match
        best_style = max(style_scores.items(), key=lambda x: x[1])
        
        # Default to APA if no clear match
        if best_style[1] < 0.3:
            return CitationStyle.APA, 0.3
        
        return best_style[0], best_style[1]
    
    def _extract_components(self, citation: str, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Extract citation components based on patterns."""
        components = {
            "authors": [],
            "year": None,
            "title": None,
            "journal": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "publisher": None,
            "location": None,
            "doi": None,
            "url": None,
            "access_date": None
        }
        
        # Extract authors
        if "single_author" in patterns:
            author_match = re.search(patterns["single_author"], citation)
            if author_match:
                components["authors"].append(author_match.group(0))
        
        if "multiple_authors" in patterns:
            authors = re.findall(patterns["authors"] if "authors" in patterns else patterns["single_author"], citation)
            components["authors"].extend(authors)
        
        # Extract year
        if "year" in patterns:
            year_match = re.search(patterns["year"], citation)
            if year_match:
                components["year"] = year_match.group(1)
        
        # Extract title
        if "article_title" in patterns:
            title_match = re.search(patterns["article_title"], citation)
            if title_match:
                components["title"] = title_match.group(1)
        elif "book_title" in patterns:
            title_match = re.search(patterns["book_title"], citation)
            if title_match:
                components["title"] = title_match.group(1)
        
        # Extract journal
        if "journal" in patterns:
            journal_match = re.search(patterns["journal"], citation)
            if journal_match:
                components["journal"] = journal_match.group(1)
                if len(journal_match.groups()) > 1:
                    components["volume"] = journal_match.group(2)
                if len(journal_match.groups()) > 2:
                    components["issue"] = journal_match.group(3)
                if len(journal_match.groups()) > 3:
                    components["pages"] = journal_match.group(4)
        
        # Extract DOI
        if "doi" in patterns:
            doi_match = re.search(patterns["doi"], citation)
            if doi_match:
                components["doi"] = doi_match.group(1)
        
        # Extract URL
        if "url" in patterns:
            url_match = re.search(patterns["url"], citation)
            if url_match:
                components["url"] = url_match.group(0)
        
        # Extract pages (if not already extracted)
        if not components["pages"] and "pages" in patterns:
            pages_match = re.search(patterns["pages"], citation)
            if pages_match:
                components["pages"] = pages_match.group(0)
        
        return components
    
    def _check_format_compliance(self, citation: str, style: CitationStyle, components: Dict[str, Any]) -> float:
        """Check how well the citation follows format rules."""
        score = 0.0
        checks = 0
        
        if style == CitationStyle.APA:
            # Check author format (Last, F. M.)
            checks += 1
            if components["authors"]:
                if all(re.match(r"[A-Z][a-z\-\']+,\s+[A-Z]\.", author) for author in components["authors"][:3]):
                    score += 1.0
            
            # Check year in parentheses
            checks += 1
            if re.search(r"\(\d{4}[a-z]?\)", citation):
                score += 1.0
            
            # Check italics formatting
            checks += 1
            if re.search(r"_[^_]+_", citation) or re.search(r"\*[^*]+\*", citation):
                score += 1.0
            
            # Check DOI format
            if components["doi"]:
                checks += 1
                if re.match(r"10\.\d{4,}/[-._;()/:\w]+", components["doi"]):
                    score += 1.0
                    
        elif style == CitationStyle.MLA:
            # Check author format
            checks += 1
            if components["authors"]:
                if re.match(r"[A-Z][a-z\-\']+,\s+[A-Z][a-z]+", components["authors"][0]):
                    score += 1.0
            
            # Check quoted titles
            checks += 1
            if re.search(r'"\s*[^"]+\s*"', citation):
                score += 1.0
            
            # Check page format
            checks += 1
            if re.search(r"pp?\.\s*\d+", citation):
                score += 1.0
                
        elif style == CitationStyle.IEEE:
            # Check reference number
            checks += 1
            if re.match(r"^\[\d+\]", citation):
                score += 1.0
            
            # Check author initials first
            checks += 1
            if components["authors"]:
                if any(re.match(r"[A-Z]\.\s*(?:[A-Z]\.\s*)?[A-Z][a-z]+", author) for author in components["authors"]):
                    score += 1.0
            
            # Check abbreviated months
            checks += 1
            if re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4}", citation):
                score += 1.0
        
        return score / checks if checks > 0 else 0.0
    
    def _check_completeness(self, components: Dict[str, Any], style: CitationStyle, patterns: Dict[str, Any]) -> float:
        """Check if all required elements are present."""
        # Determine citation type
        citation_type = self._determine_citation_type(components)
        
        # Get required elements for this style and type
        required_elements = patterns.get("required", {}).get(citation_type, [])
        
        if not required_elements:
            # Default required elements
            if citation_type == "journal":
                required_elements = ["authors", "year", "title", "journal", "volume", "pages"]
            elif citation_type == "book":
                required_elements = ["authors", "year", "title", "publisher"]
            else:
                required_elements = ["authors", "year", "title"]
        
        # Check presence of required elements
        present_count = 0
        for element in required_elements:
            if element == "authors" and components["authors"]:
                present_count += 1
            elif element == "journal_name":
                if components["journal"]:
                    present_count += 1
            elif element in components and components[element]:
                present_count += 1
        
        return present_count / len(required_elements) if required_elements else 0.0
    
    def _check_accuracy(self, components: Dict[str, Any], citation: str) -> float:
        """Check accuracy of dates, DOIs, URLs, etc."""
        score = 0.0
        checks = 0
        
        # Check year validity
        if components["year"]:
            checks += 1
            try:
                year = int(components["year"][:4])  # Handle year with letters (2023a)
                if 1900 <= year <= datetime.now().year + 1:  # Allow next year for in press
                    score += 1.0
            except:
                pass
        
        # Check DOI format
        if components["doi"]:
            checks += 1
            if re.match(r"10\.\d{4,}/[-._;()/:\w]+", components["doi"]):
                score += 1.0
        
        # Check URL validity
        if components["url"]:
            checks += 1
            if re.match(r"https?://[^\s]+\.[^\s]+", components["url"]):
                score += 1.0
        
        # Check page number logic
        if components["pages"]:
            checks += 1
            page_match = re.match(r"(\d+)[-–](\d+)", components["pages"])
            if page_match:
                start_page = int(page_match.group(1))
                end_page = int(page_match.group(2))
                if start_page < end_page and end_page - start_page < 1000:  # Reasonable range
                    score += 1.0
            elif re.match(r"\d+", components["pages"]):  # Single page
                score += 1.0
        
        # Check volume/issue numbers
        if components["volume"]:
            checks += 1
            try:
                vol = int(components["volume"])
                if 1 <= vol <= 500:  # Reasonable volume range
                    score += 1.0
            except:
                pass
        
        return score / checks if checks > 0 else 1.0  # Default to accurate if no checks
    
    def _determine_citation_type(self, components: Dict[str, Any]) -> str:
        """Determine the type of citation."""
        if components["journal"] or components["volume"]:
            return "journal"
        elif components["publisher"]:
            return "book"
        elif components["url"] and not components["journal"]:
            return "web"
        elif "conference" in str(components.get("title", "")).lower():
            return "conference"
        else:
            return "other"
    
    def _identify_issues(self, citation: str, style: CitationStyle, components: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Identify specific formatting issues."""
        issues = []
        
        # Style-specific checks
        if style == CitationStyle.APA:
            # Check ampersand usage
            if " and " in citation and len(components["authors"]) > 1:
                issues.append("Use '&' instead of 'and' between authors in APA style")
            
            # Check italics
            if components["journal"] and not re.search(rf"_{re.escape(components['journal'])}_", citation):
                issues.append("Journal name should be italicized")
            
            # Check DOI format
            if components["url"] and "doi.org" in components["url"] and not components["doi"]:
                issues.append("Use 'https://doi.org/' format for DOIs")
                
        elif style == CitationStyle.MLA:
            # Check date format
            if components["access_date"] and not re.search(r"\d{1,2}\s+\w+\.?\s+\d{4}", components["access_date"]):
                issues.append("Access date should be in 'Day Month Year' format")
            
            # Check container title
            if components["journal"] and not re.search(r'_[^_]*_', citation):
                issues.append("Container title should be italicized")
                
        elif style == CitationStyle.IEEE:
            # Check reference number
            if not re.match(r"^\[\d+\]", citation):
                issues.append("IEEE citations should start with reference number [n]")
            
            # Check month abbreviation
            if re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)", citation):
                issues.append("Use abbreviated month names in IEEE style")
        
        # Common issues
        if not components["authors"]:
            issues.append("Missing author information")
        
        if not components["year"]:
            issues.append("Missing publication year")
        
        if not components["title"]:
            issues.append("Missing title")
        
        # Check for mixed formatting
        if re.search(r"_[^_]+_", citation) and re.search(r"\*[^*]+\*", citation):
            issues.append("Inconsistent italics formatting")
        
        return issues
    
    def _generate_corrections(self, citation: str, style: CitationStyle, components: Dict[str, Any], issues: List[str]) -> List[str]:
        """Generate correction suggestions."""
        corrections = []
        
        for issue in issues:
            if "Use '&' instead of 'and'" in issue:
                corrections.append("Replace ' and ' with ' & ' before the last author")
            
            elif "should be italicized" in issue:
                corrections.append(f"Format with italics using underscores or HTML tags")
            
            elif "reference number" in issue:
                corrections.append("Add reference number at the beginning: [1] Author...")
            
            elif "Missing author" in issue:
                corrections.append("Add author name(s) at the beginning of the citation")
            
            elif "Missing publication year" in issue:
                corrections.append(f"Add publication year in {style.value} format")
            
            elif "abbreviated month" in issue:
                corrections.append("Use three-letter month abbreviations: Jan., Feb., Mar., etc.")
        
        return corrections
    
    def _format_citation(self, components: Dict[str, Any], style: CitationStyle) -> Optional[str]:
        """Format citation correctly according to style."""
        if not components["authors"] or not components["title"]:
            return None
        
        try:
            if style == CitationStyle.APA:
                # Format authors
                authors = self._format_apa_authors(components["authors"])
                
                # Build citation
                parts = [authors]
                
                if components["year"]:
                    parts.append(f"({components['year']})")
                else:
                    parts.append("(n.d.)")
                
                parts.append(components["title"])
                
                if components["journal"]:
                    journal_part = f"_{components['journal']}_"
                    if components["volume"]:
                        journal_part += f", _{components['volume']}_"
                        if components["issue"]:
                            journal_part += f"({components['issue']})"
                    if components["pages"]:
                        journal_part += f", {components['pages']}"
                    parts.append(journal_part)
                
                if components["doi"]:
                    parts.append(f"https://doi.org/{components['doi']}")
                elif components["url"]:
                    parts.append(components["url"])
                
                return ". ".join(parts) + "."
                
            # Add other styles as needed
            
        except Exception as e:
            logger.error(f"Error formatting citation: {str(e)}")
            return None
    
    def _format_apa_authors(self, authors: List[str]) -> str:
        """Format authors in APA style."""
        if not authors:
            return ""
        
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]}"
        elif len(authors) <= 20:
            return ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            # 21+ authors: list first 19, ... , last author
            return ", ".join(authors[:19]) + f", ... {authors[-1]}"
    
    def _calculate_consistency_score(self, results: List[CitationResult], dominant_style: CitationStyle) -> float:
        """Calculate how consistently citations follow the same style."""
        if not results:
            return 1.0
        
        matching_style_count = sum(1 for r in results if r.style == dominant_style)
        return matching_style_count / len(results)
    
    def _analyze_format_issues(self, results: List[CitationResult]) -> Dict[str, int]:
        """Analyze common format issues across all citations."""
        issue_counts = {}
        
        for result in results:
            for issue in result.issues_found:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_completeness_issues(self, results: List[CitationResult]) -> Dict[str, float]:
        """Analyze completeness across different citation types."""
        type_completeness = {}
        type_counts = {}
        
        for result in results:
            # Simplified type detection
            if "journal" in result.citation_text.lower():
                ctype = "journal"
            elif "book" in result.citation_text.lower() or "press" in result.citation_text.lower():
                ctype = "book"
            elif "http" in result.citation_text:
                ctype = "web"
            else:
                ctype = "other"
            
            if ctype not in type_completeness:
                type_completeness[ctype] = 0.0
                type_counts[ctype] = 0
            
            type_completeness[ctype] += result.completeness_score
            type_counts[ctype] += 1
        
        # Calculate averages
        return {
            ctype: score / type_counts[ctype] 
            for ctype, score in type_completeness.items()
        }
    
    def _analyze_consistency_issues(self, results: List[CitationResult], dominant_style: CitationStyle) -> List[str]:
        """Identify consistency issues across citations."""
        issues = []
        
        # Check style mixing
        styles_used = set(r.style for r in results)
        if len(styles_used) > 1:
            issues.append(f"Mixed citation styles detected: {', '.join(s.value for s in styles_used)}")
        
        # Check format variations within same style
        if dominant_style == CitationStyle.APA:
            # Check for consistent use of "&" vs "and"
            and_count = sum(1 for r in results if " and " in r.citation_text)
            ampersand_count = sum(1 for r in results if " & " in r.citation_text)
            
            if and_count > 0 and ampersand_count > 0:
                issues.append("Inconsistent use of '&' vs 'and' between citations")
        
        # Check italics formatting consistency
        underscore_count = sum(1 for r in results if "_" in r.citation_text)
        asterisk_count = sum(1 for r in results if "*" in r.citation_text)
        
        if underscore_count > 0 and asterisk_count > 0:
            issues.append("Inconsistent italics formatting (mix of _ and *)")
        
        return issues
    
    def _format_citation_result(self, result: CitationResult) -> Dict[str, Any]:
        """Format a single citation result for output."""
        return {
            "citation": result.citation_text[:100] + "..." if len(result.citation_text) > 100 else result.citation_text,
            "detected_style": result.style.value,
            "format_score": round(result.format_compliance, 2),
            "completeness_score": round(result.completeness_score, 2),
            "accuracy_score": round(result.accuracy_score, 2),
            "main_issues": result.issues_found[:3],  # Top 3 issues
            "has_corrections": len(result.corrections) > 0
        }
    
    def _generate_recommendations(self, results: List[CitationResult], dominant_style: CitationStyle, consistency_score: float) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Style consistency
        if consistency_score < 0.8:
            recommendations.append(
                f"Standardize all citations to {dominant_style.value} format for consistency"
            )
        
        # Common issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues_found)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Top issues
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for issue, count in top_issues:
            if count > len(results) * 0.2:  # Affects >20% of citations
                recommendations.append(f"Fix widespread issue: {issue} (affects {count} citations)")
        
        # Completeness
        avg_completeness = sum(r.completeness_score for r in results) / len(results) if results else 0
        if avg_completeness < 0.8:
            recommendations.append(
                "Add missing citation elements (year, volume, pages) to improve completeness"
            )
        
        # Format compliance
        avg_format = sum(r.format_compliance for r in results) / len(results) if results else 0
        if avg_format < 0.8:
            recommendations.append(
                f"Review {dominant_style.value} style guide for proper formatting rules"
            )
        
        # Specific style recommendations
        if dominant_style == CitationStyle.APA:
            if any("doi" not in r.citation_text.lower() and "http" in r.citation_text for r in results):
                recommendations.append(
                    "Add DOIs to journal articles when available (preferred over URLs in APA)"
                )
        elif dominant_style == CitationStyle.MLA:
            if any("accessed" not in r.citation_text.lower() and "http" in r.citation_text for r in results):
                recommendations.append(
                    "Add access dates to all web sources in MLA format"
                )
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _create_empty_citations_result(self) -> ValidationResult:
        """Create result when no citations are present."""
        return ValidationResult(
            validator_name=self.name,
            test_name="Citation Format Validation",
            status=ValidationStatus.WARNING,
            score=0.0,
            error_message="No citations found in research data",
            recommendations=[
                "Add properly formatted citations to support your research",
                "Include a mix of recent and seminal sources",
                "Follow a consistent citation style throughout"
            ]
        )
    
    def _create_error_result(self, error_message: str) -> ValidationResult:
        """Create error result."""
        return ValidationResult(
            validator_name=self.name,
            test_name="Citation Format Validation",
            status=ValidationStatus.ERROR,
            score=0.0,
            error_message=f"Citation validation error: {error_message}",
            recommendations=[
                "Fix validation errors and retry",
                "Ensure citations are properly formatted text",
                "Contact support if issue persists"
            ]
        )