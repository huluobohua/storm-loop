"""
Configuration module for Academic Validation Framework.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import (
        ValidatorProtocol,
        BenchmarkProtocol,
        DatabaseIntegrationProtocol,
        CredibilityAssessorProtocol,
        ReportGeneratorProtocol
    )


@dataclass
class FrameworkConfig:
    """Configuration for the Academic Validation Framework."""
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    console_logging: bool = True
    
    # Output configuration
    output_dir: str = "validation_results"
    auto_generate_reports: bool = True
    report_formats: List[str] = field(default_factory=lambda: ["json", "html", "pdf"])
    
    # Performance configuration
    max_concurrent_tests: int = 10
    timeout_seconds: int = 300
    retry_attempts: int = 3
    
    # Academic validation configuration
    min_citation_accuracy: float = 0.95
    min_prisma_compliance: float = 0.80
    min_research_quality_score: float = 0.75
    min_bias_detection_rate: float = 0.85
    min_expert_consensus: float = 0.70
    
    # Database integration configuration
    crossref_api_timeout: int = 10
    openalex_api_timeout: int = 15
    semantic_scholar_timeout: int = 12
    max_api_retries: int = 3
    rate_limit_delay: float = 1.0
    
    # Performance benchmarks
    max_response_time_seconds: float = 30.0
    max_memory_usage_mb: int = 2048
    min_throughput_papers_per_minute: int = 60
    max_concurrent_users: int = 50
    
    # Cross-disciplinary validation
    supported_disciplines: List[str] = field(default_factory=lambda: [
        "Computer Science",
        "Medicine", 
        "Environmental Science",
        "Physics",
        "Social Sciences",
        "Biology",
        "Chemistry",
        "Psychology",
        "Economics",
        "Engineering"
    ])
    
    # Citation style support
    supported_citation_styles: List[str] = field(default_factory=lambda: [
        "APA", "MLA", "Chicago", "IEEE", "Harvard", "Vancouver", "APSA", "ASA"
    ])
    
    # Research methodology validation
    supported_methodologies: List[str] = field(default_factory=lambda: [
        "Systematic Review",
        "Meta-Analysis", 
        "Narrative Review",
        "Scoping Review",
        "Case Study",
        "Survey Research",
        "Experimental Study",
        "Observational Study"
    ])
    
    # Quality thresholds by discipline
    discipline_quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "Computer Science": 0.80,
        "Medicine": 0.90,
        "Environmental Science": 0.85,
        "Physics": 0.85,
        "Social Sciences": 0.75,
        "Biology": 0.85,
        "Chemistry": 0.85,
        "Psychology": 0.80,
        "Economics": 0.75,
        "Engineering": 0.80,
    })
    
    # Plagiarism detection
    plagiarism_similarity_threshold: float = 0.25
    enable_semantic_similarity_check: bool = True
    enable_citation_overlap_check: bool = True
    
    # Expert validation panel
    min_expert_reviewers: int = 3
    max_expert_reviewers: int = 7
    expert_agreement_threshold: float = 0.70
    expert_confidence_threshold: float = 0.80
    
    # Benchmarking configuration
    benchmark_datasets: Dict[str, Any] = field(default_factory=lambda: {
        "systematic_review_corpus": {
            "name": "Cochrane Systematic Reviews Sample",
            "size": 100,
            "expected_quality": 0.90
        },
        "citation_accuracy_corpus": {
            "name": "IEEE Citation Accuracy Benchmark", 
            "size": 500,
            "expected_accuracy": 0.95
        },
        "bias_detection_corpus": {
            "name": "Research Bias Detection Dataset",
            "size": 200,
            "expected_detection_rate": 0.85
        },
        "interdisciplinary_corpus": {
            "name": "Cross-Disciplinary Research Dataset",
            "size": 150,
            "disciplines": ["CS", "Medicine", "Environmental Science"],
            "expected_coverage": 0.80
        }
    })
    
    # CI/CD integration
    enable_ci_reporting: bool = False
    ci_failure_threshold: float = 0.80  # Fail CI if success rate below this
    generate_junit_xml: bool = False
    
    # Academic credibility features
    enable_peer_review_simulation: bool = True
    enable_publication_readiness_assessment: bool = True
    enable_impact_prediction: bool = False
    
    # Experimental features
    enable_ai_bias_detection: bool = True
    enable_methodology_recommendation: bool = True
    enable_literature_gap_analysis: bool = True
    enable_research_trend_analysis: bool = False
    
    # Component configuration - initialized in __post_init__ or externally
    validators: List['ValidatorProtocol'] = field(default_factory=list)
    benchmarks: List['BenchmarkProtocol'] = field(default_factory=list)
    database_testers: List['DatabaseIntegrationProtocol'] = field(default_factory=list)
    credibility_assessors: List['CredibilityAssessorProtocol'] = field(default_factory=list)
    report_generators: List['ReportGeneratorProtocol'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Validate thresholds
        if not 0.0 <= self.min_citation_accuracy <= 1.0:
            raise ValueError("min_citation_accuracy must be between 0.0 and 1.0")
        
        if not 0.0 <= self.min_prisma_compliance <= 1.0:
            raise ValueError("min_prisma_compliance must be between 0.0 and 1.0")
        
        if not 0.0 <= self.min_research_quality_score <= 1.0:
            raise ValueError("min_research_quality_score must be between 0.0 and 1.0")
        
        if self.max_concurrent_tests <= 0:
            raise ValueError("max_concurrent_tests must be positive")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "FrameworkConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def update(self, **kwargs: Any) -> None:
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def get_discipline_threshold(self, discipline: str) -> float:
        """Get quality threshold for a specific discipline."""
        return self.discipline_quality_thresholds.get(
            discipline, 
            self.min_research_quality_score
        )
    
    def is_supported_discipline(self, discipline: str) -> bool:
        """Check if a discipline is supported."""
        return discipline in self.supported_disciplines
    
    def is_supported_citation_style(self, style: str) -> bool:
        """Check if a citation style is supported."""
        return style in self.supported_citation_styles
    
    def is_supported_methodology(self, methodology: str) -> bool:
        """Check if a research methodology is supported."""
        return methodology in self.supported_methodologies


@dataclass 
class ValidationThresholds:
    """Specific validation thresholds for different test types."""
    
    # PRISMA compliance thresholds
    prisma_search_strategy: float = 0.80
    prisma_inclusion_criteria: float = 0.75
    prisma_data_extraction: float = 0.85
    prisma_quality_assessment: float = 0.80
    prisma_synthesis_method: float = 0.75
    
    # Citation accuracy thresholds
    citation_format_accuracy: float = 0.95
    citation_completeness: float = 0.90
    citation_relevance: float = 0.85
    citation_recency: float = 0.70
    
    # Research quality thresholds
    comprehensiveness: float = 0.80
    accuracy: float = 0.90
    relevance: float = 0.85
    methodology_rigor: float = 0.75
    reproducibility: float = 0.80
    
    # Bias detection thresholds
    selection_bias_detection: float = 0.85
    confirmation_bias_detection: float = 0.80
    publication_bias_detection: float = 0.90
    reporting_bias_detection: float = 0.85
    
    # Performance thresholds
    response_time_p95: float = 25.0  # seconds
    response_time_p99: float = 45.0  # seconds
    memory_usage_p95: float = 1800.0  # MB
    cpu_usage_p95: float = 80.0  # percent
    
    # Scalability thresholds
    concurrent_users_max: int = 100
    papers_processed_per_hour: int = 3600
    database_query_time_max: float = 5.0  # seconds
    
    def to_dict(self) -> Dict[str, float]:
        """Convert thresholds to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


@dataclass
class ExpertPanelConfig:
    """Configuration for expert validation panel."""
    
    # Panel composition
    min_experts_per_discipline: int = 2
    max_experts_per_discipline: int = 5
    require_interdisciplinary_experts: bool = True
    
    # Expertise requirements
    min_years_experience: int = 5
    min_publications: int = 10
    min_h_index: int = 5
    
    # Review process
    blind_review: bool = True
    double_blind_review: bool = False
    review_time_limit_days: int = 14
    allow_expert_discussion: bool = True
    
    # Consensus requirements
    min_consensus_score: float = 0.70
    max_disagreement_threshold: float = 0.30
    require_unanimous_critical_issues: bool = True
    
    # Quality control
    track_reviewer_bias: bool = True
    validate_expert_credentials: bool = True
    monitor_review_quality: bool = True


@dataclass
class ValidationConfig:
    """Centralized configuration for validation framework."""

    # Thresholds
    citation_accuracy_threshold: float = 0.95
    prisma_compliance_threshold: float = 0.80
    bias_detection_threshold: float = 0.85

    # Performance
    max_concurrent_validations: int = 50
    timeout_seconds: int = 30
    memory_limit_mb: int = 2048

    # API Configuration
    api_rate_limits: Dict[str, int] = None
    retry_attempts: int = 3
    backoff_factor: float = 2.0

    def __post_init__(self):
        if self.api_rate_limits is None:
            self.api_rate_limits = {
                'openAlex': 10,  # requests per second
                'crossref': 5,
                'institutional': 2
            }
