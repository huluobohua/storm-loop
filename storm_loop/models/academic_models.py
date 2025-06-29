"""
Data models for academic papers and metadata in STORM-Loop
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum


class SourceType(str, Enum):
    """Types of academic sources"""
    JOURNAL_ARTICLE = "journal-article"
    CONFERENCE_PAPER = "conference-paper"
    BOOK_CHAPTER = "book-chapter"
    BOOK = "book"
    PREPRINT = "preprint"
    THESIS = "thesis"
    REPORT = "report"
    OTHER = "other"


class Author(BaseModel):
    """Author information model"""
    display_name: str = Field(..., description="Full display name of the author")
    given_name: Optional[str] = Field(None, description="First/given name")
    family_name: Optional[str] = Field(None, description="Last/family name")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    affiliation: Optional[str] = Field(None, description="Primary affiliation")
    author_position: Optional[str] = Field(None, description="Position (first, middle, last)")

    @validator('orcid')
    def validate_orcid(cls, v):
        if v and not v.startswith('https://orcid.org/'):
            return f"https://orcid.org/{v}"
        return v


class Journal(BaseModel):
    """Journal/venue information model"""
    name: str = Field(..., description="Journal or venue name")
    issn: Optional[str] = Field(None, description="ISSN identifier")
    publisher: Optional[str] = Field(None, description="Publisher name")
    impact_factor: Optional[float] = Field(None, description="Journal impact factor")
    h_index: Optional[int] = Field(None, description="Journal h-index")


class Concept(BaseModel):
    """Academic concept/topic model"""
    id: str = Field(..., description="Concept identifier")
    display_name: str = Field(..., description="Human-readable concept name")
    score: Optional[float] = Field(None, description="Relevance score")
    level: Optional[int] = Field(None, description="Concept hierarchy level")


class AcademicPaper(BaseModel):
    """Comprehensive academic paper model"""
    
    # Core identifiers
    id: str = Field(..., description="Unique paper identifier")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    openalex_id: Optional[str] = Field(None, description="OpenAlex identifier")
    
    # Basic metadata
    title: str = Field(..., description="Paper title")
    abstract: Optional[str] = Field(None, description="Paper abstract")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    publication_date: Optional[str] = Field(None, description="Full publication date")
    
    # Authors and venue
    authors: List[Author] = Field(default_factory=list, description="List of authors")
    journal: Optional[Journal] = Field(None, description="Journal/venue information")
    source_type: Optional[SourceType] = Field(None, description="Type of academic source")
    
    # Content and classification
    concepts: List[Concept] = Field(default_factory=list, description="Academic concepts/topics")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    
    # Metrics and quality indicators
    citation_count: Optional[int] = Field(None, description="Number of citations")
    referenced_works_count: Optional[int] = Field(None, description="Number of references")
    is_open_access: Optional[bool] = Field(None, description="Open access status")
    
    # Full text and URLs
    pdf_url: Optional[HttpUrl] = Field(None, description="PDF download URL")
    landing_page_url: Optional[HttpUrl] = Field(None, description="Publisher landing page")
    external_urls: List[HttpUrl] = Field(default_factory=list, description="Other relevant URLs")
    
    # Quality and relevance scores
    quality_score: Optional[float] = Field(None, description="Computed quality score")
    relevance_score: Optional[float] = Field(None, description="Relevance to query score")
    
    # Timestamps
    indexed_date: Optional[datetime] = Field(None, description="Date indexed in source")
    created_date: Optional[datetime] = Field(None, description="Date created in our system")
    
    # Raw data
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Original API response")

    @validator('publication_year')
    def validate_publication_year(cls, v):
        if v and (v < 1400 or v > datetime.now().year + 2):
            raise ValueError('Publication year must be reasonable')
        return v

    @validator('citation_count', 'referenced_works_count')
    def validate_counts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Counts cannot be negative')
        return v

    @validator('quality_score', 'relevance_score')
    def validate_scores(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v


class SearchQuery(BaseModel):
    """Academic search query model"""
    query: str = Field(..., description="Search query string")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(default=10, description="Maximum results to return")
    offset: int = Field(default=0, description="Results offset for pagination")
    sort_by: Optional[str] = Field(None, description="Sort criteria")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v <= 0 or v > 200:
            raise ValueError('Limit must be between 1 and 200')
        return v

    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('Offset cannot be negative')
        return v


class SearchResult(BaseModel):
    """Search result container model"""
    query: SearchQuery = Field(..., description="Original search query")
    papers: List[AcademicPaper] = Field(default_factory=list, description="Found papers")
    total_count: Optional[int] = Field(None, description="Total available results")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor")
    search_time_ms: Optional[float] = Field(None, description="Search duration in milliseconds")
    source: str = Field(..., description="Source API (openalex, crossref, etc.)")


class QualityMetrics(BaseModel):
    """Quality assessment metrics for academic papers"""
    citation_score: float = Field(default=0.0, description="Normalized citation score")
    recency_score: float = Field(default=0.0, description="Recency/freshness score")
    venue_score: float = Field(default=0.0, description="Journal/venue quality score")
    author_score: float = Field(default=0.0, description="Author reputation score")
    content_score: float = Field(default=0.0, description="Content quality indicators")
    overall_score: float = Field(default=0.0, description="Overall quality score")
    
    # Detailed metrics
    h_index_normalized: Optional[float] = Field(None, description="Normalized h-index")
    impact_factor_normalized: Optional[float] = Field(None, description="Normalized impact factor")
    open_access_bonus: float = Field(default=0.0, description="Open access accessibility bonus")
    
    # Flags and indicators
    is_predatory: bool = Field(default=False, description="Potential predatory publication flag")
    is_retracted: bool = Field(default=False, description="Paper retraction flag")
    has_peer_review: Optional[bool] = Field(None, description="Peer review status")
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'citation_score': 0.3,
            'venue_score': 0.25,
            'recency_score': 0.2,
            'author_score': 0.15,
            'content_score': 0.1
        }
        
        overall = sum(
            getattr(self, metric) * weight 
            for metric, weight in weights.items()
        )
        
        # Apply bonuses and penalties
        if self.open_access_bonus:
            overall += self.open_access_bonus * 0.05
        
        if self.is_predatory:
            overall *= 0.1  # Heavy penalty
        
        if self.is_retracted:
            overall = 0.0  # Complete penalty
        
        self.overall_score = max(0.0, min(1.0, overall))
        return self.overall_score


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = Field(default=True, description="Request success status")
    data: Union[AcademicPaper, SearchResult, List[AcademicPaper]] = Field(..., description="Response data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    api_source: str = Field(..., description="Source API")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    rate_limit_remaining: Optional[int] = Field(None, description="Remaining API calls")
    cache_hit: bool = Field(default=False, description="Whether result was cached")