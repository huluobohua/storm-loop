from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class ValidationResult:
    """Simple validation result data structure."""
    test_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    error_message: str = ""
    execution_time_seconds: float = 0.0
    timestamp: datetime = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ResearchData:
    """Simplified research data structure for validation."""
    title: str
    abstract: str
    methodology_section: str
    search_terms: Optional[List[str]] = None
    databases_searched: Optional[List[str]] = None
    inclusion_criteria: Optional[List[str]] = None
    exclusion_criteria: Optional[List[str]] = None
    studies_found: int = 0
    studies_included: int = 0
    data_extraction_method: str = ""
    quality_assessment_tool: str = ""
    references: Optional[List[Dict[str, str]]] = None

    def __post_init__(self) -> None:
        self.search_terms = self.search_terms or []
        self.databases_searched = self.databases_searched or []
        self.inclusion_criteria = self.inclusion_criteria or []
        self.exclusion_criteria = self.exclusion_criteria or []
        self.references = self.references or []

class ValidatorProtocol(ABC):
    """Protocol for all validation components."""

    @abstractmethod
    async def validate(self, data: Any) -> ValidationResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_data_types(self) -> List[type]:
        pass

class BenchmarkProtocol(ABC):
    """Protocol for benchmark components."""

    @abstractmethod
    async def benchmark(self, target: Any, config: Optional[Dict[str, Any]] = None) -> ValidationResult:
        pass

    @property
    @abstractmethod
    def benchmark_categories(self) -> List[str]:
        pass

class DatabaseIntegrationProtocol(ABC):
    """Protocol for database integration testing."""

    @abstractmethod
    async def test_integration(self, config: Dict[str, Any]) -> ValidationResult:
        pass

    @property
    @abstractmethod
    def supported_databases(self) -> List[str]:
        pass

class CredibilityAssessorProtocol(ABC):
    """Protocol for credibility assessment."""

    @abstractmethod
    async def assess_credibility(self, research_data: ResearchData) -> ValidationResult:
        pass

    @property
    @abstractmethod
    def assessment_criteria(self) -> List[str]:
        pass

class ReportGeneratorProtocol(ABC):
    """Protocol for report generation."""

    @abstractmethod
    async def generate_report(self, results: List[ValidationResult], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        pass

class ValidationError(Exception):
    pass

class ConfigurationError(Exception):
    pass

class IntegrationError(Exception):
    pass
