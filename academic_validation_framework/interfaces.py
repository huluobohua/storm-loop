"""
Abstract base classes and protocols for the academic validation framework.
This module defines interfaces to avoid circular imports.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime

from .models import (
    ValidationResult, 
    ValidationRequest,
    ResearchData,
    PRISMAResult,
    CitationResult,
    BiasAnalysisResult,
    PerformanceMetrics
)


class ValidatorProtocol(Protocol):
    """Protocol for all validators in the framework."""
    
    @property
    def name(self) -> str:
        """Unique name of the validator."""
        ...
    
    @property
    def version(self) -> str:
        """Version of the validator."""
        ...
    
    async def validate(self, data: ResearchData) -> ValidationResult:
        """
        Validate research data according to specific criteria.
        
        Args:
            data: Research data to validate
            
        Returns:
            ValidationResult containing scores and findings
        """
        ...
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current validator configuration."""
        ...


class BenchmarkProtocol(Protocol):
    """Protocol for performance benchmarks."""
    
    @property
    def name(self) -> str:
        """Benchmark name."""
        ...
    
    async def run(self, **kwargs) -> PerformanceMetrics:
        """
        Run the benchmark with given parameters.
        
        Returns:
            Performance metrics from the benchmark
        """
        ...
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get benchmark requirements (memory, CPU, etc.)."""
        ...


class CredibilityAssessorProtocol(Protocol):
    """Protocol for credibility assessment components."""
    
    async def assess(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Assess overall credibility based on validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Credibility assessment with scores and recommendations
        """
        ...


class ReportGeneratorProtocol(Protocol):
    """Protocol for report generation components."""
    
    async def generate(
        self, 
        session_id: str,
        results: List[ValidationResult],
        format: str = "json"
    ) -> str:
        """
        Generate a report from validation results.
        
        Args:
            session_id: Validation session identifier
            results: Validation results to include
            format: Output format (json, html, pdf, etc.)
            
        Returns:
            Generated report as string
        """
        ...


class DatabaseIntegrationProtocol(Protocol):
    """Protocol for academic database integrations."""
    
    @property
    def database_name(self) -> str:
        """Name of the integrated database."""
        ...
    
    async def search(self, query: str, **params) -> List[Dict[str, Any]]:
        """
        Search the database with given query.
        
        Args:
            query: Search query
            **params: Additional search parameters
            
        Returns:
            List of search results
        """
        ...
    
    async def fetch_metadata(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch detailed metadata for a specific item.
        
        Args:
            identifier: Database-specific identifier (DOI, ID, etc.)
            
        Returns:
            Metadata dictionary
        """
        ...


class SessionManagerProtocol(Protocol):
    """Protocol for validation session management."""
    
    def create_session(self, request: ValidationRequest) -> str:
        """Create a new validation session."""
        ...
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session information."""
        ...
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update session data."""
        ...
    
    def close_session(self, session_id: str) -> None:
        """Close and finalize a session."""
        ...


class ComponentRegistryProtocol(Protocol):
    """Protocol for component registration and management."""
    
    def register_validator(self, validator: ValidatorProtocol) -> None:
        """Register a validator."""
        ...
    
    def register_benchmark(self, benchmark: BenchmarkProtocol) -> None:
        """Register a benchmark."""
        ...
    
    def get_validators(self) -> List[ValidatorProtocol]:
        """Get all registered validators."""
        ...
    
    def get_benchmarks(self) -> List[BenchmarkProtocol]:
        """Get all registered benchmarks."""
        ...


# Abstract base classes for concrete implementations

class BaseValidator(ABC):
    """Abstract base class for validators."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self._name = name
        self._version = version
        self._config: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @abstractmethod
    async def validate(self, data: ResearchData) -> ValidationResult:
        """Must be implemented by subclasses."""
        pass
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self._config.copy()
    
    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self._config.update(config)


class BaseBenchmark(ABC):
    """Abstract base class for benchmarks."""
    
    def __init__(self, name: str):
        self._name = name
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @abstractmethod
    async def run(self, **kwargs) -> PerformanceMetrics:
        """Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_requirements(self) -> Dict[str, Any]:
        """Must be implemented by subclasses."""
        pass
    
    def _start_timing(self) -> None:
        """Start timing the benchmark."""
        self._start_time = datetime.now()
    
    def _stop_timing(self) -> float:
        """Stop timing and return duration in seconds."""
        self._end_time = datetime.now()
        if self._start_time:
            return (self._end_time - self._start_time).total_seconds()
        return 0.0


class BaseCredibilityAssessor(ABC):
    """Abstract base class for credibility assessors."""
    
    @abstractmethod
    async def assess(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Must be implemented by subclasses."""
        pass
    
    def calculate_overall_score(self, scores: List[float], weights: Optional[List[float]] = None) -> float:
        """Calculate weighted average score."""
        if not scores:
            return 0.0
        
        if weights is None:
            return sum(scores) / len(scores)
        
        if len(scores) != len(weights):
            raise ValueError("Scores and weights must have same length")
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        return sum(s * w for s, w in zip(scores, weights)) / total_weight


class BaseReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    SUPPORTED_FORMATS = ["json", "html", "markdown", "pdf"]
    
    @abstractmethod
    async def generate(
        self, 
        session_id: str,
        results: List[ValidationResult],
        format: str = "json"
    ) -> str:
        """Must be implemented by subclasses."""
        pass
    
    def validate_format(self, format: str) -> None:
        """Validate the requested format is supported."""
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS}")


class BaseDatabaseIntegration(ABC):
    """Abstract base class for database integrations."""
    
    def __init__(self, database_name: str, api_key: Optional[str] = None):
        self._database_name = database_name
        self._api_key = api_key
        self._rate_limiter = None
    
    @property
    def database_name(self) -> str:
        return self._database_name
    
    @abstractmethod
    async def search(self, query: str, **params) -> List[Dict[str, Any]]:
        """Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def fetch_metadata(self, identifier: str) -> Dict[str, Any]:
        """Must be implemented by subclasses."""
        pass
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting if configured."""
        if self._rate_limiter:
            await self._rate_limiter.acquire()