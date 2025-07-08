"""
Comprehensive test runner for academic validation framework.
"""
import pytest
import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime

# Test suite configurations
TEST_SUITES = {
    "quick": {
        "description": "Quick validation tests for development",
        "markers": "not slow and not integration",
        "timeout": 300,  # 5 minutes
        "parallel": True
    },
    "academic": {
        "description": "Academic validation and quality tests",
        "markers": "academic_validation",
        "timeout": 1800,  # 30 minutes
        "parallel": True
    },
    "performance": {
        "description": "Performance and scalability tests",
        "markers": "performance or slow",
        "timeout": 3600,  # 1 hour
        "parallel": False  # Performance tests should run sequentially
    },
    "integration": {
        "description": "Database and API integration tests",
        "markers": "integration",
        "timeout": 1200,  # 20 minutes
        "parallel": True
    },
    "full": {
        "description": "Complete test suite for CI/CD",
        "markers": "",  # Run all tests
        "timeout": 7200,  # 2 hours
        "parallel": True
    }
}

# Academic validation benchmarks
ACADEMIC_BENCHMARKS = {
    "citation_accuracy": {
        "threshold": 0.95,
        "description": "Citation extraction and formatting accuracy"
    },
    "research_quality": {
        "threshold": 0.80,
        "description": "Overall research quality score"
    },
    "expert_consensus": {
        "threshold": 0.80,
        "description": "Expert reviewer consensus score"
    },
    "bias_detection": {
        "threshold": 0.85,
        "description": "Bias detection accuracy"
    },
    "coverage_completeness": {
        "threshold": 0.80,
        "description": "Research coverage completeness"
    }
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "response_time": {
        "threshold": 30.0,
        "unit": "seconds",
        "description": "Maximum response time for research generation"
    },
    "memory_usage": {
        "threshold": 2048,
        "unit": "MB",
        "description": "Maximum memory usage during processing"
    },
    "concurrent_users": {
        "threshold": 50,
        "unit": "users",
        "description": "Maximum concurrent users supported"
    },
    "success_rate": {
        "threshold": 0.95,
        "unit": "ratio",
        "description": "Minimum success rate under load"
    }
}


class AcademicTestRunner:
    """Advanced test runner for academic validation framework."""
    
    def __init__(self, output_dir: Path = Path("test_results")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = {}
        
    async def run_test_suite(self, suite_name: str, **kwargs) -> Dict[str, Any]:
        """Run a specific test suite with academic validation."""
        if suite_name not in TEST_SUITES:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = TEST_SUITES[suite_name]
        print(f"\n🧪 Running {suite_name} test suite: {suite_config['description']}")
        
        # Prepare pytest arguments
        pytest_args = self._build_pytest_args(suite_config, **kwargs)
        
        # Run tests and capture results
        start_time = time.time()
        
        try:
            # Run pytest programmatically
            exit_code = pytest.main(pytest_args)
            end_time = time.time()
            
            # Load test results
            results = self._load_test_results()
            
            # Perform academic validation
            validation_results = await self._perform_academic_validation(results)
            
            # Generate comprehensive report
            report = self._generate_test_report(
                suite_name, 
                results, 
                validation_results,
                end_time - start_time,
                exit_code
            )
            
            # Save results
            self._save_test_report(report, suite_name)
            
            return report
            
        except Exception as e:
            end_time = time.time()
            error_report = {
                "suite": suite_name,
                "status": "error",
                "error": str(e),
                "duration": end_time - start_time,
                "timestamp": datetime.now().isoformat()
            }
            self._save_test_report(error_report, f"{suite_name}_error")
            raise
    
    def _build_pytest_args(self, suite_config: Dict[str, Any], **kwargs) -> List[str]:
        """Build pytest command line arguments."""
        args = []
        
        # Base test directory
        args.extend(["tests/"])
        
        # Test markers
        if suite_config["markers"]:
            args.extend(["-m", suite_config["markers"]])
        
        # Parallel execution
        if suite_config["parallel"] and kwargs.get("parallel", True):
            worker_count = kwargs.get("workers", "auto")
            args.extend(["-n", str(worker_count)])
        
        # Output configuration
        args.extend([
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            f"--junitxml={self.output_dir}/junit_{suite_config.get('name', 'test')}.xml",
            f"--html={self.output_dir}/report_{suite_config.get('name', 'test')}.html",
            "--self-contained-html"
        ])
        
        # Coverage reporting
        if kwargs.get("coverage", True):
            args.extend([
                "--cov=knowledge_storm",
                f"--cov-report=html:{self.output_dir}/coverage_html",
                f"--cov-report=xml:{self.output_dir}/coverage.xml",
                "--cov-report=term-missing"
            ])
        
        # Performance profiling
        if "performance" in suite_config.get("markers", ""):
            args.extend([
                "--benchmark-only",
                f"--benchmark-json={self.output_dir}/benchmark.json"
            ])
        
        # Timeout configuration
        timeout = kwargs.get("timeout", suite_config.get("timeout", 300))
        args.extend(["--timeout", str(timeout)])
        
        # Additional pytest arguments
        if kwargs.get("verbose", False):
            args.append("-vv")
        
        if kwargs.get("stop_on_failure", False):
            args.append("-x")
        
        return args
    
    def _load_test_results(self) -> Dict[str, Any]:
        """Load test results from pytest output files."""
        results = {
            "junit": None,
            "coverage": None,
            "benchmark": None
        }
        
        # Load JUnit XML results
        junit_file = self.output_dir / "junit_test.xml"
        if junit_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                results["junit"] = {
                    "tests": int(root.get("tests", 0)),
                    "failures": int(root.get("failures", 0)),
                    "errors": int(root.get("errors", 0)),
                    "skipped": int(root.get("skipped", 0)),
                    "time": float(root.get("time", 0))
                }
            except Exception as e:
                print(f"Warning: Could not parse JUnit results: {e}")
        
        # Load coverage results
        coverage_file = self.output_dir / "coverage.xml"
        if coverage_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(coverage_file)
                root = tree.getroot()
                
                # Extract coverage percentage
                coverage_elem = root.find(".//coverage")
                if coverage_elem is not None:
                    results["coverage"] = {
                        "line_rate": float(coverage_elem.get("line-rate", 0)),
                        "branch_rate": float(coverage_elem.get("branch-rate", 0))
                    }
            except Exception as e:
                print(f"Warning: Could not parse coverage results: {e}")
        
        # Load benchmark results
        benchmark_file = self.output_dir / "benchmark.json"
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    results["benchmark"] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not parse benchmark results: {e}")
        
        return results
    
    async def _perform_academic_validation(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform academic validation of test results."""
        validation = {
            "academic_benchmarks": {},
            "performance_benchmarks": {},
            "overall_score": 0.0,
            "validation_status": "pending"
        }
        
        # Validate academic benchmarks
        if test_results.get("junit"):
            junit = test_results["junit"]
            
            # Calculate success rate
            total_tests = junit["tests"]
            failed_tests = junit["failures"] + junit["errors"]
            success_rate = (total_tests - failed_tests) / total_tests if total_tests > 0 else 0
            
            validation["academic_benchmarks"]["test_success_rate"] = {
                "value": success_rate,
                "threshold": 0.95,
                "passed": success_rate >= 0.95
            }
        
        # Validate coverage benchmarks
        if test_results.get("coverage"):
            coverage = test_results["coverage"]
            line_coverage = coverage["line_rate"]
            
            validation["academic_benchmarks"]["code_coverage"] = {
                "value": line_coverage,
                "threshold": 0.80,
                "passed": line_coverage >= 0.80
            }
        
        # Validate performance benchmarks
        if test_results.get("benchmark"):
            benchmark = test_results["benchmark"]
            
            # Extract performance metrics from benchmark data
            if "benchmarks" in benchmark:
                avg_times = []
                for bench in benchmark["benchmarks"]:
                    if "stats" in bench and "mean" in bench["stats"]:
                        avg_times.append(bench["stats"]["mean"])
                
                if avg_times:
                    avg_response_time = sum(avg_times) / len(avg_times)
                    validation["performance_benchmarks"]["response_time"] = {
                        "value": avg_response_time,
                        "threshold": PERFORMANCE_BENCHMARKS["response_time"]["threshold"],
                        "passed": avg_response_time <= PERFORMANCE_BENCHMARKS["response_time"]["threshold"]
                    }
        
        # Calculate overall validation score
        all_benchmarks = {}
        all_benchmarks.update(validation["academic_benchmarks"])
        all_benchmarks.update(validation["performance_benchmarks"])
        
        if all_benchmarks:
            passed_count = sum(1 for bench in all_benchmarks.values() if bench.get("passed", False))
            validation["overall_score"] = passed_count / len(all_benchmarks)
            validation["validation_status"] = "passed" if validation["overall_score"] >= 0.80 else "failed"
        
        return validation
    
    def _generate_test_report(
        self, 
        suite_name: str,
        test_results: Dict[str, Any],
        validation_results: Dict[str, Any],
        duration: float,
        exit_code: int
    ) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        report = {
            "metadata": {
                "suite": suite_name,
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "exit_code": exit_code,
                "status": "passed" if exit_code == 0 else "failed"
            },
            "test_results": test_results,
            "validation": validation_results,
            "summary": self._generate_summary(test_results, validation_results),
            "recommendations": self._generate_recommendations(validation_results)
        }
        
        return report
    
    def _generate_summary(
        self, 
        test_results: Dict[str, Any], 
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate test summary."""
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "coverage_percentage": 0.0,
            "validation_score": validation_results.get("overall_score", 0.0),
            "critical_issues": []
        }
        
        if test_results.get("junit"):
            junit = test_results["junit"]
            summary["total_tests"] = junit["tests"]
            summary["failed_tests"] = junit["failures"] + junit["errors"]
            summary["passed_tests"] = summary["total_tests"] - summary["failed_tests"]
        
        if test_results.get("coverage"):
            summary["coverage_percentage"] = test_results["coverage"]["line_rate"] * 100
        
        # Identify critical issues
        for category, benchmarks in validation_results.items():
            if isinstance(benchmarks, dict):
                for name, benchmark in benchmarks.items():
                    if isinstance(benchmark, dict) and not benchmark.get("passed", True):
                        summary["critical_issues"].append({
                            "category": category,
                            "benchmark": name,
                            "value": benchmark.get("value"),
                            "threshold": benchmark.get("threshold")
                        })
        
        return summary
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on validation results."""
        recommendations = []
        
        # Academic validation recommendations
        academic_benchmarks = validation_results.get("academic_benchmarks", {})
        
        for name, benchmark in academic_benchmarks.items():
            if not benchmark.get("passed", True):
                if name == "test_success_rate":
                    recommendations.append(
                        f"Improve test reliability - current success rate: {benchmark['value']:.2%}, "
                        f"target: {benchmark['threshold']:.2%}"
                    )
                elif name == "code_coverage":
                    recommendations.append(
                        f"Increase test coverage - current: {benchmark['value']:.2%}, "
                        f"target: {benchmark['threshold']:.2%}"
                    )
        
        # Performance recommendations
        performance_benchmarks = validation_results.get("performance_benchmarks", {})
        
        for name, benchmark in performance_benchmarks.items():
            if not benchmark.get("passed", True):
                if name == "response_time":
                    recommendations.append(
                        f"Optimize response time - current: {benchmark['value']:.2f}s, "
                        f"target: <{benchmark['threshold']}s"
                    )
        
        # Overall validation recommendations
        overall_score = validation_results.get("overall_score", 0.0)
        if overall_score < 0.80:
            recommendations.append(
                f"Overall validation score ({overall_score:.2%}) below academic standards (80%). "
                "Focus on critical failing benchmarks."
            )
        
        if not recommendations:
            recommendations.append("All validation benchmarks passed! Consider optimizing for performance.")
        
        return recommendations
    
    def _save_test_report(self, report: Dict[str, Any], suite_name: str):
        """Save test report to file."""
        report_file = self.output_dir / f"academic_validation_report_{suite_name}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 Test report saved to: {report_file}")
        
        # Also save a human-readable summary
        summary_file = self.output_dir / f"summary_{suite_name}.txt"
        self._save_summary_text(report, summary_file)
    
    def _save_summary_text(self, report: Dict[str, Any], summary_file: Path):
        """Save human-readable summary."""
        with open(summary_file, 'w') as f:
            f.write("🧪 ACADEMIC VALIDATION TEST REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            metadata = report["metadata"]
            f.write(f"Suite: {metadata['suite']}\n")
            f.write(f"Timestamp: {metadata['timestamp']}\n")
            f.write(f"Duration: {metadata['duration']:.2f} seconds\n")
            f.write(f"Status: {metadata['status'].upper()}\n\n")
            
            # Summary
            summary = report["summary"]
            f.write("📋 SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Passed: {summary['passed_tests']}\n")
            f.write(f"Failed: {summary['failed_tests']}\n")
            f.write(f"Coverage: {summary['coverage_percentage']:.1f}%\n")
            f.write(f"Validation Score: {summary['validation_score']:.2%}\n\n")
            
            # Critical Issues
            if summary["critical_issues"]:
                f.write("⚠️  CRITICAL ISSUES\n")
                f.write("-" * 20 + "\n")
                for issue in summary["critical_issues"]:
                    f.write(f"• {issue['category']}.{issue['benchmark']}: ")
                    f.write(f"{issue['value']} (threshold: {issue['threshold']})\n")
                f.write("\n")
            
            # Recommendations
            f.write("💡 RECOMMENDATIONS\n")
            f.write("-" * 20 + "\n")
            for rec in report["recommendations"]:
                f.write(f"• {rec}\n")
        
        print(f"📝 Summary saved to: {summary_file}")


async def main():
    """Main entry point for academic test runner."""
    parser = argparse.ArgumentParser(description="Academic Validation Test Runner")
    parser.add_argument(
        "suite", 
        choices=list(TEST_SUITES.keys()),
        help="Test suite to run"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("test_results"), help="Output directory")
    parser.add_argument("--workers", default="auto", help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, help="Test timeout in seconds")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = AcademicTestRunner(args.output_dir)
    
    # Run test suite
    try:
        report = await runner.run_test_suite(
            args.suite,
            workers=args.workers,
            timeout=args.timeout,
            coverage=not args.no_coverage,
            verbose=args.verbose,
            stop_on_failure=args.stop_on_failure
        )
        
        # Print final status
        status = report["metadata"]["status"]
        validation_score = report["validation"]["overall_score"]
        
        if status == "passed" and validation_score >= 0.80:
            print(f"\n✅ Academic validation PASSED (Score: {validation_score:.2%})")
            sys.exit(0)
        else:
            print(f"\n❌ Academic validation FAILED (Score: {validation_score:.2%})")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())