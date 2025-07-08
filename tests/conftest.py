"""
Pytest configuration and fixtures for comprehensive testing framework.
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List, Optional

from knowledge_storm.lm import OpenAIModel
from knowledge_storm.rm import VectorRM
from knowledge_storm.storm_wiki.engine import STORMWikiRunner
from knowledge_storm.services.config import STORMConfig
from knowledge_storm.services.crossref_service import CrossrefService
from knowledge_storm.services.academic_source_service import AcademicSourceService


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_openai_model():
    """Mock OpenAI model for testing."""
    model = Mock(spec=OpenAIModel)
    model.generate = AsyncMock(return_value="Generated text")
    model.model = "gpt-4"
    return model


@pytest.fixture
def mock_vector_rm():
    """Mock vector retrieval module."""
    rm = Mock(spec=VectorRM)
    rm.retrieve = AsyncMock(return_value=[
        {"title": "Test Paper", "abstract": "Test abstract", "url": "http://test.com"}
    ])
    return rm


@pytest.fixture
def mock_crossref_service():
    """Mock Crossref service."""
    service = Mock(spec=CrossrefService)
    service.search_papers = AsyncMock(return_value=[
        {
            "title": "Test Research Paper",
            "authors": ["John Doe", "Jane Smith"],
            "year": 2023,
            "doi": "10.1000/test",
            "abstract": "This is a test abstract for academic validation."
        }
    ])
    service.get_paper_details = AsyncMock(return_value={
        "title": "Test Research Paper",
        "authors": ["John Doe", "Jane Smith"],
        "year": 2023,
        "doi": "10.1000/test",
        "journal": "Test Journal",
        "citations": 42,
        "abstract": "This is a test abstract for academic validation."
    })
    return service


@pytest.fixture
def mock_academic_source_service():
    """Mock academic source service."""
    service = Mock(spec=AcademicSourceService)
    service.search_papers = AsyncMock(return_value=[
        {
            "id": "test_paper_1",
            "title": "Academic Research Test Paper",
            "authors": ["Dr. Academic", "Prof. Research"],
            "year": 2023,
            "venue": "Test Conference",
            "abstract": "Test abstract for academic validation testing."
        }
    ])
    return service


@pytest.fixture
def storm_config():
    """Create test STORM configuration."""
    config = STORMConfig()
    config.set_retrieval_module_type("vector")
    config.set_language_model_type("openai")
    return config


@pytest.fixture
def academic_test_data():
    """Academic test data for validation."""
    return {
        "topics": [
            "Machine Learning in Healthcare",
            "Climate Change Mitigation Strategies",
            "Quantum Computing Applications",
            "Sustainable Energy Technologies",
            "Artificial Intelligence Ethics"
        ],
        "disciplines": [
            "Computer Science",
            "Environmental Science",
            "Physics",
            "Engineering",
            "Philosophy"
        ],
        "citation_styles": ["APA", "MLA", "Chicago", "IEEE", "Harvard"],
        "research_methodologies": ["Systematic Review", "Meta-Analysis", "Case Study", "Survey"],
        "quality_metrics": {
            "min_citations": 10,
            "min_papers": 20,
            "coverage_threshold": 0.8,
            "relevance_threshold": 0.7
        }
    }


@pytest.fixture
def benchmark_datasets():
    """Benchmark datasets for academic validation."""
    return {
        "systematic_review_corpus": {
            "name": "Cochrane Systematic Reviews Sample",
            "size": 100,
            "topics": ["Medicine", "Healthcare", "Public Health"],
            "expected_quality": 0.9
        },
        "citation_accuracy_corpus": {
            "name": "IEEE Citation Accuracy Benchmark",
            "size": 500,
            "citation_styles": ["IEEE", "ACM"],
            "expected_accuracy": 0.95
        },
        "bias_detection_corpus": {
            "name": "Research Bias Detection Dataset",
            "size": 200,
            "bias_types": ["Selection", "Confirmation", "Publication"],
            "expected_detection_rate": 0.85
        }
    }


@pytest.fixture
def performance_benchmarks():
    """Performance benchmarks for scalability testing."""
    return {
        "load_scenarios": [
            {"concurrent_users": 1, "papers_per_request": 10},
            {"concurrent_users": 5, "papers_per_request": 50},
            {"concurrent_users": 10, "papers_per_request": 100},
            {"concurrent_users": 50, "papers_per_request": 1000}
        ],
        "performance_thresholds": {
            "max_response_time": 30.0,  # seconds
            "max_memory_usage": 2048,  # MB
            "min_success_rate": 0.95
        }
    }


@pytest.fixture
def expert_validation_criteria():
    """Expert validation criteria for academic quality assessment."""
    return {
        "research_quality_metrics": {
            "comprehensiveness": {"weight": 0.3, "min_score": 0.8},
            "accuracy": {"weight": 0.3, "min_score": 0.9},
            "relevance": {"weight": 0.2, "min_score": 0.8},
            "methodology": {"weight": 0.2, "min_score": 0.7}
        },
        "citation_quality_metrics": {
            "accuracy": {"weight": 0.4, "min_score": 0.95},
            "relevance": {"weight": 0.3, "min_score": 0.85},
            "completeness": {"weight": 0.3, "min_score": 0.8}
        },
        "overall_thresholds": {
            "min_expert_score": 0.8,
            "min_inter_rater_reliability": 0.7,
            "required_expert_consensus": 0.8
        }
    }


class MockExpertReviewer:
    """Mock expert reviewer for academic validation."""
    
    def __init__(self, expertise_area: str, bias_score: float = 0.1):
        self.expertise_area = expertise_area
        self.bias_score = bias_score
        self.review_history = []
    
    async def review_research_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate expert review of research output."""
        review = {
            "reviewer_id": f"expert_{self.expertise_area}",
            "expertise_area": self.expertise_area,
            "overall_score": 0.85 + (0.1 * (1 - self.bias_score)),
            "detailed_scores": {
                "comprehensiveness": 0.8,
                "accuracy": 0.9,
                "relevance": 0.85,
                "methodology": 0.8
            },
            "comments": f"Reviewed from {self.expertise_area} perspective",
            "recommendations": ["Improve methodology section", "Add more recent citations"],
            "confidence": 0.9
        }
        self.review_history.append(review)
        return review


@pytest.fixture
def mock_expert_panel():
    """Mock expert panel for validation."""
    return {
        "Computer Science": MockExpertReviewer("Computer Science", 0.05),
        "Medicine": MockExpertReviewer("Medicine", 0.08),
        "Environmental Science": MockExpertReviewer("Environmental Science", 0.06),
        "Physics": MockExpertReviewer("Physics", 0.04),
        "Social Sciences": MockExpertReviewer("Social Sciences", 0.12)
    }


@pytest.fixture
def academic_workflow_scenarios():
    """Academic workflow scenarios for end-to-end testing."""
    return [
        {
            "scenario": "Graduate Literature Review",
            "topic": "Deep Learning Applications in Medical Imaging",
            "requirements": {
                "min_papers": 50,
                "time_span": "2018-2023",
                "citation_style": "APA",
                "methodology": "Systematic Review"
            },
            "expected_outcomes": {
                "sections": ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"],
                "min_citations": 50,
                "quality_score": 0.8
            }
        },
        {
            "scenario": "Research Proposal Background",
            "topic": "Sustainable Transportation Systems",
            "requirements": {
                "min_papers": 30,
                "time_span": "2020-2024",
                "citation_style": "IEEE",
                "methodology": "Narrative Review"
            },
            "expected_outcomes": {
                "sections": ["Background", "Literature Gap", "Proposed Research"],
                "min_citations": 30,
                "quality_score": 0.75
            }
        },
        {
            "scenario": "Meta-Analysis Preparation",
            "topic": "Effectiveness of Online Learning",
            "requirements": {
                "min_papers": 100,
                "time_span": "2019-2024",
                "citation_style": "APA",
                "methodology": "Meta-Analysis"
            },
            "expected_outcomes": {
                "sections": ["Introduction", "Methods", "Results", "Discussion"],
                "min_citations": 100,
                "quality_score": 0.9
            }
        }
    ]