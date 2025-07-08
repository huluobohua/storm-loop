"""
Harvard citation format validation strategy.

This module implements the Strategy pattern for Harvard citation format validation 
with comprehensive rule checking for author-date referencing system.
"""

import re
from typing import Dict, List, Set
from .base import CitationFormatStrategy, ValidationResult, ValidationError, ValidationSeverity
from ..models import CitationStyle


class HarvardStrategy(CitationFormatStrategy):
    """
    Harvard citation format validation strategy.
    
    Implements validation rules for Harvard author-date referencing system,
    commonly used in humanities and social sciences.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize Harvard citation strategy.
        
        Args:
            strict_mode: Whether to apply strict Harvard validation rules
        """
        super().__init__(strict_mode)
        self._setup_patterns()
    
    @property
    def format_name(self) -> str:
        """Return the name of the citation format."""
        return "Harvard"
    
    @property
    def citation_style(self) -> CitationStyle:
        """Return the CitationStyle enum value."""
        return CitationStyle.HARVARD
    
    @property
    def required_fields(self) -> Set[str]:
        """Return the set of required fields for Harvard citations."""
        return {
            'author',
            'year',
            'title'
        }
    
    @property
    def optional_fields(self) -> Set[str]:
        """Return the set of optional fields for Harvard citations."""
        return {
            'editor',
            'edition',
            'place',
            'publisher',
            'journal',
            'volume',
            'issue',
            'pages',
            'url',
            'accessed_date',
            'doi'
        }
    
    def _setup_patterns(self):
        """Set up regex patterns for Harvard validation."""
        # Author patterns (Harvard uses full names or initials)
        self.author_patterns = {
            'single_author_full': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
            'single_author_initial': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z]\.(?:\s*[A-Z]\.)*$',
            'multiple_authors': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z]\.?(?:\s*[A-Z]\.?)*(?:\s+[A-Za-z]+)*(?:,\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z]\.?(?:\s*[A-Z]\.?)*(?:\s+[A-Za-z]+)*)*(?:\s*and\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z]\.?(?:\s*[A-Z]\.?)*(?:\s+[A-Za-z]+)*)?$',
            'et_al': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z]\.?(?:\s*[A-Z]\.?)*(?:\s+[A-Za-z]+)*\s+et\s+al\.$'
        }
        
        # Year pattern
        self.year_pattern = r'\b(\d{4}[a-z]?)\b'
        
        # Title patterns (Harvard uses sentence case for articles, title case for books)
        self.title_patterns = {
            'sentence_case': r'^[A-Z][^A-Z]*(?:\s[a-z][^A-Z]*)*[.!?]?$',
            'title_case': r'^[A-Z][A-Za-z\s]*(?:[A-Z][A-Za-z\s]*)*$',
            'with_subtitle': r'^[A-Z][^:]*:\s*[A-Z][^:]*$'
        }
        
        # Journal patterns
        self.journal_pattern = r'^[A-Z][A-Za-z\s&:,-]+[A-Za-z]$'
        
        # Volume and issue patterns
        self.volume_pattern = r'^\d+$'
        self.issue_pattern = r'^\d+$'
        
        # Pages patterns
        self.pages_patterns = {
            'range': r'^\d+[-–]\d+$',
            'single': r'^\d+$',
            'with_pp': r'^pp\.\s*\d+[-–]?\d*$'
        }
        
        # Place pattern
        self.place_pattern = r'^[A-Z][A-Za-z\s,]+$'
        
        # Publisher pattern
        self.publisher_pattern = r'^[A-Z][A-Za-z\s&.,()-]+$'
        
        # URL pattern
        self.url_pattern = r'^(?:Available at:\s*)?https?:\/\/[^\s]+$'
        
        # DOI pattern
        self.doi_pattern = r'^doi:\s*10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'
        
        # Access date pattern
        self.access_date_pattern = r'^\[Accessed\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}\]$'
    
    def validate_single_citation(self, citation: str) -> ValidationResult:
        """
        Validate a single Harvard citation string.
        
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
        errors.extend(self._validate_year(components.get('year', '')))
        errors.extend(self._validate_title(components.get('title', '')))
        
        # Validate optional fields if present
        if 'journal' in components:
            errors.extend(self._validate_journal(components['journal']))
        
        if 'volume' in components:
            errors.extend(self._validate_volume(components['volume']))
        
        if 'issue' in components:
            errors.extend(self._validate_issue(components['issue']))
        
        if 'pages' in components:
            errors.extend(self._validate_pages(components['pages']))
        
        if 'place' in components:
            errors.extend(self._validate_place(components['place']))
        
        if 'publisher' in components:
            errors.extend(self._validate_publisher(components['publisher']))
        
        if 'url' in components:
            errors.extend(self._validate_url(components['url']))
        
        if 'doi' in components:
            errors.extend(self._validate_doi(components['doi']))
        
        if 'accessed_date' in components:
            errors.extend(self._validate_access_date(components['accessed_date']))
        
        # Validate overall structure
        structure_errors = self._validate_structure(citation)
        errors.extend(structure_errors)
        
        # Generate warnings for style issues
        style_warnings = self._check_style_issues(citation, components)
        warnings.extend(style_warnings)
        
        # Calculate confidence
        confidence = self._calculate_harvard_confidence(citation, components, errors)
        
        is_valid = len([e for e in errors if e.severity == ValidationSeverity.CRITICAL]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata={
                'format': 'Harvard',
                'components_found': list(components.keys()),
                'citation_length': len(citation)
            }
        )
    
    def _extract_components(self, citation: str) -> Dict[str, str]:
        """
        Extract citation components from Harvard citation string.
        
        Args:
            citation: The citation string to parse
            
        Returns:
            Dictionary mapping component names to extracted values
        """
        components = super()._extract_components(citation)
        
        # Harvard format: Author, A. (Year) 'Title,' Journal, Volume(Issue), pp. Pages.
        # or: Author, A. (Year) Title, Place: Publisher.
        
        # Extract year in parentheses
        year_match = re.search(r'\((\d{4}[a-z]?)\)', citation)
        if year_match:
            year_pos = year_match.start()
            author_part = citation[:year_pos].strip()
            if author_part.endswith(','):
                author_part = author_part[:-1].strip()
            components['author'] = author_part
            components['year'] = year_match.group(1)
            
            # Extract everything after the year
            rest = citation[year_match.end():].strip()
            
            # Look for title (could be in quotes or italics indicators)
            # Try to find the main title before comma or period
            title_patterns = [
                r"^'([^']+)'",  # Single quotes
                r'^"([^"]+)"',  # Double quotes
                r'^([^,]+),',   # Until comma
                r'^([^.]+)\.',  # Until period
            ]
            
            title_found = False
            for pattern in title_patterns:
                title_match = re.search(pattern, rest)
                if title_match:
                    components['title'] = title_match.group(1).strip()
                    rest = rest[title_match.end():].strip()
                    title_found = True
                    break
            
            if not title_found and rest:
                # Fallback: take everything up to first comma or period
                end_pos = min(
                    [pos for pos in [rest.find(','), rest.find('.')] if pos > 0] or [len(rest)]
                )
                components['title'] = rest[:end_pos].strip()
                rest = rest[end_pos:].strip()
            
            # Parse remaining components
            if rest.startswith(','):
                rest = rest[1:].strip()
            
            # Split by commas and analyze each part
            parts = [part.strip() for part in rest.split(',') if part.strip()]
            
            for part in parts:
                # Check if it's a journal (italicized text or journal-like pattern)
                if re.match(self.journal_pattern, part) and 'journal' not in components:
                    components['journal'] = part
                # Check for volume(issue) pattern
                elif re.match(r'^\d+\(\d+\)', part):
                    vol_issue_match = re.match(r'^(\d+)\((\d+)\)', part)
                    if vol_issue_match:
                        components['volume'] = vol_issue_match.group(1)
                        components['issue'] = vol_issue_match.group(2)
                # Check for pages
                elif re.match(r'^pp?\.\s*\d+[-–]?\d*', part):
                    components['pages'] = part
                # Check for place: publisher pattern
                elif ':' in part:
                    place_pub = part.split(':', 1)
                    if len(place_pub) == 2:
                        components['place'] = place_pub[0].strip()
                        components['publisher'] = place_pub[1].strip()
                # Check for URL
                elif part.startswith('http') or part.startswith('Available at:'):
                    components['url'] = part
                # Check for DOI
                elif part.startswith('doi:'):
                    components['doi'] = part
                # Check for access date
                elif part.startswith('[Accessed'):
                    components['accessed_date'] = part
        
        return components
    
    def _validate_author(self, author: str) -> List[ValidationError]:
        """Validate author format according to Harvard guidelines."""
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
                message=f"Author format does not match Harvard style: {author}",
                severity=ValidationSeverity.MAJOR,
                field='author',
                suggestion="Use format: Last, F.M. or Last, First and Last, F.M."
            ))
        
        # Check for '&' instead of 'and'
        if '&' in author:
            errors.append(ValidationError(
                message="Harvard uses 'and' instead of '&' between authors",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        return errors
    
    def _validate_year(self, year: str) -> List[ValidationError]:
        """Validate year format according to Harvard guidelines."""
        errors = []
        
        if not year:
            return errors  # Handled by required field validation
        
        # Check year format
        if not re.match(r'^\d{4}[a-z]?$', year):
            errors.append(ValidationError(
                message=f"Year format should be YYYY or YYYYa: {year}",
                severity=ValidationSeverity.MAJOR,
                field='year'
            ))
        
        # Check reasonable year range
        year_num = int(re.sub(r'[a-z]', '', year))
        if year_num < 1800 or year_num > 2030:
            errors.append(ValidationError(
                message=f"Year seems unreasonable: {year}",
                severity=ValidationSeverity.MINOR,
                field='year'
            ))
        
        return errors
    
    def _validate_title(self, title: str) -> List[ValidationError]:
        """Validate title format according to Harvard guidelines."""
        errors = []
        
        if not title:
            return errors  # Handled by required field validation
        
        # Harvard can use either sentence case or title case depending on source type
        # Check for basic capitalization
        if not re.match(r'^[A-Z]', title):
            errors.append(ValidationError(
                message="Title should start with capital letter",
                severity=ValidationSeverity.MINOR,
                field='title'
            ))
        
        return errors
    
    def _validate_journal(self, journal: str) -> List[ValidationError]:
        """Validate journal format according to Harvard guidelines."""
        errors = []
        
        if not journal:
            return errors
        
        # Check basic journal format
        if not re.match(self.journal_pattern, journal):
            errors.append(ValidationError(
                message=f"Journal name format may be incorrect: {journal}",
                severity=ValidationSeverity.MINOR,
                field='journal'
            ))
        
        return errors
    
    def _validate_volume(self, volume: str) -> List[ValidationError]:
        """Validate volume format according to Harvard guidelines."""
        errors = []
        
        if not volume:
            return errors
        
        if not re.match(self.volume_pattern, volume):
            errors.append(ValidationError(
                message=f"Volume should be a number: {volume}",
                severity=ValidationSeverity.MINOR,
                field='volume'
            ))
        
        return errors
    
    def _validate_issue(self, issue: str) -> List[ValidationError]:
        """Validate issue format according to Harvard guidelines."""
        errors = []
        
        if not issue:
            return errors
        
        if not re.match(self.issue_pattern, issue):
            errors.append(ValidationError(
                message=f"Issue should be a number: {issue}",
                severity=ValidationSeverity.MINOR,
                field='issue'
            ))
        
        return errors
    
    def _validate_pages(self, pages: str) -> List[ValidationError]:
        """Validate pages format according to Harvard guidelines."""
        errors = []
        
        if not pages:
            return errors
        
        # Check if pages match any valid pattern
        valid_format = False
        for pattern_name, pattern in self.pages_patterns.items():
            if re.match(pattern, pages):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Pages format should be 'pp. #-#' or '#-#': {pages}",
                severity=ValidationSeverity.MINOR,
                field='pages'
            ))
        
        return errors
    
    def _validate_place(self, place: str) -> List[ValidationError]:
        """Validate publication place according to Harvard guidelines."""
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
        """Validate publisher format according to Harvard guidelines."""
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
    
    def _validate_url(self, url: str) -> List[ValidationError]:
        """Validate URL format according to Harvard guidelines."""
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
        """Validate DOI format according to Harvard guidelines."""
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
    
    def _validate_access_date(self, access_date: str) -> List[ValidationError]:
        """Validate access date format according to Harvard guidelines."""
        errors = []
        
        if not access_date:
            return errors
        
        if not re.match(self.access_date_pattern, access_date):
            errors.append(ValidationError(
                message=f"Access date should be '[Accessed DD Month YYYY]': {access_date}",
                severity=ValidationSeverity.MINOR,
                field='accessed_date'
            ))
        
        return errors
    
    def _validate_structure(self, citation: str) -> List[ValidationError]:
        """Validate overall citation structure."""
        errors = []
        
        # Check for year in parentheses
        if not re.search(r'\(\d{4}[a-z]?\)', citation):
            errors.append(ValidationError(
                message="Year should be in parentheses: (YYYY)",
                severity=ValidationSeverity.CRITICAL,
                field='structure'
            ))
        
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
        
        return errors
    
    def _check_style_issues(self, citation: str, components: Dict[str, str]) -> List[ValidationError]:
        """Check for common Harvard style issues."""
        warnings = []
        
        # Check for italicization indicators for journal/book titles
        if 'journal' in components and components['journal']:
            if not any(indicator in citation for indicator in ['*', '_', '<em>', '<i>']):
                warnings.append(ValidationError(
                    message="Journal names should be italicized",
                    severity=ValidationSeverity.WARNING,
                    field='journal'
                ))
        
        # Check for access date with online sources
        if 'url' in components and 'accessed_date' not in components:
            warnings.append(ValidationError(
                message="Online sources should include access date",
                severity=ValidationSeverity.WARNING,
                field='accessed_date'
            ))
        
        # Check for proper volume/issue format
        if 'volume' in components and 'issue' in components:
            vol_issue_pattern = f"{components['volume']}({components['issue']})"
            if vol_issue_pattern not in citation:
                warnings.append(ValidationError(
                    message="Volume and issue should be formatted as 'Volume(Issue)'",
                    severity=ValidationSeverity.WARNING,
                    field='volume'
                ))
        
        return warnings
    
    def _calculate_harvard_confidence(self, citation: str, components: Dict[str, str], errors: List[ValidationError]) -> float:
        """Calculate confidence score specific to Harvard format."""
        base_confidence = self._calculate_base_confidence(citation, errors)
        
        # Bonus points for having Harvard-specific elements
        harvard_bonus = 0.0
        
        # Year in parentheses
        if re.search(r'\(\d{4}[a-z]?\)', citation):
            harvard_bonus += 0.1
        
        # Proper author format
        if 'author' in components:
            for pattern in self.author_patterns.values():
                if re.match(pattern, components['author']):
                    harvard_bonus += 0.1
                    break
        
        # Journal or publication information
        if 'journal' in components:
            harvard_bonus += 0.1
        
        # Publisher information
        if 'place' in components and 'publisher' in components:
            harvard_bonus += 0.1
        
        # Volume and issue
        if 'volume' in components and 'issue' in components:
            harvard_bonus += 0.05
        
        # Page information
        if 'pages' in components:
            harvard_bonus += 0.05
        
        return min(1.0, base_confidence + harvard_bonus)