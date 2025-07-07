"""
Performance Benchmark Suite for academic validation framework.

Comprehensive performance testing including response time, memory usage, 
throughput, and concurrent user load testing.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .base import BaseBenchmarkSuite, BenchmarkContext, BenchmarkMetrics, PerformanceProfiler
from ..core import ValidationResult


class PerformanceBenchmarkSuite(BaseBenchmarkSuite):
    """
    Comprehensive performance benchmarking for academic research systems.
    
    Tests response time, memory efficiency, throughput, and scalability
    under various load conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Performance_Benchmark_Suite",
            description="Comprehensive performance benchmarking for academic systems",
            version="1.0.0",
            config=config or {}
        )
        
        # Performance thresholds
        self.performance_thresholds = {
            "max_response_time_seconds": 30.0,
            "max_memory_usage_mb": 2048.0,
            "min_throughput_papers_per_minute": 60.0,
            "max_concurrent_users": 50,
            "min_success_rate": 0.95,
            "max_error_rate": 0.05,
            "p95_response_time": 25.0,
            "p99_response_time": 45.0,
        }
        
        # Load test scenarios
        self.load_scenarios = [
            {"name": "light_load", "concurrent_users": 1, "papers_per_user": 10},
            {"name": "moderate_load", "concurrent_users": 5, "papers_per_user": 50},
            {"name": "heavy_load", "concurrent_users": 10, "papers_per_user": 100},
            {"name": "stress_load", "concurrent_users": 25, "papers_per_user": 200},
            {"name": "peak_load", "concurrent_users": 50, "papers_per_user": 500},
        ]
        
        # Performance test types
        self.test_types = [
            "response_time",
            "memory_usage", 
            "throughput",
            "concurrent_load",
            "stress_testing",
            "endurance_testing"
        ]
    
    async def _initialize_benchmark_suite(self) -> None:
        """Initialize performance benchmark suite."""
        # Override thresholds from config if provided
        if "performance_thresholds" in self.config:
            self.performance_thresholds.update(self.config["performance_thresholds"])
        
        if "load_scenarios" in self.config:
            self.load_scenarios = self.config["load_scenarios"]
    
    async def run_benchmarks(
        self,
        research_output: Any,
        context: Optional[BenchmarkContext] = None,
        **kwargs: Any
    ) -> List[ValidationResult]:
        """Run comprehensive performance benchmarks."""
        
        results = []
        
        # Response time benchmarks
        response_time_result = await self._benchmark_response_time(research_output, context)
        results.append(response_time_result)
        
        # Memory usage benchmarks
        memory_result = await self._benchmark_memory_usage(research_output, context)
        results.append(memory_result)
        
        # Throughput benchmarks
        throughput_result = await self._benchmark_throughput(research_output, context)
        results.append(throughput_result)
        
        # Concurrent load benchmarks
        concurrent_result = await self._benchmark_concurrent_load(research_output, context)
        results.append(concurrent_result)
        
        # Stress testing
        stress_result = await self._benchmark_stress_testing(research_output, context)
        results.append(stress_result)
        
        # Endurance testing
        endurance_result = await self._benchmark_endurance(research_output, context)
        results.append(endurance_result)
        
        return results
    
    async def _benchmark_response_time(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark response time performance."""
        
        response_times = []
        successful_requests = 0
        total_requests = 10  # Number of test requests
        
        for i in range(total_requests):
            start_time = time.time()
            
            try:
                # Simulate processing research output
                await self._simulate_research_processing(research_output)
                response_time = time.time() - start_time
                response_times.append(response_time)
                successful_requests += 1
                
            except Exception as e:
                # Record failed request time
                response_times.append(time.time() - start_time)
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        max_response_time = max(response_times) if response_times else 0.0
        min_response_time = min(response_times) if response_times else 0.0
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p95_time = sorted_times[int(0.95 * len(sorted_times))] if sorted_times else 0.0
        p99_time = sorted_times[int(0.99 * len(sorted_times))] if sorted_times else 0.0
        
        success_rate = successful_requests / total_requests
        
        # Evaluate performance
        meets_avg_threshold = avg_response_time <= self.performance_thresholds["max_response_time_seconds"]
        meets_p95_threshold = p95_time <= self.performance_thresholds["p95_response_time"]
        meets_p99_threshold = p99_time <= self.performance_thresholds["p99_response_time"]
        meets_success_threshold = success_rate >= self.performance_thresholds["min_success_rate"]
        
        overall_pass = all([
            meets_avg_threshold, meets_p95_threshold, 
            meets_p99_threshold, meets_success_threshold
        ])
        
        # Calculate performance score
        time_score = min(self.performance_thresholds["max_response_time_seconds"] / max(avg_response_time, 0.1), 1.0)
        success_score = success_rate
        performance_score = (time_score + success_score) / 2
        
        status = "passed" if overall_pass else "failed"
        
        metrics = BenchmarkMetrics(
            execution_time=sum(response_times),
            throughput=total_requests / sum(response_times) if sum(response_times) > 0 else 0,
            success_rate=success_rate,
            error_rate=1.0 - success_rate,
            custom_metrics={
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_time,
                "p99_response_time": p99_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time
            }
        )
        
        return self._create_result(
            test_name="response_time_benchmark",
            status=status,
            score=performance_score,
            details={
                "response_time_stats": {
                    "average": avg_response_time,
                    "maximum": max_response_time,
                    "minimum": min_response_time,
                    "p95": p95_time,
                    "p99": p99_time
                },
                "thresholds": {
                    "max_avg_time": self.performance_thresholds["max_response_time_seconds"],
                    "max_p95_time": self.performance_thresholds["p95_response_time"],
                    "max_p99_time": self.performance_thresholds["p99_response_time"]
                },
                "threshold_compliance": {
                    "avg_time": meets_avg_threshold,
                    "p95_time": meets_p95_threshold,
                    "p99_time": meets_p99_threshold,
                    "success_rate": meets_success_threshold
                },
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate
            },
            metadata={
                "benchmark_type": "response_time",
                "test_duration": sum(response_times)
            },
            metrics=metrics
        )
    
    async def _benchmark_memory_usage(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark memory usage efficiency."""
        
        profiler = PerformanceProfiler()
        await profiler.start_profiling(sample_interval=0.05)
        
        try:
            # Process multiple research outputs to test memory scaling
            memory_samples = []
            
            for i in range(5):  # Process 5 iterations
                start_memory = self._get_memory_usage()
                
                # Simulate memory-intensive research processing
                await self._simulate_memory_intensive_processing(research_output)
                
                end_memory = self._get_memory_usage()
                if start_memory and end_memory:
                    memory_delta = end_memory - start_memory
                    memory_samples.append({
                        "iteration": i + 1,
                        "start_memory": start_memory,
                        "end_memory": end_memory,
                        "memory_delta": memory_delta
                    })
            
            final_metrics = await profiler.stop_profiling()
            
            # Analyze memory usage
            if memory_samples:
                max_memory_delta = max(sample["memory_delta"] for sample in memory_samples)
                avg_memory_delta = sum(sample["memory_delta"] for sample in memory_samples) / len(memory_samples)
                total_memory_used = sum(sample["memory_delta"] for sample in memory_samples)
            else:
                max_memory_delta = 0.0
                avg_memory_delta = 0.0
                total_memory_used = 0.0
            
            # Evaluate memory efficiency
            meets_memory_threshold = max_memory_delta <= self.performance_thresholds["max_memory_usage_mb"]
            memory_efficiency = min(
                self.performance_thresholds["max_memory_usage_mb"] / max(max_memory_delta, 1.0), 
                1.0
            )
            
            status = "passed" if meets_memory_threshold else "failed"
            
            final_metrics.custom_metrics.update({
                "max_memory_delta": max_memory_delta,
                "avg_memory_delta": avg_memory_delta,
                "total_memory_used": total_memory_used,
                "memory_samples": memory_samples
            })
            
            return self._create_result(
                test_name="memory_usage_benchmark",
                status=status,
                score=memory_efficiency,
                details={
                    "memory_statistics": {
                        "max_memory_delta_mb": max_memory_delta,
                        "avg_memory_delta_mb": avg_memory_delta,
                        "total_memory_used_mb": total_memory_used,
                        "iterations_tested": len(memory_samples)
                    },
                    "threshold": self.performance_thresholds["max_memory_usage_mb"],
                    "threshold_met": meets_memory_threshold,
                    "memory_efficiency_score": memory_efficiency,
                    "memory_samples": memory_samples
                },
                metadata={
                    "benchmark_type": "memory_usage",
                    "profiling_enabled": True
                },
                metrics=final_metrics
            )
            
        except Exception as e:
            await profiler.stop_profiling()
            return self._create_result(
                test_name="memory_usage_benchmark", 
                status="failed",
                details={"error": str(e)}
            )
    
    async def _benchmark_throughput(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark processing throughput."""
        
        test_duration = 60.0  # 1 minute test
        papers_processed = 0
        processing_times = []
        
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            paper_start = time.time()
            
            try:
                await self._simulate_research_processing(research_output)
                papers_processed += 1
                processing_times.append(time.time() - paper_start)
                
            except Exception:
                # Count failed processing
                processing_times.append(time.time() - paper_start)
        
        total_time = time.time() - start_time
        
        # Calculate throughput metrics
        papers_per_second = papers_processed / total_time if total_time > 0 else 0
        papers_per_minute = papers_per_second * 60
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Evaluate throughput
        meets_throughput_threshold = papers_per_minute >= self.performance_thresholds["min_throughput_papers_per_minute"]
        throughput_score = min(
            papers_per_minute / self.performance_thresholds["min_throughput_papers_per_minute"],
            1.0
        )
        
        status = "passed" if meets_throughput_threshold else "failed"
        
        metrics = BenchmarkMetrics(
            execution_time=total_time,
            throughput=papers_per_second,
            success_rate=1.0,  # Assuming all completed processing attempts were successful
            custom_metrics={
                "papers_processed": papers_processed,
                "papers_per_minute": papers_per_minute,
                "avg_processing_time": avg_processing_time
            }
        )
        
        return self._create_result(
            test_name="throughput_benchmark",
            status=status,
            score=throughput_score,
            details={
                "throughput_metrics": {
                    "papers_processed": papers_processed,
                    "papers_per_second": papers_per_second,
                    "papers_per_minute": papers_per_minute,
                    "avg_processing_time_seconds": avg_processing_time,
                    "test_duration_seconds": total_time
                },
                "threshold": self.performance_thresholds["min_throughput_papers_per_minute"],
                "threshold_met": meets_throughput_threshold,
                "throughput_score": throughput_score
            },
            metadata={
                "benchmark_type": "throughput",
                "test_duration": test_duration
            },
            metrics=metrics
        )
    
    async def _benchmark_concurrent_load(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark performance under concurrent load."""
        
        load_results = []
        
        for scenario in self.load_scenarios:
            scenario_result = await self._run_load_scenario(research_output, scenario)
            load_results.append(scenario_result)
        
        # Analyze overall concurrent load performance
        total_users_tested = sum(scenario["concurrent_users"] for scenario in self.load_scenarios)
        successful_scenarios = sum(1 for result in load_results if result["success"])
        avg_response_time = sum(result["avg_response_time"] for result in load_results) / len(load_results)
        
        # Find maximum successful concurrent users
        max_successful_users = 0
        for scenario, result in zip(self.load_scenarios, load_results):
            if result["success"]:
                max_successful_users = max(max_successful_users, scenario["concurrent_users"])
        
        # Evaluate concurrent load performance
        meets_concurrency_threshold = max_successful_users >= self.performance_thresholds["max_concurrent_users"]
        concurrency_score = min(
            max_successful_users / self.performance_thresholds["max_concurrent_users"],
            1.0
        )
        
        status = "passed" if meets_concurrency_threshold else "failed"
        
        return self._create_result(
            test_name="concurrent_load_benchmark",
            status=status,
            score=concurrency_score,
            details={
                "load_test_results": load_results,
                "overall_metrics": {
                    "total_scenarios_tested": len(self.load_scenarios),
                    "successful_scenarios": successful_scenarios,
                    "max_successful_concurrent_users": max_successful_users,
                    "avg_response_time_all_scenarios": avg_response_time
                },
                "threshold": self.performance_thresholds["max_concurrent_users"],
                "threshold_met": meets_concurrency_threshold,
                "concurrency_score": concurrency_score
            },
            metadata={
                "benchmark_type": "concurrent_load",
                "scenarios_tested": len(self.load_scenarios)
            }
        )
    
    async def _benchmark_stress_testing(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark system behavior under stress conditions."""
        
        # Gradually increase load until system fails or reaches maximum
        max_users = 100
        user_increment = 5
        stress_results = []
        
        for concurrent_users in range(user_increment, max_users + 1, user_increment):
            scenario = {
                "name": f"stress_{concurrent_users}_users",
                "concurrent_users": concurrent_users,
                "papers_per_user": 20
            }
            
            result = await self._run_load_scenario(research_output, scenario)
            stress_results.append({
                "concurrent_users": concurrent_users,
                "result": result
            })
            
            # Stop if system starts failing significantly
            if not result["success"] or result["error_rate"] > 0.1:
                break
        
        # Analyze stress test results
        breaking_point = None
        max_stable_users = 0
        
        for stress_result in stress_results:
            if stress_result["result"]["success"] and stress_result["result"]["error_rate"] <= 0.05:
                max_stable_users = stress_result["concurrent_users"]
            else:
                breaking_point = stress_result["concurrent_users"]
                break
        
        # Evaluate stress resistance
        stress_score = min(max_stable_users / 50.0, 1.0)  # Normalize against 50 users
        
        status = "passed" if max_stable_users >= 25 else "failed"  # Require at least 25 stable users
        
        return self._create_result(
            test_name="stress_testing_benchmark",
            status=status,
            score=stress_score,
            details={
                "stress_test_results": stress_results,
                "max_stable_concurrent_users": max_stable_users,
                "breaking_point_users": breaking_point,
                "stress_resistance_score": stress_score,
                "users_tested_range": f"{user_increment}-{min(max_users, breaking_point or max_users)}"
            },
            metadata={
                "benchmark_type": "stress_testing",
                "max_users_attempted": max_users,
                "user_increment": user_increment
            }
        )
    
    async def _benchmark_endurance(
        self, 
        research_output: Any, 
        context: Optional[BenchmarkContext] = None
    ) -> ValidationResult:
        """Benchmark system endurance over extended periods."""
        
        # Run moderate load for extended period
        test_duration = 300.0  # 5 minutes
        concurrent_users = 5
        check_interval = 30.0  # Check every 30 seconds
        
        endurance_samples = []
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            sample_start = time.time()
            
            # Run short load test
            scenario = {
                "name": "endurance_sample",
                "concurrent_users": concurrent_users,
                "papers_per_user": 10
            }
            
            result = await self._run_load_scenario(research_output, scenario)
            
            sample_time = time.time() - sample_start
            endurance_samples.append({
                "timestamp": time.time() - start_time,
                "duration": sample_time,
                "result": result,
                "memory_usage": self._get_memory_usage()
            })
            
            # Wait until next check interval
            elapsed = time.time() - start_time
            next_check = ((len(endurance_samples)) * check_interval)
            if next_check > elapsed:
                await asyncio.sleep(next_check - elapsed)
        
        # Analyze endurance performance
        successful_samples = sum(1 for sample in endurance_samples if sample["result"]["success"])
        avg_response_time = sum(
            sample["result"]["avg_response_time"] for sample in endurance_samples
        ) / len(endurance_samples)
        
        # Check for performance degradation
        early_samples = endurance_samples[:len(endurance_samples)//3]
        late_samples = endurance_samples[-len(endurance_samples)//3:]
        
        early_avg_time = sum(s["result"]["avg_response_time"] for s in early_samples) / len(early_samples)
        late_avg_time = sum(s["result"]["avg_response_time"] for s in late_samples) / len(late_samples)
        
        performance_degradation = (late_avg_time - early_avg_time) / early_avg_time if early_avg_time > 0 else 0
        
        # Evaluate endurance
        success_rate = successful_samples / len(endurance_samples)
        endurance_score = success_rate * max(1.0 - performance_degradation, 0.0)
        
        status = "passed" if success_rate >= 0.95 and performance_degradation <= 0.2 else "failed"
        
        return self._create_result(
            test_name="endurance_benchmark",
            status=status,
            score=endurance_score,
            details={
                "endurance_metrics": {
                    "test_duration_seconds": test_duration,
                    "total_samples": len(endurance_samples),
                    "successful_samples": successful_samples,
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "performance_degradation": performance_degradation
                },
                "performance_analysis": {
                    "early_avg_response_time": early_avg_time,
                    "late_avg_response_time": late_avg_time,
                    "degradation_percentage": performance_degradation * 100
                },
                "endurance_samples": endurance_samples[-10:],  # Last 10 samples
                "endurance_score": endurance_score
            },
            metadata={
                "benchmark_type": "endurance",
                "test_duration": test_duration,
                "check_interval": check_interval
            }
        )
    
    async def _run_load_scenario(
        self, 
        research_output: Any, 
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a specific load testing scenario."""
        
        concurrent_users = scenario["concurrent_users"]
        papers_per_user = scenario["papers_per_user"]
        
        # Create tasks for concurrent users
        user_tasks = []
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_user_load(research_output, papers_per_user, user_id)
            )
            user_tasks.append(task)
        
        # Wait for all users to complete
        start_time = time.time()
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_users = 0
        total_papers_processed = 0
        total_response_time = 0.0
        total_errors = 0
        
        for result in user_results:
            if not isinstance(result, Exception) and result:
                if result["success"]:
                    successful_users += 1
                total_papers_processed += result["papers_processed"]
                total_response_time += result["total_time"]
                total_errors += result["errors"]
        
        # Calculate metrics
        success_rate = successful_users / concurrent_users if concurrent_users > 0 else 0
        error_rate = total_errors / total_papers_processed if total_papers_processed > 0 else 0
        avg_response_time = total_response_time / concurrent_users if concurrent_users > 0 else 0
        throughput = total_papers_processed / total_time if total_time > 0 else 0
        
        # Determine if scenario was successful
        scenario_success = (
            success_rate >= 0.9 and 
            error_rate <= 0.1 and 
            avg_response_time <= self.performance_thresholds["max_response_time_seconds"]
        )
        
        return {
            "scenario_name": scenario["name"],
            "concurrent_users": concurrent_users,
            "papers_per_user": papers_per_user,
            "success": scenario_success,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "throughput": throughput,
            "total_papers_processed": total_papers_processed,
            "total_time": total_time
        }
    
    async def _simulate_user_load(
        self, 
        research_output: Any, 
        papers_to_process: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """Simulate load from a single user."""
        
        start_time = time.time()
        papers_processed = 0
        errors = 0
        
        for paper_idx in range(papers_to_process):
            try:
                await self._simulate_research_processing(research_output)
                papers_processed += 1
                
                # Small delay between requests to simulate human behavior
                await asyncio.sleep(0.1)
                
            except Exception:
                errors += 1
        
        total_time = time.time() - start_time
        success = errors / papers_to_process <= 0.1 if papers_to_process > 0 else True
        
        return {
            "user_id": user_id,
            "success": success,
            "papers_processed": papers_processed,
            "errors": errors,
            "total_time": total_time
        }
    
    async def _simulate_research_processing(self, research_output: Any) -> None:
        """Simulate research processing work."""
        # Simulate CPU-intensive work
        await asyncio.sleep(0.1)  # Base processing time
        
        # Simulate some computational work
        text_content = str(research_output)
        hash_value = hash(text_content)
        
        # Simulate variable processing time based on content
        processing_factor = (abs(hash_value) % 100) / 1000.0  # 0-0.1 seconds
        await asyncio.sleep(processing_factor)
    
    async def _simulate_memory_intensive_processing(self, research_output: Any) -> None:
        """Simulate memory-intensive research processing."""
        # Create temporary data structures to test memory usage
        large_data = []
        
        # Simulate processing that uses memory
        text_content = str(research_output)
        for i in range(1000):  # Create some memory load
            large_data.append(f"{text_content}_{i}" * 10)
        
        # Simulate work on the data
        await asyncio.sleep(0.05)
        
        # Clean up
        del large_data