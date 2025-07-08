"""
Chicago citation format validation strategy.

This module implements the Strategy pattern for Chicago Manual of Style 
citation format validation with comprehensive rule checking.
"""

import re
from typing import Dict, List, Set
from .base import CitationFormatStrategy, ValidationResult, ValidationError, ValidationSeverity
from ..models import CitationStyle


class ChicagoStrategy(CitationFormatStrategy):
    """
    Chicago citation format validation strategy.
    
    Implements validation rules for Chicago Manual of Style 17th edition.
    Supports both notes-bibliography and author-date styles.
    """
    
    def __init__(self, strict_mode: bool = True, style_variant: str = "notes"):
        """
        Initialize Chicago citation strategy.
        
        Args:
            strict_mode: Whether to apply strict Chicago validation rules
            style_variant: Either "notes" (notes-bibliography) or "author-date"
        """
        super().__init__(strict_mode)
        self.style_variant = style_variant.lower()
        if self.style_variant not in ["notes", "author-date"]:
            raise ValueError("style_variant must be 'notes' or 'author-date'")
        self._setup_patterns()
    
    @property
    def format_name(self) -> str:
        """Return the name of the citation format."""
        return f"Chicago ({self.style_variant})"
    
    @property
    def citation_style(self) -> CitationStyle:
        """Return the CitationStyle enum value."""
        return CitationStyle.CHICAGO
    
    @property
    def required_fields(self) -> Set[str]:
        """Return the set of required fields for Chicago citations."""
        if self.style_variant == "author-date":
            return {
                'author',
                'year',
                'title'
            }
        else:  # notes-bibliography
            return {
                'author',
                'title',
                'publication_info'
            }
    
    @property
    def optional_fields(self) -> Set[str]:
        """Return the set of optional fields for Chicago citations."""
        return {
            'editor',
            'translator',
            'edition',
            'volume',
            'publisher',
            'place',
            'year',
            'pages',
            'url',
            'doi',
            'access_date'
        }
    
    def _setup_patterns(self):
        """Set up regex patterns for Chicago validation."""
        # Author patterns (Chicago uses full names)
        self.author_patterns = {
            'single_author': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
            'multiple_authors': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*and\s+[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*$',
            'last_first': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'
        }
        
        # Year pattern
        self.year_pattern = r'\b(\d{4})\b'
        
        # Title patterns (Chicago uses title case)
        self.title_patterns = {
            'title_case': r'^[A-Z][A-Za-z\s]*(?:[A-Z][A-Za-z\s]*)*$',
            'with_subtitle': r'^[A-Z][A-Za-z\s]*:\s*[A-Z][A-Za-z\s]*$'
        }
        
        # Publication place pattern
        self.place_pattern = r'^[A-Z][A-Za-z\s,]+$'
        
        # Publisher pattern
        self.publisher_pattern = r'^[A-Z][A-Za-z\s&.,()-]+$'
        
        # Page patterns
        self.page_patterns = {
            'range': r'^\d+[-–]\d+$',
            'single': r'^\d+$',
            'with_prefix': r'^pp?\.\s*\d+[-–]?\d*$'
        }
        
        # URL pattern
        self.url_pattern = r'^https?:\/\/[^\s]+$'
        
        # DOI pattern
        self.doi_pattern = r'^10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'
    
    def validate_single_citation(self, citation: str) -> ValidationResult:
        """
        Validate a single Chicago citation string.
        
        Args:
            citation: The citation string to validate
            
        Returns:
            ValidationResult containing validation status and details
        """
        if not citation or not citation.strip():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[ValidationError(
                    message="Empty citation provided",
                    severity=ValidationSeverity.CRITICAL
                )],
                warnings=[]
            )
        
        citation = citation.strip()
        errors = []
        warnings = []
        
        # Extract components
        components = self._extract_components(citation)
        
        # Validate required fields
        errors.extend(self._validate_required_fields(components))
        
        # Validate individual components
        errors.extend(self._validate_author(components.get('author', '')))
        errors.extend(self._validate_title(components.get('title', '')))
        
        if self.style_variant == "author-date":
            errors.extend(self._validate_year(components.get('year', '')))
        
        # Validate optional fields if present
        if 'place' in components:
            errors.extend(self._validate_place(components['place']))
        
        if 'publisher' in components:
            errors.extend(self._validate_publisher(components['publisher']))
        
        if 'year' in components:
            errors.extend(self._validate_year(components['year']))
        
        if 'pages' in components:
            errors.extend(self._validate_pages(components['pages']))
        
        if 'url' in components:
            errors.extend(self._validate_url(components['url']))
        
        if 'doi' in components:
            errors.extend(self._validate_doi(components['doi']))
        
        # Validate overall structure
        structure_errors = self._validate_structure(citation)
        errors.extend(structure_errors)
        
        # Generate warnings for style issues
        style_warnings = self._check_style_issues(citation, components)
        warnings.extend(style_warnings)
        
        # Calculate confidence
        confidence = self._calculate_chicago_confidence(citation, components, errors)
        
        is_valid = len([e for e in errors if e.severity == ValidationSeverity.CRITICAL]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata={
                'format': f'Chicago ({self.style_variant})',
                'components_found': list(components.keys()),
                'citation_length': len(citation)
            }
        )
    
    def _extract_components(self, citation: str) -> Dict[str, str]:
        """
        Extract citation components from Chicago citation string.
        
        Args:
            citation: The citation string to parse
            
        Returns:
            Dictionary mapping component names to extracted values
        """
        components = super()._extract_components(citation)
        
        if self.style_variant == "author-date":
            # Author-date format: Author, Year. "Title." Place: Publisher.
            return self._extract_author_date_components(citation, components)
        else:
            # Notes-bibliography format: Author, Title (Place: Publisher, Year).
            return self._extract_notes_components(citation, components)
    
    def _extract_author_date_components(self, citation: str, components: Dict[str, str]) -> Dict[str, str]:
        """Extract components for Chicago author-date style."""
        # Look for year early in citation (after author)
        year_match = re.search(r'(\d{4})', citation)
        if year_match:
            year_pos = year_match.start()
            author_part = citation[:year_pos].strip()
            if author_part.endswith(','):
                author_part = author_part[:-1].strip()
            components['author'] = author_part
            components['year'] = year_match.group(1)
            
            # Extract title (usually in quotes after year)
            rest = citation[year_match.end():].strip()
            if rest.startswith('.'):
                rest = rest[1:].strip()
            
            # Look for quoted title
            title_match = re.search(r'"([^"]+)"', rest)
            if title_match:
                components['title'] = title_match.group(1)
                
                # Extract publication info after title
                pub_info = rest[title_match.end():].strip()
                if pub_info.startswith('.'):
                    pub_info = pub_info[1:].strip()
                
                # Look for place and publisher
                place_pub_match = re.search(r'^([^:]+):\s*([^,.]+)', pub_info)
                if place_pub_match:
                    components['place'] = place_pub_match.group(1).strip()
                    components['publisher'] = place_pub_match.group(2).strip()
        
        return components
    
    def _extract_notes_components(self, citation: str, components: Dict[str, str]) -> Dict[str, str]:
        """Extract components for Chicago notes-bibliography style."""
        # Look for author at the beginning
        comma_pos = citation.find(',')
        if comma_pos > 0:
            components['author'] = citation[:comma_pos].strip()
            rest = citation[comma_pos + 1:].strip()
            
            # Look for title (often italicized or in quotes)
            # Try to find parentheses for publication info
            paren_start = rest.find('(')
            if paren_start > 0:
                title_part = rest[:paren_start].strip()
                components['title'] = title_part
                
                # Extract publication info from parentheses
                paren_end = rest.find(')', paren_start)
                if paren_end > paren_start:
                    pub_info = rest[paren_start + 1:paren_end]
                    components['publication_info'] = pub_info
                    
                    # Try to extract place, publisher, and year from pub info
                    # Format: Place: Publisher, Year
                    colon_pos = pub_info.find(':')
                    if colon_pos > 0:
                        components['place'] = pub_info[:colon_pos].strip()
                        rest_pub = pub_info[colon_pos + 1:].strip()
                        
                        comma_pos = rest_pub.rfind(',')
                        if comma_pos > 0:
                            components['publisher'] = rest_pub[:comma_pos].strip()
                            year_part = rest_pub[comma_pos + 1:].strip()
                            year_match = re.search(r'\d{4}', year_part)
                            if year_match:
                                components['year'] = year_match.group()
        
        return components
    
    def _validate_author(self, author: str) -> List[ValidationError]:
        """Validate author format according to Chicago guidelines."""
        errors = []
        
        if not author:
            return errors  # Handled by required field validation
        
        # Check for basic author format
        valid_format = False
        for pattern_name, pattern in self.author_patterns.items():
            if re.match(pattern, author):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Author format does not match Chicago style: {author}",
                severity=ValidationSeverity.MAJOR,
                field='author',
                suggestion="Use format: First Last or Last, First"
            ))
        
        # Check for initials (Chicago prefers full names)
        if re.search(r'\b[A-Z]\.\s*[A-Z]\.', author):
            errors.append(ValidationError(
                message="Chicago style prefers full first names over initials",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        return errors
    
    def _validate_title(self, title: str) -> List[ValidationError]:
        """Validate title format according to Chicago guidelines."""
        errors = []
        
        if not title:
            return errors  # Handled by required field validation
        
        # Check for title case (Chicago requirement)
        words = title.split()
        if len(words) > 1:
            # Check if most significant words are capitalized
            significant_words = [w for w in words if len(w) > 3 or w.lower() not in ['a', 'an', 'the', 'and', 'or', 'but', 'for', 'nor', 'on', 'at', 'to', 'by', 'of', 'in']]
            if significant_words:
                capitalized_significant = sum(1 for w in significant_words if w[0].isupper())
                if capitalized_significant / len(significant_words) < 0.8:
                    errors.append(ValidationError(
                        message="Title should use title case",
                        severity=ValidationSeverity.MINOR,
                        field='title',
                        suggestion="Capitalize first word, last word, and all major words"
                    ))
        
        return errors
    
    def _validate_year(self, year: str) -> List[ValidationError]:
        """Validate year format according to Chicago guidelines."""
        errors = []
        
        if not year:
            return errors  # May be optional depending on style
        
        # Check year format
        if not re.match(r'^\d{4}$', year):
            errors.append(ValidationError(
                message=f"Year format should be YYYY: {year}",
                severity=ValidationSeverity.MAJOR,
                field='year'
            ))
        
        # Check reasonable year range
        try:
            year_num = int(year)
            if year_num < 1800 or year_num > 2030:
                errors.append(ValidationError(
                    message=f"Year seems unreasonable: {year}",
                    severity=ValidationSeverity.MINOR,
                    field='year'
                ))
        except ValueError:
            pass  # Already caught by format check
        
        return errors
    
    def _validate_place(self, place: str) -> List[ValidationError]:
        """Validate publication place according to Chicago guidelines."""
        errors = []
        
        if not place:
            return errors
        
        # Check basic place format
        if not re.match(self.place_pattern, place):
            errors.append(ValidationError(
                message=f"Publication place format may be incorrect: {place}",
                severity=ValidationSeverity.MINOR,
                field='place'
            ))
        
        return errors
    
    def _validate_publisher(self, publisher: str) -> List[ValidationError]:
        """Validate publisher format according to Chicago guidelines."""
        errors = []
        
        if not publisher:
            return errors
        
        # Check basic publisher format
        if not re.match(self.publisher_pattern, publisher):
            errors.append(ValidationError(
                message=f"Publisher format may be incorrect: {publisher}",
                severity=ValidationSeverity.MINOR,
                field='publisher'
            ))
        
        return errors
    
    def _validate_pages(self, pages: str) -> List[ValidationError]:
        """Validate page format according to Chicago guidelines."""
        errors = []
        
        if not pages:
            return errors
        
        # Check if pages match any valid pattern
        valid_format = False
        for pattern_name, pattern in self.page_patterns.items():
            if re.match(pattern, pages):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Page format should be 'pp-pp' or 'pp': {pages}",
                severity=ValidationSeverity.MINOR,
                field='pages'
            ))
        
        return errors
    
    def _validate_url(self, url: str) -> List[ValidationError]:
        """Validate URL format according to Chicago guidelines."""
        errors = []
        
        if not url:
            return errors
        
        if not re.match(self.url_pattern, url):
            errors.append(ValidationError(
                message=f"URL format is incorrect: {url}",
                severity=ValidationSeverity.MINOR,
                field='url'
            ))
        
        return errors
    
    def _validate_doi(self, doi: str) -> List[ValidationError]:
        """Validate DOI format according to Chicago guidelines."""
        errors = []
        
        if not doi:
            return errors
        
        if not re.match(self.doi_pattern, doi):
            errors.append(ValidationError(
                message=f"DOI format is incorrect: {doi}",
                severity=ValidationSeverity.MINOR,
                field='doi'
            ))
        
        return errors
    
    def _validate_structure(self, citation: str) -> List[ValidationError]:
        """Validate overall citation structure."""
        errors = []
        
        # Check for proper punctuation
        if not citation.endswith('.'):
            errors.append(ValidationError(
                message="Citation should end with a period",
                severity=ValidationSeverity.MINOR,
                field='structure'
            ))
        
        # Check for double spaces
        if '  ' in citation:
            errors.append(ValidationError(
                message="Citation contains double spaces",
                severity=ValidationSeverity.MINOR,
                field='structure'
            ))
        
        # Style-specific structure checks
        if self.style_variant == "author-date":
            # Should have year early in citation
            if not re.search(r'\d{4}', citation[:len(citation)//2]):
                errors.append(ValidationError(
                    message="Author-date style should have year near beginning",
                    severity=ValidationSeverity.MINOR,
                    field='structure'
                ))
        else:
            # Notes style should have parentheses for publication info
            if '(' not in citation or ')' not in citation:
                errors.append(ValidationError(
                    message="Notes style should have publication info in parentheses",
                    severity=ValidationSeverity.MINOR,
                    field='structure'
                ))
        
        return errors
    
    def _check_style_issues(self, citation: str, components: Dict[str, str]) -> List[ValidationError]:
        """Check for common Chicago style issues."""
        warnings = []
        
        # Check for italicization indicators for book titles
        if 'title' in components and components['title']:
            # Book titles should be italicized, article titles in quotes
            if not any(indicator in citation for indicator in ['*', '_', '<em>', '<i>', '"']):
                warnings.append(ValidationError(
                    message="Book titles should be italicized, article titles in quotes",
                    severity=ValidationSeverity.WARNING,
                    field='title'
                ))
        
        # Check for proper comma usage
        if self.style_variant == "author-date":
            if not re.search(r'[A-Za-z],\s*\d{4}', citation):
                warnings.append(ValidationError(
                    message="Author-date style should have comma before year",
                    severity=ValidationSeverity.WARNING,
                    field='structure'
                ))
        
        return warnings
    
    def _calculate_chicago_confidence(self, citation: str, components: Dict[str, str], errors: List[ValidationError]) -> float:
        """Calculate confidence score specific to Chicago format."""
        base_confidence = self._calculate_base_confidence(citation, errors)
        
        # Bonus points for having Chicago-specific elements
        chicago_bonus = 0.0
        
        # Proper author format
        if 'author' in components:
            for pattern in self.author_patterns.values():
                if re.match(pattern, components['author']):
                    chicago_bonus += 0.1
                    break
        
        # Title case title
        if 'title' in components:
            chicago_bonus += 0.05
        
        # Publication information
        if 'place' in components and 'publisher' in components:
            chicago_bonus += 0.1
        
        # Year information
        if 'year' in components:
            chicago_bonus += 0.05
        
        # Style-specific bonuses
        if self.style_variant == "author-date":
            # Year early in citation
            if re.search(r'\d{4}', citation[:len(citation)//2]):
                chicago_bonus += 0.05
        else:
            # Parentheses for publication info
            if '(' in citation and ')' in citation:
                chicago_bonus += 0.05
        
        return min(1.0, base_confidence + chicago_bonus)