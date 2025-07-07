"""
Data models for Academic Validation Framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ValidationStatus(Enum):
    """Validation status enumeration."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class BiasType(Enum):
    """Types of research bias."""
    CONFIRMATION = "confirmation_bias"
    PUBLICATION = "publication_bias"
    SELECTION = "selection_bias"
    FUNDING = "funding_bias"
    SAMPLING = "sampling_bias"
    REPORTING = "reporting_bias"
    CITATION = "citation_bias"


class CitationStyle(Enum):
    """Academic citation styles."""
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "Chicago"
    IEEE = "IEEE"
    HARVARD = "Harvard"
    VANCOUVER = "Vancouver"
    AMA = "AMA"


@dataclass
class ValidationResult:
    """Result of a validation test."""
    
    validator_name: str
    test_name: str
    status: ValidationStatus
    score: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASSED
    
    @property
    def failed(self) -> bool:
        return self.status == ValidationStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "validator_name": self.validator_name,
            "test_name": self.test_name,
            "status": self.status.value,
            "score": self.score,
            "details": self.details,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "recommendations": self.recommendations
        }


@dataclass
class ResearchData:
    """Research data to be validated."""
    
    title: str
    abstract: str
    methodology: str
    search_terms: List[str]
    databases_used: List[str]
    date_range: Optional[Dict[str, datetime]] = None
    inclusion_criteria: List[str] = field(default_factory=list)
    exclusion_criteria: List[str] = field(default_factory=list)
    papers: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    raw_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    protocol_registration: Optional[str] = None
    extraction_method: Optional[str] = None
    extracted_fields: List[str] = field(default_factory=list)


@dataclass
class ValidationRequest:
    """Request for validation."""
    
    research_data: ResearchData
    validators: List[str] = field(default_factory=list)
    benchmarks: List[str] = field(default_factory=list)
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class PRISMAResult:
    """PRISMA compliance validation result."""
    
    protocol_registered: bool
    search_strategy_score: float
    selection_criteria_score: float
    data_extraction_score: float
    bias_assessment_score: float
    overall_compliance: float
    checklist_items: Dict[str, bool] = field(default_factory=dict)
    missing_elements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CitationResult:
    """Citation validation result."""
    
    citation_text: str
    style: CitationStyle
    format_compliance: float
    completeness_score: float
    accuracy_score: float
    issues_found: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    formatted_citation: Optional[str] = None


@dataclass
class BiasAnalysisResult:
    """Bias analysis result."""
    
    bias_detected: bool
    bias_types: List[BiasType]
    confidence_score: float
    severity: str  # "low", "medium", "high"
    evidence: List[str] = field(default_factory=list)
    mitigation_recommendations: List[str] = field(default_factory=list)
    original_confidence: Optional[float] = None
    revised_confidence: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Performance benchmark metrics."""
    
    benchmark_name: str
    papers_processed: int
    total_time: float
    avg_time_per_paper: float
    memory_used_mb: float
    success_rate: float
    concurrent_users: Optional[int] = None
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationSession:
    """A complete validation session with all results."""
    
    session_id: str
    request: ValidationRequest
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: List[ValidationResult] = field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    
    @property
    def duration(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.failed)
    
    @property
    def total_count(self) -> int:
        return len(self.results)
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count