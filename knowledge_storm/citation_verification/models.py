"""
Citation Verification Models

Core data models for citation verification system.
Follows SOLID principles and Sandi Metz rules.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass(frozen=True)
class Citation:
    """
    Immutable citation model with validation.
    
    Represents a single academic citation with all metadata.
    Validates inputs to prevent invalid citations.
    """
    title: str
    authors: List[str]
    journal: str
    year: int
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        """Validate citation data after initialization."""
        self._validate_title()
        self._validate_authors()
        self._validate_year()
    
    def _validate_title(self) -> None:
        """Validate title is not empty."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")
    
    def _validate_authors(self) -> None:
        """Validate authors list is not empty."""
        if not self.authors or len(self.authors) == 0:
            raise ValueError("Authors cannot be empty")
    
    def _validate_year(self) -> None:
        """Validate publication year is reasonable."""
        current_year = datetime.now().year
        
        if self.year > current_year:
            raise ValueError("Publication year cannot be in the future")
        
        if self.year < 1900:
            raise ValueError("Publication year must be reasonable")
    
    def __eq__(self, other) -> bool:
        """Citation equality based on core identifying fields."""
        if not isinstance(other, Citation):
            return False
        
        return (
            self.title == other.title and
            self.authors == other.authors and
            self.journal == other.journal and
            self.year == other.year
        )
    
    def __hash__(self) -> int:
        """Hash based on core identifying fields."""
        return hash((
            self.title,
            tuple(self.authors),
            self.journal,
            self.year
        ))


@dataclass(frozen=True)
class VerificationResult:
    """
    Result of citation verification process.
    
    Contains verification status, confidence, and diagnostic info.
    Immutable to prevent tampering with verification results.
    """
    is_verified: bool
    confidence_score: float
    verification_source: str
    issues: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate verification result data."""
        self._validate_confidence()
        self._validate_source()
    
    def _validate_confidence(self) -> None:
        """Validate confidence score is between 0 and 1."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
    
    def _validate_source(self) -> None:
        """Validate verification source is recognized."""
        valid_sources = {
            'openalex', 'crossref', 'local_cache', 'error', 
            'openalex_crossref', 'api_error', 'concurrent_api_error'
        }
        if self.verification_source not in valid_sources:
            raise ValueError(f"Invalid verification source: {self.verification_source}")


@dataclass(frozen=True)
class ValidationReport:
    """
    Report of batch citation validation.
    
    Aggregates multiple verification results with summary statistics.
    Provides insights into overall citation quality.
    """
    total_citations: int
    verified_count: int
    fabricated_count: int
    verification_results: List[VerificationResult]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate report consistency."""
        self._validate_counts()
    
    def _validate_counts(self) -> None:
        """Validate that counts are consistent with results."""
        if len(self.verification_results) != self.total_citations:
            raise ValueError("Verification counts inconsistent with results")
        
        actual_verified = sum(1 for r in self.verification_results if r.is_verified)
        if actual_verified != self.verified_count:
            raise ValueError("Verified count inconsistent with results")
    
    @property
    def verification_rate(self) -> float:
        """Calculate percentage of verified citations."""
        if self.total_citations == 0:
            return 0.0
        return self.verified_count / self.total_citations
    
    @property
    def average_confidence(self) -> float:
        """Calculate average confidence score across all results."""
        if not self.verification_results:
            return 0.0
        
        total_confidence = sum(r.confidence_score for r in self.verification_results)
        return total_confidence / len(self.verification_results)