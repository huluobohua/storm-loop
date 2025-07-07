"""
Academic Validation Framework for Knowledge Storm

A comprehensive testing and validation system focused on academic research quality,
credibility establishment, and cross-disciplinary validation.

This framework provides:
- Academic Research Validation (PRISMA, citation accuracy, research quality benchmarks)
- Multi-Agent System Testing (coordination, concurrent processing, failure recovery)
- Academic Database Integration Tests (OpenAlex, Crossref, institutional databases)
- Performance and Scalability Testing (1000+ papers, 50+ concurrent users, memory profiling)
- Quality Assurance Testing (citation styles, academic formats, plagiarism detection)
- Cross-Disciplinary Validation (STEM, humanities, social sciences, interdisciplinary)
- Academic Benchmarking Studies (human vs AI, time efficiency, comprehensiveness)
- Automated Testing Infrastructure (CI/CD, regression testing, performance monitoring)
- Academic Credibility Establishment (peer-reviewed publication, expert advisory)
"""

from .core import AcademicValidationFramework
from .validators import (
    PRISMAValidator,
    CitationAccuracyValidator,
)

__all__ = [
    "AcademicValidationFramework",
    "PRISMAValidator",
    "CitationAccuracyValidator",
]

__version__ = "1.0.0"