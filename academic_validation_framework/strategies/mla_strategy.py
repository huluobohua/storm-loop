"""
MLA citation format validation strategy.

This module implements the Strategy pattern for MLA (Modern Language Association) 
citation format validation with comprehensive rule checking.
"""

import re
from typing import Dict, List, Set
from .base import CitationFormatStrategy, ValidationResult, ValidationError, ValidationSeverity
from ..models import CitationStyle


class MLAStrategy(CitationFormatStrategy):
    """
    MLA citation format validation strategy.
    
    Implements validation rules for MLA 8th edition citation format.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize MLA citation strategy.
        
        Args:
            strict_mode: Whether to apply strict MLA validation rules
        """
        super().__init__(strict_mode)
        self._setup_patterns()
    
    @property
    def format_name(self) -> str:
        """Return the name of the citation format."""
        return "MLA"
    
    @property
    def citation_style(self) -> CitationStyle:
        """Return the CitationStyle enum value."""
        return CitationStyle.MLA
    
    @property
    def required_fields(self) -> Set[str]:
        """Return the set of required fields for MLA citations."""
        return {
            'author',
            'title',
            'container'  # Could be journal, website, book, etc.
        }
    
    @property
    def optional_fields(self) -> Set[str]:
        """Return the set of optional fields for MLA citations."""
        return {
            'other_contributors',
            'version',
            'number',
            'publisher',
            'publication_date',
            'location',
            'date_of_access',
            'url'
        }
    
    def _setup_patterns(self):
        """Set up regex patterns for MLA validation."""
        # Author patterns (MLA uses full names, not initials)
        self.author_patterns = {
            'single_author': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',
            'multiple_authors': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*and\s*[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)*$',
            'et_al': r'^[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*et\s*al\.$'
        }
        
        # Title patterns (MLA uses title case)
        self.title_patterns = {
            'title_case': r'^[A-Z][A-Za-z\s]*(?:[A-Z][A-Za-z\s]*)*$',
            'with_subtitle': r'^[A-Z][A-Za-z\s]*:\s*[A-Z][A-Za-z\s]*$'
        }
        
        # Container patterns (journals, websites, etc.)
        self.container_pattern = r'^[A-Z][A-Za-z\s&:,-]+[A-Za-z]$'
        
        # Date patterns
        self.date_patterns = {
            'full_date': r'^\d{1,2}\s+[A-Za-z]+\s+\d{4}$',  # 15 May 2020
            'month_year': r'^[A-Za-z]+\s+\d{4}$',  # May 2020
            'year_only': r'^\d{4}$'  # 2020
        }
        
        # Page patterns
        self.page_patterns = {
            'range': r'^pp\.\s*\d+[-–]\d+$',
            'single': r'^p\.\s*\d+$',
            'no_prefix': r'^\d+[-–]\d+$'
        }
        
        # URL pattern
        self.url_pattern = r'^https?:\/\/[^\s]+$'
    
    def validate_single_citation(self, citation: str) -> ValidationResult:
        """
        Validate a single MLA citation string.
        
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
        errors.extend(self._validate_container(components.get('container', '')))
        
        # Validate optional fields if present
        if 'publication_date' in components:
            errors.extend(self._validate_date(components['publication_date']))
        
        if 'location' in components:
            errors.extend(self._validate_pages(components['location']))
        
        if 'url' in components:
            errors.extend(self._validate_url(components['url']))
        
        # Validate overall structure
        structure_errors = self._validate_structure(citation)
        errors.extend(structure_errors)
        
        # Generate warnings for style issues
        style_warnings = self._check_style_issues(citation, components)
        warnings.extend(style_warnings)
        
        # Calculate confidence
        confidence = self._calculate_mla_confidence(citation, components, errors)
        
        is_valid = len([e for e in errors if e.severity == ValidationSeverity.CRITICAL]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata={
                'format': 'MLA',
                'components_found': list(components.keys()),
                'citation_length': len(citation)
            }
        )
    
    def _extract_components(self, citation: str) -> Dict[str, str]:
        """
        Extract citation components from MLA citation string.
        
        Args:
            citation: The citation string to parse
            
        Returns:
            Dictionary mapping component names to extracted values
        """
        components = super()._extract_components(citation)
        
        # MLA format: Author. "Title." Container, Publication Date, Location.
        # Split by periods and quotes to identify components
        parts = []
        current_part = ""
        in_quotes = False
        
        for char in citation:
            if char == '"' and not in_quotes:
                in_quotes = True
                current_part += char
            elif char == '"' and in_quotes:
                in_quotes = False
                current_part += char
            elif char == '.' and not in_quotes:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Try to identify components
        if parts:
            # First part is typically the author
            if not parts[0].startswith('"'):
                components['author'] = parts[0].strip()
                parts = parts[1:]
        
        # Look for quoted title
        for i, part in enumerate(parts):
            if part.startswith('"') and part.endswith('"'):
                components['title'] = part[1:-1]  # Remove quotes
                parts = parts[:i] + parts[i+1:]
                break
        
        # Remaining parts contain container, date, location
        remaining = ' '.join(parts)
        
        # Extract container (typically italicized, but we'll look for comma-separated elements)
        container_match = re.search(r'^([^,]+)', remaining)
        if container_match:
            potential_container = container_match.group(1).strip()
            if len(potential_container) > 3:
                components['container'] = potential_container
        
        # Extract date
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{4})', remaining)
        if date_match:
            components['publication_date'] = date_match.group(1)
        
        # Extract page information
        page_match = re.search(r'(pp?\.\s*\d+[-–]?\d*)', remaining)
        if page_match:
            components['location'] = page_match.group(1)
        
        # Extract URL
        url_match = re.search(r'(https?:\/\/[^\s,]+)', remaining)
        if url_match:
            components['url'] = url_match.group(1)
        
        return components
    
    def _validate_author(self, author: str) -> List[ValidationError]:
        """Validate author format according to MLA guidelines."""
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
                message=f"Author format does not match MLA style: {author}",
                severity=ValidationSeverity.MAJOR,
                field='author',
                suggestion="Use format: Last, First Middle, and Last, First Middle"
            ))
        
        # Check for proper name format (MLA uses full first names)
        if re.search(r'\b[A-Z]\.\s*[A-Z]\.', author):
            errors.append(ValidationError(
                message="MLA uses full first names, not initials",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        # Check for 'and' instead of '&'
        if '&' in author:
            errors.append(ValidationError(
                message="MLA uses 'and' instead of '&' between authors",
                severity=ValidationSeverity.MINOR,
                field='author'
            ))
        
        return errors
    
    def _validate_title(self, title: str) -> List[ValidationError]:
        """Validate title format according to MLA guidelines."""
        errors = []
        
        if not title:
            return errors  # Handled by required field validation
        
        # Check for title case (MLA requirement)
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
    
    def _validate_container(self, container: str) -> List[ValidationError]:
        """Validate container format according to MLA guidelines."""
        errors = []
        
        if not container:
            return errors  # Handled by required field validation
        
        # Check basic container format
        if not re.match(self.container_pattern, container):
            errors.append(ValidationError(
                message=f"Container format may be incorrect: {container}",
                severity=ValidationSeverity.MINOR,
                field='container'
            ))
        
        return errors
    
    def _validate_date(self, date: str) -> List[ValidationError]:
        """Validate date format according to MLA guidelines."""
        errors = []
        
        if not date:
            return errors
        
        # Check if date matches any valid pattern
        valid_format = False
        for pattern_name, pattern in self.date_patterns.items():
            if re.match(pattern, date):
                valid_format = True
                break
        
        if not valid_format:
            errors.append(ValidationError(
                message=f"Date format should be 'Day Month Year' or 'Month Year' or 'Year': {date}",
                severity=ValidationSeverity.MINOR,
                field='publication_date'
            ))
        
        return errors
    
    def _validate_pages(self, pages: str) -> List[ValidationError]:
        """Validate page format according to MLA guidelines."""
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
                message=f"Page format should be 'pp. #-#' or 'p. #': {pages}",
                severity=ValidationSeverity.MINOR,
                field='location'
            ))
        
        return errors
    
    def _validate_url(self, url: str) -> List[ValidationError]:
        """Validate URL format according to MLA guidelines."""
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
                message="Article/chapter title should be in quotation marks",
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
        """Check for common MLA style issues."""
        warnings = []
        
        # Check for italicization indicators for container
        if 'container' in components and components['container']:
            if not any(indicator in citation for indicator in ['*', '_', '<em>', '<i>']):
                warnings.append(ValidationError(
                    message="Container (journal, website, etc.) should be italicized",
                    severity=ValidationSeverity.WARNING,
                    field='container'
                ))
        
        # Check for date access for web sources
        if 'url' in components and 'date_of_access' not in components:
            warnings.append(ValidationError(
                message="Web sources should include date of access",
                severity=ValidationSeverity.WARNING,
                field='date_of_access'
            ))
        
        return warnings
    
    def _calculate_mla_confidence(self, citation: str, components: Dict[str, str], errors: List[ValidationError]) -> float:
        """Calculate confidence score specific to MLA format."""
        base_confidence = self._calculate_base_confidence(citation, errors)
        
        # Bonus points for having MLA-specific elements
        mla_bonus = 0.0
        
        # Title in quotes
        if '"' in citation:
            mla_bonus += 0.1
        
        # Proper author format (full names)
        if 'author' in components and not re.search(r'\b[A-Z]\.\s*[A-Z]\.', components['author']):
            mla_bonus += 0.1
        
        # Container information
        if 'container' in components:
            mla_bonus += 0.1
        
        # Date information
        if 'publication_date' in components:
            mla_bonus += 0.05
        
        # Location (page) information
        if 'location' in components:
            mla_bonus += 0.05
        
        return min(1.0, base_confidence + mla_bonus)