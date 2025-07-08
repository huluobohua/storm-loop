"""
IEEE citation format validation strategy.

This module implements the Strategy pattern for IEEE citation format validation 
with comprehensive rule checking for technical publications.
"""

import re
from typing import Dict, List, Set
from .base import CitationFormatStrategy, ValidationResult, ValidationError, ValidationSeverity
from ..models import CitationStyle


class IEEEStrategy(CitationFormatStrategy):
    """
    IEEE citation format validation strategy.
    
    Implements validation rules for IEEE citation format commonly used
    in engineering and computer science publications.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize IEEE citation strategy.
        
        Args:
            strict_mode: Whether to apply strict IEEE validation rules
        """
        super().__init__(strict_mode)
        self._setup_patterns()
    
    @property
    def format_name(self) -> str:
        """Return the name of the citation format."""
        return "IEEE"
    
    @property
    def citation_style(self) -> CitationStyle:
        """Return the CitationStyle enum value."""
        return CitationStyle.IEEE
    
    @property
    def required_fields(self) -> Set[str]:
        """Return the set of required fields for IEEE citations."""
        return {
            'author',
            'title',
            'publication'  # Journal or conference
        }
    
    @property
    def optional_fields(self) -> Set[str]:
        """Return the set of optional fields for IEEE citations."""
        return {
            'volume',
            'issue',
            'pages',
            'year',
            'month',
            'publisher',
            'location',
            'doi',
            'url',
            'accessed_date'
        }
    
    def _setup_patterns(self):
        """Set up regex patterns for IEEE validation."""
        # Author patterns (IEEE uses initials)
        self.author_patterns = {
            'single_author': r'^[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*$',
            'multiple_authors': r'^[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*(?:,\s*[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)*(?:,?\s*and\s*[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)?$',
            'et_al': r'^[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*(?:,\s*[A-Z]\.\s*[A-Z]\.?\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)*,?\s*et\s*al\.$'
        }
        
        # Title patterns (IEEE uses quotes for article titles)
        self.title_patterns = {
            'quoted_title': r'^"[^"]+[.!?]?"$',
            'title_case': r'^[A-Z][A-Za-z\s]*(?:[A-Z][A-Za-z\s]*)*$'
        }
        
        # Publication patterns (journal or conference)
        self.publication_patterns = {
            'journal': r'^[A-Z][A-Za-z\s&.,-]+$',
            'conference': r'^(?:Proc\.|Proceedings)\s+[A-Za-z\s&.,-]+$',
            'abbreviated': r'^[A-Z]{2,}[A-Za-z\s&.,-]*$'  # For abbreviated journal names
        }
        
        # Volume and issue patterns
        self.volume_pattern = r'^vol\.\s*\d+$'
        self.issue_pattern = r'^no\.\s*\d+$'
        
        # Pages patterns
        self.pages_patterns = {
            'range': r'^pp\.\s*\d+[-–]\d+$',
            'single': r'^p\.\s*\d+$',
            'article_number': r'^Art\.\s*no\.\s*\d+$'
        }
        
        # Date patterns
        self.date_patterns = {
            'month_year': r'^[A-Z][a-z]{2,8}\s+\d{4}$',  # Jan. 2020
            'year_only': r'^\d{4}$'
        }
        
        # DOI pattern
        self.doi_pattern = r'^doi:\s*10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'
        
        # URL pattern
        self.url_pattern = r'^(?:Available:\s*)?https?:\/\/[^\s]+$'
    
    def validate_single_citation(self, citation: str) -> ValidationResult:
        """
        Validate a single IEEE citation string.
        
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
        errors.extend(self._validate_publication(components.get('publication', '')))
        
        # Validate optional fields if present
        if 'volume' in components:
            errors.extend(self._validate_volume(components['volume']))
        
        if 'issue' in components:
            errors.extend(self._validate_issue(components['issue']))
        
        if 'pages' in components:
            errors.extend(self._validate_pages(components['pages']))
        
        if 'year' in components:
            errors.extend(self._validate_year(components['year']))
        
        if 'doi' in components:
            errors.extend(self._validate_doi(components['doi']))
        
        if 'url' in components:
            errors.extend(self._validate_url(components['url']))
        
        # Validate overall structure
        structure_errors = self._validate_structure(citation)
        errors.extend(structure_errors)
        
        # Generate warnings for style issues
        style_warnings = self._check_style_issues(citation, components)
        warnings.extend(style_warnings)
        
        # Calculate confidence
        confidence = self._calculate_ieee_confidence(citation, components, errors)
        
        is_valid = len([e for e in errors if e.severity == ValidationSeverity.CRITICAL]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata={
                'format': 'IEEE',
                'components_found': list(components.keys()),
                'citation_length': len(citation)
            }
        )
    
    def _extract_components(self, citation: str) -> Dict[str, str]:
        """
        Extract citation components from IEEE citation string.
        
        Args:
            citation: The citation string to parse
            
        Returns:
            Dictionary mapping component names to extracted values
        """
        components = super()._extract_components(citation)
        
        # IEEE format: A. B. Author, "Title," Journal, vol. X, no. Y, pp. Z-Z, Month Year.
        
        # Find the first quoted string (title)
        title_match = re.search(r'"([^"]+)"', citation)
        if title_match:
            title_end = title_match.end()
            author_part = citation[:title_match.start()].strip()
            if author_part.endswith(','):
                author_part = author_part[:-1].strip()
            components['author'] = author_part
            components['title'] = title_match.group(1)
            
            # Extract remaining components after title
            rest = citation[title_end:].strip()
            if rest.startswith(','):
                rest = rest[1:].strip()
            
            # Split by commas to get publication info
            parts = [part.strip() for part in rest.split(',')]
            
            if parts:
                # First part is usually the publication (journal/conference)
                if parts[0] and not parts[0].startswith('vol.') and not parts[0].startswith('pp.'):
                    components['publication'] = parts[0]
                    parts = parts[1:]
                
                # Look for volume, issue, pages, date
                for part in parts:
                    if part.startswith('vol.'):
                        components['volume'] = part
                    elif part.startswith('no.'):
                        components['issue'] = part
                    elif part.startswith('pp.'):
                        components['pages'] = part
                    elif part.startswith('Art. no.'):
                        components['pages'] = part
                    elif re.match(r'^[A-Z][a-z]{2,8}\s+\d{4}$', part):
                        components['month_year'] = part
                        year_match = re.search(r'\d{4}', part)
                        if year_match:
                            components['year'] = year_match.group()
                    elif re.match(r'^\d{4}$', part):
                        components['year'] = part
                    elif part.startswith('doi:'):
                        components['doi'] = part
                    elif part.startswith('http') or part.startswith('Available:'):
                        components['url'] = part
        
        return components
    
    def _validate_author(self, author: str) -> List[ValidationError]:
        """Validate author format according to IEEE guidelines."""
        errors = []
        
        if not author:
            return errors  # Handled by required field validation
        
        # Check for basic IEEE author format (initials)
        valid_format = False
        for pattern_name, pattern in self.author_patterns.items():
            if re.match(pattern, author):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Author format does not match IEEE style: {author}",
                severity=ValidationSeverity.MAJOR,
                field='author',
                suggestion="Use format: A. B. Last, C. D. Last, and E. F. Last"
            ))
        
        # Check for full first names (IEEE prefers initials)
        if re.search(r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]+', author):
            errors.append(ValidationError(
                message="IEEE style uses initials for first names",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        # Check for proper comma and "and" usage
        if ' & ' in author:
            errors.append(ValidationError(
                message="IEEE uses 'and' instead of '&' between authors",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        return errors
    
    def _validate_title(self, title: str) -> List[ValidationError]:
        """Validate title format according to IEEE guidelines."""
        errors = []
        
        if not title:
            return errors  # Handled by required field validation
        
        # IEEE titles should be in quotes (handled in extraction)
        # Check for title case
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
    
    def _validate_publication(self, publication: str) -> List[ValidationError]:
        """Validate publication format according to IEEE guidelines."""
        errors = []
        
        if not publication:
            return errors  # Handled by required field validation
        
        # Check if publication matches any valid pattern
        valid_format = False
        for pattern_name, pattern in self.publication_patterns.items():
            if re.match(pattern, publication):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Publication format may be incorrect: {publication}",
                severity=ValidationSeverity.MINOR,
                field='publication',
                suggestion="Use full journal name or standard abbreviation"
            ))
        
        return errors
    
    def _validate_volume(self, volume: str) -> List[ValidationError]:
        """Validate volume format according to IEEE guidelines."""
        errors = []
        
        if not volume:
            return errors
        
        if not re.match(self.volume_pattern, volume, re.IGNORECASE):
            errors.append(ValidationError(
                message=f"Volume should be formatted as 'vol. X': {volume}",
                severity=ValidationSeverity.MINOR,
                field='volume'
            ))
        
        return errors
    
    def _validate_issue(self, issue: str) -> List[ValidationError]:
        """Validate issue format according to IEEE guidelines."""
        errors = []
        
        if not issue:
            return errors
        
        if not re.match(self.issue_pattern, issue, re.IGNORECASE):
            errors.append(ValidationError(
                message=f"Issue should be formatted as 'no. X': {issue}",
                severity=ValidationSeverity.MINOR,
                field='issue'
            ))
        
        return errors
    
    def _validate_pages(self, pages: str) -> List[ValidationError]:
        """Validate pages format according to IEEE guidelines."""
        errors = []
        
        if not pages:
            return errors
        
        # Check if pages match any valid pattern
        valid_format = False
        for pattern_name, pattern in self.pages_patterns.items():
            if re.match(pattern, pages, re.IGNORECASE):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Pages should be 'pp. X-Y' or 'Art. no. X': {pages}",
                severity=ValidationSeverity.MINOR,
                field='pages'
            ))
        
        return errors
    
    def _validate_year(self, year: str) -> List[ValidationError]:
        """Validate year format according to IEEE guidelines."""
        errors = []
        
        if not year:
            return errors
        
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
    
    def _validate_doi(self, doi: str) -> List[ValidationError]:
        """Validate DOI format according to IEEE guidelines."""
        errors = []
        
        if not doi:
            return errors
        
        if not re.match(self.doi_pattern, doi):
            errors.append(ValidationError(
                message=f"DOI should be formatted as 'doi: 10.xxxx/xxx': {doi}",
                severity=ValidationSeverity.MINOR,
                field='doi'
            ))
        
        return errors
    
    def _validate_url(self, url: str) -> List[ValidationError]:
        """Validate URL format according to IEEE guidelines."""
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
        
        # Check for title in quotes
        if '"' not in citation:
            errors.append(ValidationError(
                message="Article title should be in quotation marks",
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
        
        # Check for proper comma usage
        if citation.count(',') < 2:
            errors.append(ValidationError(
                message="IEEE citations typically have multiple comma-separated elements",
                severity=ValidationSeverity.MINOR,
                field='structure'
            ))
        
        return errors
    
    def _check_style_issues(self, citation: str, components: Dict[str, str]) -> List[ValidationError]:
        """Check for common IEEE style issues."""
        warnings = []
        
        # Check for italicization indicators for journal names
        if 'publication' in components and components['publication']:
            if not any(indicator in citation for indicator in ['*', '_', '<em>', '<i>']):
                warnings.append(ValidationError(
                    message="Journal names should be italicized",
                    severity=ValidationSeverity.WARNING,
                    field='publication'
                ))
        
        # Check for proper abbreviations
        if 'volume' in components and 'vol.' not in components['volume'].lower():
            warnings.append(ValidationError(
                message="Volume should be abbreviated as 'vol.'",
                severity=ValidationSeverity.WARNING,
                field='volume'
            ))
        
        if 'issue' in components and 'no.' not in components['issue'].lower():
            warnings.append(ValidationError(
                message="Issue should be abbreviated as 'no.'",
                severity=ValidationSeverity.WARNING,
                field='issue'
            ))
        
        if 'pages' in components and 'pp.' not in components['pages'].lower() and 'art.' not in components['pages'].lower():
            warnings.append(ValidationError(
                message="Pages should be abbreviated as 'pp.' or use 'Art. no.' for article numbers",
                severity=ValidationSeverity.WARNING,
                field='pages'
            ))
        
        return warnings
    
    def _calculate_ieee_confidence(self, citation: str, components: Dict[str, str], errors: List[ValidationError]) -> float:
        """Calculate confidence score specific to IEEE format."""
        base_confidence = self._calculate_base_confidence(citation, errors)
        
        # Bonus points for having IEEE-specific elements
        ieee_bonus = 0.0
        
        # Title in quotes
        if '"' in citation:
            ieee_bonus += 0.1
        
        # Proper author format (initials)
        if 'author' in components:
            for pattern in self.author_patterns.values():
                if re.match(pattern, components['author']):
                    ieee_bonus += 0.1
                    break
        
        # IEEE-style abbreviations
        if 'volume' in components and 'vol.' in components['volume'].lower():
            ieee_bonus += 0.05
        
        if 'issue' in components and 'no.' in components['issue'].lower():
            ieee_bonus += 0.05
        
        if 'pages' in components and ('pp.' in components['pages'].lower() or 'art.' in components['pages'].lower()):
            ieee_bonus += 0.05
        
        # Publication information
        if 'publication' in components:
            ieee_bonus += 0.1
        
        # Technical identifiers (DOI, etc.)
        if 'doi' in components:
            ieee_bonus += 0.05
        
        return min(1.0, base_confidence + ieee_bonus)