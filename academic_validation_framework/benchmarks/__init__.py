"""
Academic benchmarking modules for performance and quality assessment.
"""

from .base import BaseBenchmarkSuite
from .performance_benchmark_suite import PerformanceBenchmarkSuite

__all__ = [
    "BaseBenchmarkSuite",
    "PerformanceBenchmarkSuite", 
]