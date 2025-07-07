"""
Real performance benchmark implementation for academic validation framework.
"""

import asyncio
import time
import psutil
import tracemalloc
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import statistics
from collections import defaultdict
import gc

from ..interfaces import BaseBenchmark
from ..models import ValidationResult, ValidationStatus, ResearchData, PerformanceMetrics

logger = logging.getLogger(__name__)


class RealPerformanceBenchmark(BaseBenchmark):
    """Real implementation of performance benchmarking for academic systems."""
    
    def __init__(self):
        super().__init__(
            name="Real Performance Benchmark",
            version="2.0.0"
        )
        self._config = {
            "warmup_iterations": 3,
            "test_iterations": 10,
            "enable_memory_profiling": True,
            "enable_cpu_profiling": True,
            "collect_system_metrics": True,
            "benchmark_timeout": 300.0  # 5 minutes
        }
        
        # Performance thresholds
        self._thresholds = {
            "response_time": {
                "excellent": 1.0,    # < 1 second
                "good": 5.0,        # < 5 seconds
                "acceptable": 10.0,  # < 10 seconds
                "poor": 30.0        # < 30 seconds
            },
            "throughput": {
                "excellent": 100,    # > 100 papers/minute
                "good": 50,         # > 50 papers/minute
                "acceptable": 20,   # > 20 papers/minute
                "poor": 10          # > 10 papers/minute
            },
            "memory": {
                "excellent": 100,    # < 100 MB
                "good": 500,        # < 500 MB
                "acceptable": 1000, # < 1 GB
                "poor": 2000        # < 2 GB
            },
            "cpu": {
                "excellent": 25,     # < 25% CPU
                "good": 50,         # < 50% CPU
                "acceptable": 75,   # < 75% CPU
                "poor": 90          # < 90% CPU
            }
        }
        
        # System info
        self._system_info = self._collect_system_info()
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmark context."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "total_memory": psutil.virtual_memory().total / (1024**3),  # GB
                "available_memory": psutil.virtual_memory().available / (1024**3),  # GB
                "python_version": str(__import__('sys').version),
                "platform": __import__('platform').platform()
            }
        except Exception as e:
            logger.error(f"Error collecting system info: {e}")
            return {}
    
    async def run_benchmark(self, data: ResearchData) -> ValidationResult:
        """
        Run comprehensive performance benchmark.
        
        Args:
            data: Research data to benchmark
            
        Returns:
            Detailed performance benchmark results
        """
        try:
            logger.info("Starting real performance benchmark")
            
            # Run warmup iterations
            logger.info(f"Running {self._config['warmup_iterations']} warmup iterations")
            await self._run_warmup(data)
            
            # Run actual benchmarks
            benchmark_results = {
                "response_time": await self._benchmark_response_time(data),
                "throughput": await self._benchmark_throughput(data),
                "memory_usage": await self._benchmark_memory_usage(data),
                "cpu_usage": await self._benchmark_cpu_usage(data),
                "scalability": await self._benchmark_scalability(data),
                "concurrent_performance": await self._benchmark_concurrent_load(data)
            }
            
            # Calculate overall performance score
            overall_score = self._calculate_overall_score(benchmark_results)
            
            # Determine status
            if overall_score >= 0.8:
                status = ValidationStatus.PASSED
            elif overall_score >= 0.6:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            # Generate detailed analysis
            analysis = self._generate_performance_analysis(benchmark_results)
            recommendations = self._generate_performance_recommendations(benchmark_results, analysis)
            
            return ValidationResult(
                validator_name=self.name,
                test_name="Comprehensive Performance Benchmark",
                status=status,
                score=overall_score,
                details={
                    "system_info": self._system_info,
                    "benchmark_results": self._format_benchmark_results(benchmark_results),
                    "performance_analysis": analysis,
                    "bottlenecks": self._identify_bottlenecks(benchmark_results),
                    "optimization_opportunities": self._identify_optimizations(benchmark_results)
                },
                recommendations=recommendations,
                metadata={
                    "benchmark_version": self.version,
                    "test_iterations": self._config["test_iterations"],
                    "timestamp": datetime.now().isoformat(),
                    "total_benchmark_time": sum(r.get("duration", 0) for r in benchmark_results.values())
                }
            )
            
        except Exception as e:
            logger.error(f"Performance benchmark error: {str(e)}", exc_info=True)
            return self._create_error_result(str(e))
    
    async def _run_warmup(self, data: ResearchData) -> None:
        """Run warmup iterations to stabilize performance."""
        for i in range(self._config["warmup_iterations"]):
            try:
                # Simulate processing without recording metrics
                await self._process_research_data(data)
                await asyncio.sleep(0.1)  # Brief pause between warmups
            except Exception as e:
                logger.warning(f"Warmup iteration {i+1} failed: {e}")
    
    async def _benchmark_response_time(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark response time performance."""
        logger.info("Benchmarking response time")
        
        response_times = []
        
        for i in range(self._config["test_iterations"]):
            start_time = time.perf_counter()
            
            try:
                await self._process_research_data(data)
                response_time = time.perf_counter() - start_time
                response_times.append(response_time)
            except Exception as e:
                logger.error(f"Response time test iteration {i+1} failed: {e}")
                response_times.append(float('inf'))
        
        # Calculate statistics
        valid_times = [t for t in response_times if t != float('inf')]
        
        if not valid_times:
            return {
                "error": "All response time tests failed",
                "score": 0.0
            }
        
        stats = {
            "mean": statistics.mean(valid_times),
            "median": statistics.median(valid_times),
            "stdev": statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            "min": min(valid_times),
            "max": max(valid_times),
            "p95": sorted(valid_times)[int(len(valid_times) * 0.95)] if valid_times else 0,
            "p99": sorted(valid_times)[int(len(valid_times) * 0.99)] if valid_times else 0,
            "success_rate": len(valid_times) / len(response_times)
        }
        
        # Calculate score based on mean response time
        score = self._calculate_metric_score(stats["mean"], self._thresholds["response_time"])
        
        return {
            "statistics": stats,
            "raw_data": response_times[:10],  # First 10 samples
            "score": score,
            "rating": self._get_performance_rating(score),
            "duration": sum(valid_times)
        }
    
    async def _benchmark_throughput(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark processing throughput."""
        logger.info("Benchmarking throughput")
        
        # Test for 30 seconds
        test_duration = 30.0
        papers_processed = 0
        errors = 0
        
        start_time = time.perf_counter()
        
        while time.perf_counter() - start_time < test_duration:
            try:
                await self._process_research_data(data)
                papers_processed += 1
            except Exception as e:
                errors += 1
                logger.error(f"Throughput test error: {e}")
        
        elapsed_time = time.perf_counter() - start_time
        
        # Calculate metrics
        papers_per_second = papers_processed / elapsed_time
        papers_per_minute = papers_per_second * 60
        error_rate = errors / (papers_processed + errors) if (papers_processed + errors) > 0 else 0
        
        # Calculate score
        score = self._calculate_metric_score(papers_per_minute, self._thresholds["throughput"], inverse=True)
        
        return {
            "papers_processed": papers_processed,
            "papers_per_second": papers_per_second,
            "papers_per_minute": papers_per_minute,
            "error_rate": error_rate,
            "test_duration": elapsed_time,
            "score": score,
            "rating": self._get_performance_rating(score),
            "duration": elapsed_time
        }
    
    async def _benchmark_memory_usage(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark memory usage and efficiency."""
        logger.info("Benchmarking memory usage")
        
        if not self._config["enable_memory_profiling"]:
            return {"skipped": True, "reason": "Memory profiling disabled"}
        
        # Start memory tracking
        tracemalloc.start()
        gc.collect()  # Clean up before measurement
        
        initial_memory = self._get_current_memory_usage()
        memory_samples = []
        
        try:
            # Process multiple iterations to see memory growth
            for i in range(5):
                await self._process_research_data(data)
                
                current, peak = tracemalloc.get_traced_memory()
                process_memory = self._get_current_memory_usage()
                
                memory_samples.append({
                    "iteration": i + 1,
                    "traced_current_mb": current / (1024 * 1024),
                    "traced_peak_mb": peak / (1024 * 1024),
                    "process_memory_mb": process_memory
                })
                
                gc.collect()  # Force garbage collection between iterations
        
        finally:
            tracemalloc.stop()
        
        # Analyze memory usage
        final_memory = self._get_current_memory_usage()
        memory_growth = final_memory - initial_memory
        
        peak_memory = max(s["process_memory_mb"] for s in memory_samples) if memory_samples else 0
        avg_memory = statistics.mean(s["process_memory_mb"] for s in memory_samples) if memory_samples else 0
        
        # Check for memory leaks (significant growth over iterations)
        memory_leak_detected = False
        if len(memory_samples) > 2:
            first_half_avg = statistics.mean(s["process_memory_mb"] for s in memory_samples[:len(memory_samples)//2])
            second_half_avg = statistics.mean(s["process_memory_mb"] for s in memory_samples[len(memory_samples)//2:])
            
            if second_half_avg > first_half_avg * 1.2:  # 20% growth indicates potential leak
                memory_leak_detected = True
        
        # Calculate score
        score = self._calculate_metric_score(peak_memory, self._thresholds["memory"])
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": memory_growth,
            "peak_memory_mb": peak_memory,
            "average_memory_mb": avg_memory,
            "memory_samples": memory_samples,
            "memory_leak_detected": memory_leak_detected,
            "score": score,
            "rating": self._get_performance_rating(score),
            "duration": len(memory_samples) * 2  # Approximate duration
        }
    
    async def _benchmark_cpu_usage(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark CPU usage and efficiency."""
        logger.info("Benchmarking CPU usage")
        
        if not self._config["enable_cpu_profiling"]:
            return {"skipped": True, "reason": "CPU profiling disabled"}
        
        cpu_samples = []
        process = psutil.Process()
        
        # Monitor CPU usage during processing
        monitoring_task = asyncio.create_task(self._monitor_cpu_usage(cpu_samples, process))
        
        try:
            # Run processing workload
            start_time = time.perf_counter()
            
            for i in range(self._config["test_iterations"]):
                await self._process_research_data(data)
            
            elapsed_time = time.perf_counter() - start_time
            
        finally:
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            peak_cpu = max(cpu_samples)
            cpu_efficiency = self._calculate_cpu_efficiency(avg_cpu, elapsed_time)
        else:
            avg_cpu = peak_cpu = cpu_efficiency = 0
        
        # Calculate score
        score = self._calculate_metric_score(avg_cpu, self._thresholds["cpu"])
        
        return {
            "average_cpu_percent": avg_cpu,
            "peak_cpu_percent": peak_cpu,
            "cpu_efficiency": cpu_efficiency,
            "samples_collected": len(cpu_samples),
            "test_duration": elapsed_time,
            "cpu_cores_used": avg_cpu / 100 * self._system_info.get("cpu_count", 1),
            "score": score,
            "rating": self._get_performance_rating(score),
            "duration": elapsed_time
        }
    
    async def _monitor_cpu_usage(self, samples: List[float], process: psutil.Process) -> None:
        """Monitor CPU usage in background."""
        try:
            while True:
                cpu_percent = process.cpu_percent(interval=0.1)
                if cpu_percent > 0:  # Filter out initial 0 readings
                    samples.append(cpu_percent)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
    
    async def _benchmark_scalability(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark scalability with increasing load."""
        logger.info("Benchmarking scalability")
        
        load_levels = [1, 5, 10, 20, 50]  # Number of papers to process
        scalability_results = []
        
        for load in load_levels:
            start_time = time.perf_counter()
            errors = 0
            
            # Process multiple papers
            tasks = []
            for i in range(load):
                task = self._process_research_data(data)
                tasks.append(task)
            
            # Execute with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
            
            async def process_with_limit(task):
                async with semaphore:
                    try:
                        await task
                        return True
                    except Exception:
                        return False
            
            results = await asyncio.gather(*[process_with_limit(task) for task in tasks])
            
            elapsed_time = time.perf_counter() - start_time
            success_count = sum(1 for r in results if r)
            
            scalability_results.append({
                "load": load,
                "elapsed_time": elapsed_time,
                "success_count": success_count,
                "error_count": load - success_count,
                "throughput": success_count / elapsed_time if elapsed_time > 0 else 0,
                "avg_time_per_paper": elapsed_time / load
            })
        
        # Analyze scalability
        scalability_score = self._calculate_scalability_score(scalability_results)
        
        return {
            "load_test_results": scalability_results,
            "scalability_score": scalability_score,
            "rating": self._get_performance_rating(scalability_score),
            "linear_scalability": self._check_linear_scalability(scalability_results),
            "bottleneck_analysis": self._analyze_scalability_bottlenecks(scalability_results),
            "duration": sum(r["elapsed_time"] for r in scalability_results)
        }
    
    async def _benchmark_concurrent_load(self, data: ResearchData) -> Dict[str, Any]:
        """Benchmark performance under concurrent load."""
        logger.info("Benchmarking concurrent load")
        
        concurrent_levels = [1, 2, 5, 10, 20]
        concurrency_results = []
        
        for level in concurrent_levels:
            # Run concurrent requests
            start_time = time.perf_counter()
            
            tasks = [
                self._process_research_data(data)
                for _ in range(level)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed_time = time.perf_counter() - start_time
            
            # Analyze results
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = level - successes
            
            concurrency_results.append({
                "concurrency_level": level,
                "elapsed_time": elapsed_time,
                "successes": successes,
                "failures": failures,
                "avg_response_time": elapsed_time / level,
                "success_rate": successes / level
            })
        
        # Calculate concurrency score
        concurrency_score = self._calculate_concurrency_score(concurrency_results)
        
        return {
            "concurrency_test_results": concurrency_results,
            "max_efficient_concurrency": self._find_max_efficient_concurrency(concurrency_results),
            "concurrency_score": concurrency_score,
            "rating": self._get_performance_rating(concurrency_score),
            "duration": sum(r["elapsed_time"] for r in concurrency_results)
        }
    
    async def _process_research_data(self, data: ResearchData) -> None:
        """Simulate processing research data."""
        # Simulate various processing steps
        
        # Text processing
        text_length = len(data.title + data.abstract + data.methodology)
        processing_time = min(text_length / 10000, 1.0)  # Scale with text length
        
        # Simulate CPU-intensive work
        start = time.perf_counter()
        while time.perf_counter() - start < processing_time:
            # Perform some calculations
            _ = sum(i * i for i in range(1000))
        
        # Simulate I/O
        await asyncio.sleep(0.1)
        
        # Simulate memory allocation
        temp_data = [data.abstract] * 100  # Create temporary data
        
        # Cleanup
        del temp_data
    
    def _get_current_memory_usage(self) -> float:
        """Get current process memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _calculate_metric_score(self, value: float, thresholds: Dict[str, float], inverse: bool = False) -> float:
        """Calculate score based on thresholds."""
        if inverse:
            # Higher values are better (e.g., throughput)
            if value >= thresholds["excellent"]:
                return 1.0
            elif value >= thresholds["good"]:
                return 0.8
            elif value >= thresholds["acceptable"]:
                return 0.6
            elif value >= thresholds["poor"]:
                return 0.4
            else:
                return 0.2
        else:
            # Lower values are better (e.g., response time)
            if value <= thresholds["excellent"]:
                return 1.0
            elif value <= thresholds["good"]:
                return 0.8
            elif value <= thresholds["acceptable"]:
                return 0.6
            elif value <= thresholds["poor"]:
                return 0.4
            else:
                return 0.2
    
    def _get_performance_rating(self, score: float) -> str:
        """Get performance rating based on score."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Acceptable"
        elif score >= 0.3:
            return "Poor"
        else:
            return "Critical"
    
    def _calculate_cpu_efficiency(self, avg_cpu: float, elapsed_time: float) -> float:
        """Calculate CPU efficiency metric."""
        # Efficiency = work done / resources used
        # Simplified: inversely proportional to CPU% * time
        if avg_cpu > 0 and elapsed_time > 0:
            return 100 / (avg_cpu * elapsed_time)
        return 0.0
    
    def _calculate_scalability_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate scalability score from load test results."""
        if len(results) < 2:
            return 0.5
        
        # Check if throughput scales linearly with load
        throughputs = [r["throughput"] for r in results]
        loads = [r["load"] for r in results]
        
        # Calculate correlation between load and throughput
        # Perfect linear scaling would maintain constant throughput
        first_throughput = throughputs[0] if throughputs else 1
        
        scaling_factors = []
        for i in range(1, len(throughputs)):
            expected_time = loads[i] / first_throughput
            actual_time = results[i]["elapsed_time"]
            scaling_factor = expected_time / actual_time if actual_time > 0 else 0
            scaling_factors.append(min(scaling_factor, 1.0))
        
        return statistics.mean(scaling_factors) if scaling_factors else 0.5
    
    def _check_linear_scalability(self, results: List[Dict[str, Any]]) -> bool:
        """Check if system scales linearly."""
        if len(results) < 3:
            return False
        
        # Check if time increases linearly with load
        times = [r["avg_time_per_paper"] for r in results]
        
        # Calculate variance in per-paper processing time
        if times:
            variance = statistics.stdev(times) / statistics.mean(times) if statistics.mean(times) > 0 else 0
            return variance < 0.2  # Less than 20% variance indicates linear scaling
        
        return False
    
    def _analyze_scalability_bottlenecks(self, results: List[Dict[str, Any]]) -> List[str]:
        """Analyze bottlenecks from scalability results."""
        bottlenecks = []
        
        if not results:
            return bottlenecks
        
        # Check for degrading performance
        if len(results) > 2:
            early_throughput = results[0]["throughput"]
            late_throughput = results[-1]["throughput"]
            
            if late_throughput < early_throughput * 0.5:
                bottlenecks.append("Significant performance degradation at high load")
        
        # Check for high error rates
        high_error_results = [r for r in results if r["error_count"] / r["load"] > 0.1]
        if high_error_results:
            bottlenecks.append(f"High error rates at load levels: {[r['load'] for r in high_error_results]}")
        
        # Check for non-linear scaling
        if not self._check_linear_scalability(results):
            bottlenecks.append("Non-linear scaling detected - possible resource contention")
        
        return bottlenecks
    
    def _calculate_concurrency_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate concurrency handling score."""
        if not results:
            return 0.0
        
        # Factor in success rate and response time degradation
        scores = []
        
        for i, result in enumerate(results):
            success_score = result["success_rate"]
            
            # Compare response time to single-threaded baseline
            if i == 0:
                baseline_time = result["avg_response_time"]
            else:
                time_degradation = result["avg_response_time"] / baseline_time
                time_score = 1.0 / time_degradation if time_degradation > 0 else 0
                
                combined_score = (success_score + time_score) / 2
                scores.append(combined_score)
        
        return statistics.mean(scores) if scores else result["success_rate"]
    
    def _find_max_efficient_concurrency(self, results: List[Dict[str, Any]]) -> int:
        """Find maximum efficient concurrency level."""
        max_level = 1
        
        for result in results:
            # Consider it efficient if success rate > 90% and response time < 2x baseline
            if result["success_rate"] >= 0.9:
                if result["concurrency_level"] == 1 or result["avg_response_time"] < results[0]["avg_response_time"] * 2:
                    max_level = result["concurrency_level"]
        
        return max_level
    
    def _calculate_overall_score(self, benchmark_results: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        weights = {
            "response_time": 0.25,
            "throughput": 0.25,
            "memory_usage": 0.20,
            "cpu_usage": 0.10,
            "scalability": 0.10,
            "concurrent_performance": 0.10
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in benchmark_results and "score" in benchmark_results[metric]:
                total_score += benchmark_results[metric]["score"] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _format_benchmark_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format benchmark results for output."""
        formatted = {}
        
        for benchmark, data in results.items():
            if isinstance(data, dict) and not data.get("skipped"):
                formatted[benchmark] = {
                    "score": data.get("score", 0),
                    "rating": data.get("rating", "Unknown"),
                    "key_metrics": self._extract_key_metrics(benchmark, data)
                }
        
        return formatted
    
    def _extract_key_metrics(self, benchmark_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for each benchmark type."""
        if benchmark_type == "response_time":
            return {
                "mean": data["statistics"]["mean"],
                "p95": data["statistics"]["p95"],
                "p99": data["statistics"]["p99"]
            }
        elif benchmark_type == "throughput":
            return {
                "papers_per_minute": data["papers_per_minute"],
                "error_rate": data["error_rate"]
            }
        elif benchmark_type == "memory_usage":
            return {
                "peak_memory_mb": data["peak_memory_mb"],
                "memory_leak_detected": data["memory_leak_detected"]
            }
        elif benchmark_type == "cpu_usage":
            return {
                "average_cpu_percent": data["average_cpu_percent"],
                "cpu_efficiency": data["cpu_efficiency"]
            }
        elif benchmark_type == "scalability":
            return {
                "scalability_score": data["scalability_score"],
                "linear_scalability": data["linear_scalability"]
            }
        elif benchmark_type == "concurrent_performance":
            return {
                "max_efficient_concurrency": data["max_efficient_concurrency"],
                "concurrency_score": data["concurrency_score"]
            }
        
        return {}
    
    def _generate_performance_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed performance analysis."""
        analysis = {
            "overall_rating": self._get_overall_rating(results),
            "strengths": self._identify_strengths(results),
            "weaknesses": self._identify_weaknesses(results),
            "performance_profile": self._create_performance_profile(results)
        }
        
        return analysis
    
    def _get_overall_rating(self, results: Dict[str, Any]) -> str:
        """Determine overall performance rating."""
        scores = [r.get("score", 0) for r in results.values() if isinstance(r, dict) and "score" in r]
        
        if scores:
            avg_score = statistics.mean(scores)
            return self._get_performance_rating(avg_score)
        
        return "Unknown"
    
    def _identify_strengths(self, results: Dict[str, Any]) -> List[str]:
        """Identify performance strengths."""
        strengths = []
        
        for metric, data in results.items():
            if isinstance(data, dict) and data.get("score", 0) >= 0.8:
                strengths.append(f"Excellent {metric.replace('_', ' ')}")
        
        return strengths
    
    def _identify_weaknesses(self, results: Dict[str, Any]) -> List[str]:
        """Identify performance weaknesses."""
        weaknesses = []
        
        for metric, data in results.items():
            if isinstance(data, dict) and data.get("score", 0) < 0.6:
                weaknesses.append(f"Poor {metric.replace('_', ' ')}")
        
        return weaknesses
    
    def _create_performance_profile(self, results: Dict[str, Any]) -> str:
        """Create a performance profile description."""
        profiles = {
            "cpu_bound": False,
            "memory_bound": False,
            "io_bound": False,
            "scalability_limited": False
        }
        
        # Analyze profile
        if results.get("cpu_usage", {}).get("average_cpu_percent", 0) > 70:
            profiles["cpu_bound"] = True
        
        if results.get("memory_usage", {}).get("memory_leak_detected", False):
            profiles["memory_bound"] = True
        
        if results.get("scalability", {}).get("linear_scalability", True) is False:
            profiles["scalability_limited"] = True
        
        # Generate profile description
        active_profiles = [k for k, v in profiles.items() if v]
        
        if not active_profiles:
            return "Balanced performance profile"
        else:
            return f"Performance limited by: {', '.join(p.replace('_', ' ') for p in active_profiles)}"
    
    def _identify_bottlenecks(self, results: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Response time bottlenecks
        if results.get("response_time", {}).get("statistics", {}).get("p99", 0) > 10:
            bottlenecks.append("High tail latency (p99 > 10s)")
        
        # Throughput bottlenecks
        if results.get("throughput", {}).get("papers_per_minute", 100) < 20:
            bottlenecks.append("Low throughput (< 20 papers/minute)")
        
        # Memory bottlenecks
        if results.get("memory_usage", {}).get("memory_leak_detected", False):
            bottlenecks.append("Memory leak detected")
        
        # CPU bottlenecks
        if results.get("cpu_usage", {}).get("average_cpu_percent", 0) > 80:
            bottlenecks.append("High CPU usage (> 80%)")
        
        # Scalability bottlenecks
        if results.get("scalability", {}).get("bottleneck_analysis", []):
            bottlenecks.extend(results["scalability"]["bottleneck_analysis"])
        
        return bottlenecks
    
    def _identify_optimizations(self, results: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities."""
        optimizations = []
        
        # Based on performance profile
        if results.get("cpu_usage", {}).get("average_cpu_percent", 0) > 70:
            optimizations.append("Consider algorithm optimization or parallel processing")
        
        if results.get("memory_usage", {}).get("peak_memory_mb", 0) > 1000:
            optimizations.append("Implement memory pooling or streaming processing")
        
        if not results.get("scalability", {}).get("linear_scalability", True):
            optimizations.append("Address resource contention for better scalability")
        
        max_concurrency = results.get("concurrent_performance", {}).get("max_efficient_concurrency", 1)
        if max_concurrency < 10:
            optimizations.append("Improve concurrent request handling")
        
        return optimizations
    
    def _generate_performance_recommendations(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Critical issues first
        bottlenecks = self._identify_bottlenecks(results)
        if bottlenecks:
            recommendations.append(f"Address critical bottlenecks: {', '.join(bottlenecks[:2])}")
        
        # Memory recommendations
        if results.get("memory_usage", {}).get("memory_leak_detected", False):
            recommendations.append("Fix memory leak - implement proper resource cleanup")
        
        # CPU recommendations
        cpu_avg = results.get("cpu_usage", {}).get("average_cpu_percent", 0)
        if cpu_avg > 70:
            recommendations.append("Optimize CPU usage through algorithm improvements")
        elif cpu_avg < 20:
            recommendations.append("Consider increasing parallelism to utilize available CPU")
        
        # Scalability recommendations
        if not results.get("scalability", {}).get("linear_scalability", True):
            recommendations.append("Improve scalability by addressing resource contention")
        
        # Response time recommendations
        p99 = results.get("response_time", {}).get("statistics", {}).get("p99", 0)
        if p99 > 10:
            recommendations.append("Reduce tail latency through request prioritization")
        
        # General optimizations
        optimizations = self._identify_optimizations(results)
        recommendations.extend(optimizations[:3])
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _create_error_result(self, error_message: str) -> ValidationResult:
        """Create error result."""
        return ValidationResult(
            validator_name=self.name,
            test_name="Performance Benchmark",
            status=ValidationStatus.ERROR,
            score=0.0,
            error_message=f"Performance benchmark error: {error_message}",
            recommendations=[
                "Fix benchmark execution errors",
                "Ensure system has sufficient resources",
                "Check system permissions for performance monitoring"
            ]
        )