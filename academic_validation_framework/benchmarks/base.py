"""
Base benchmark suite interface for academic validation.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..models import ValidationResult


@dataclass
class BenchmarkMetrics:
    """Metrics collected during benchmark execution."""
    
    execution_time: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    success_rate: Optional[float] = None
    custom_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


@dataclass
class BenchmarkContext:
    """Context for benchmark execution."""
    
    benchmark_type: str
    dataset_name: Optional[str] = None
    dataset_size: Optional[int] = None
    concurrency_level: Optional[int] = None
    target_metrics: Optional[Dict[str, float]] = None
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


class BaseBenchmarkSuite(ABC):
    """
    Base class for all academic benchmark suites.
    
    Provides common functionality for running benchmarks and collecting metrics.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the benchmark suite."""
        if not self._initialized:
            await self._initialize_benchmark_suite()
            self._initialized = True
    
    @abstractmethod
    async def _initialize_benchmark_suite(self) -> None:
        """Benchmark suite-specific initialization logic."""
        pass
    
    @abstractmethod
    async def run_benchmarks(
        self,
        research_output: Any,
        context: Optional[BenchmarkContext] = None,
        **kwargs: Any
    ) -> Union[ValidationResult, List[ValidationResult]]:
        """
        Run benchmark tests on research output.
        
        Args:
            research_output: The research output to benchmark
            context: Additional context for benchmarking
            **kwargs: Additional benchmark parameters
            
        Returns:
            ValidationResult or list of ValidationResults
        """
        pass
    
    async def run_benchmarks_with_metrics(
        self,
        research_output: Any,
        context: Optional[BenchmarkContext] = None,
        **kwargs: Any
    ) -> Union[ValidationResult, List[ValidationResult]]:
        """Run benchmarks with automatic metrics collection."""
        await self.initialize()
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = await self.run_benchmarks(research_output, context, **kwargs)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory if start_memory and end_memory else None
            
            # Create metrics
            metrics = BenchmarkMetrics(
                execution_time=execution_time,
                memory_usage=memory_delta,
                success_rate=1.0  # Successful execution
            )
            
            # Add metrics to results
            if isinstance(result, list):
                for r in result:
                    r.metadata.update({"benchmark_metrics": metrics.__dict__})
            else:
                result.metadata.update({"benchmark_metrics": metrics.__dict__})
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ValidationResult(
                validator_name=self.name,
                test_name="benchmark_execution",
                status="failed",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                execution_time=execution_time,
                metadata={
                    "benchmark_metrics": BenchmarkMetrics(
                        execution_time=execution_time,
                        success_rate=0.0
                    ).__dict__
                }
            )
            return error_result
    
    def _create_result(
        self,
        test_name: str,
        status: str,
        score: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metrics: Optional[BenchmarkMetrics] = None,
    ) -> ValidationResult:
        """Create a benchmark validation result."""
        result_metadata = metadata or {}
        
        if metrics:
            result_metadata["benchmark_metrics"] = metrics.__dict__
        
        return ValidationResult(
            validator_name=self.name,
            test_name=test_name,
            status=status,
            score=score,
            details=details or {},
            metadata=result_metadata,
        )
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return None
    
    def _calculate_throughput(
        self, 
        items_processed: int, 
        execution_time: float
    ) -> float:
        """Calculate throughput (items per second)."""
        if execution_time <= 0:
            return 0.0
        return items_processed / execution_time
    
    def _calculate_success_rate(
        self, 
        successful_operations: int, 
        total_operations: int
    ) -> float:
        """Calculate success rate."""
        if total_operations <= 0:
            return 0.0
        return successful_operations / total_operations
    
    def _calculate_error_rate(
        self, 
        failed_operations: int, 
        total_operations: int
    ) -> float:
        """Calculate error rate."""
        if total_operations <= 0:
            return 0.0
        return failed_operations / total_operations
    
    async def cleanup(self) -> None:
        """Cleanup benchmark resources."""
        pass
    
    def get_benchmark_info(self) -> Dict[str, Any]:
        """Get information about this benchmark suite."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "config": self.config,
            "initialized": self._initialized,
        }


class CompositeBenchmarkSuite(BaseBenchmarkSuite):
    """
    A benchmark suite that combines multiple sub-benchmark suites.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        benchmark_suites: List[BaseBenchmarkSuite],
        parallel_execution: bool = True,
        **kwargs
    ):
        super().__init__(name, description, **kwargs)
        self.benchmark_suites = benchmark_suites
        self.parallel_execution = parallel_execution
    
    async def _initialize_benchmark_suite(self) -> None:
        """Initialize all sub-benchmark suites."""
        if self.parallel_execution:
            await asyncio.gather(
                *[suite.initialize() for suite in self.benchmark_suites]
            )
        else:
            for suite in self.benchmark_suites:
                await suite.initialize()
    
    async def run_benchmarks(
        self,
        research_output: Any,
        context: Optional[BenchmarkContext] = None,
        **kwargs: Any
    ) -> List[ValidationResult]:
        """Run all sub-benchmark suites."""
        if self.parallel_execution:
            sub_results = await asyncio.gather(
                *[
                    suite.run_benchmarks_with_metrics(research_output, context, **kwargs)
                    for suite in self.benchmark_suites
                ],
                return_exceptions=True
            )
        else:
            sub_results = []
            for suite in self.benchmark_suites:
                try:
                    result = await suite.run_benchmarks_with_metrics(
                        research_output, context, **kwargs
                    )
                    sub_results.append(result)
                except Exception as e:
                    sub_results.append(e)
        
        # Flatten results and filter out exceptions
        all_results = []
        for result in sub_results:
            if not isinstance(result, Exception):
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    all_results.append(result)
            else:
                # Create error result for failed sub-benchmark
                error_result = ValidationResult(
                    validator_name=self.name,
                    test_name="sub_benchmark_execution",
                    status="failed",
                    details={
                        "error": str(result),
                        "error_type": type(result).__name__,
                    }
                )
                all_results.append(error_result)
        
        return all_results
    
    async def cleanup(self) -> None:
        """Cleanup all sub-benchmark suites."""
        await asyncio.gather(
            *[suite.cleanup() for suite in self.benchmark_suites],
            return_exceptions=True
        )


class PerformanceProfiler:
    """Helper class for collecting detailed performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.cpu_samples = []
        self._monitoring = False
    
    async def start_profiling(self, sample_interval: float = 0.1) -> None:
        """Start performance profiling."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self._monitoring = True
        
        # Start CPU monitoring in background
        asyncio.create_task(self._monitor_cpu(sample_interval))
    
    async def stop_profiling(self) -> BenchmarkMetrics:
        """Stop profiling and return metrics."""
        self.end_time = time.time()
        self.end_memory = self._get_memory_usage()
        self._monitoring = False
        
        execution_time = self.end_time - self.start_time if self.start_time else 0.0
        memory_delta = (
            self.end_memory - self.start_memory 
            if self.start_memory and self.end_memory 
            else None
        )
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else None
        
        return BenchmarkMetrics(
            execution_time=execution_time,
            memory_usage=memory_delta,
            cpu_usage=avg_cpu,
        )
    
    async def _monitor_cpu(self, interval: float) -> None:
        """Monitor CPU usage in background."""
        while self._monitoring:
            cpu_usage = self._get_cpu_usage()
            if cpu_usage is not None:
                self.cpu_samples.append(cpu_usage)
            await asyncio.sleep(interval)
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except ImportError:
            return None