"""
Comprehensive Test Runner for Academic Validation Framework

This module provides a high-level interface to run all academic validation tests
including PRISMA compliance, citation accuracy, performance benchmarks, database
integration tests, and credibility assessments.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import AcademicValidationFramework
from .models import ValidationSession
from .config import FrameworkConfig
from .validators import (
    PRISMAValidator,
    CitationAccuracyValidator,
)
from .benchmarks import (
    PerformanceBenchmarkSuite,
)
from .database_integrations import (
    BaseDatabaseIntegrationTester,
)
from .credibility import (
    BaseCredibilityAssessment,
)
from .reporting import (
    BaseReportGenerator,
)


logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """
    Comprehensive test runner for academic validation framework.
    
    Orchestrates all types of validation tests and generates comprehensive reports.
    """
    
    def __init__(
        self,
        config: Optional[FrameworkConfig] = None,
        enable_all_tests: bool = True,
        custom_validators: Optional[List] = None,
        custom_benchmarks: Optional[List] = None,
        custom_database_testers: Optional[List] = None,
        custom_credibility_assessors: Optional[List] = None,
    ):
        self.config = config or FrameworkConfig()
        self.enable_all_tests = enable_all_tests
        
        # Initialize framework
        self.framework = AcademicValidationFramework(config=self.config)
        
        # Setup default components
        self._setup_validators(custom_validators)
        self._setup_benchmarks(custom_benchmarks)
        self._setup_database_testers(custom_database_testers)
        self._setup_credibility_assessors(custom_credibility_assessors)
        self._setup_report_generators()
    
    def _setup_validators(self, custom_validators: Optional[List] = None) -> None:
        """Setup validation components."""
        if self.enable_all_tests:
            # Core academic validators
            self.framework.register_validator(PRISMAValidator())
            self.framework.register_validator(CitationAccuracyValidator())
        
        # Add custom validators
        if custom_validators:
            for validator in custom_validators:
                self.framework.register_validator(validator)
    
    def _setup_benchmarks(self, custom_benchmarks: Optional[List] = None) -> None:
        """Setup benchmark suites."""
        if self.enable_all_tests:
            # Core benchmark suites
            self.framework.register_benchmark_suite(PerformanceBenchmarkSuite())
        
        # Add custom benchmarks
        if custom_benchmarks:
            for benchmark in custom_benchmarks:
                self.framework.register_benchmark_suite(benchmark)
    
    def _setup_database_testers(self, custom_testers: Optional[List] = None) -> None:
        """Setup database integration testers."""
        # For now, skip default database testers until they're implemented
        # Add custom testers
        if custom_testers:
            for tester in custom_testers:
                self.framework.register_database_tester(tester)
    
    def _setup_credibility_assessors(self, custom_assessors: Optional[List] = None) -> None:
        """Setup credibility assessors."""
        # For now, skip default credibility assessors until they're implemented
        # Add custom assessors
        if custom_assessors:
            for assessor in custom_assessors:
                self.framework.register_credibility_assessor(assessor)
    
    def _setup_report_generators(self) -> None:
        """Setup report generators."""
        # For now, skip default report generators until they're implemented
        pass
    
    async def run_comprehensive_validation(
        self,
        research_output: Any,
        session_id: Optional[str] = None,
        test_categories: Optional[List[str]] = None,
        discipline: Optional[str] = None,
        citation_style: Optional[str] = None,
        methodology: Optional[str] = None,
        **kwargs: Any
    ) -> ValidationSession:
        """
        Run comprehensive academic validation on research output.
        
        Args:
            research_output: The research output to validate
            session_id: Optional session identifier
            test_categories: Categories to test (validation, benchmarks, database_integration, credibility)
            discipline: Academic discipline for context
            citation_style: Citation style for validation
            methodology: Research methodology for validation
            **kwargs: Additional parameters
            
        Returns:
            Complete validation session with results
        """
        
        # Prepare session metadata
        session_metadata = {
            "discipline": discipline,
            "citation_style": citation_style,
            "methodology": methodology,
            "test_categories": test_categories or ["all"],
            "framework_version": "1.0.0",
            **kwargs
        }
        
        logger.info(f"Starting comprehensive validation for discipline: {discipline}")
        
        # Run comprehensive validation
        session = await self.framework.run_comprehensive_validation(
            research_output=research_output,
            test_categories=test_categories,
            session_metadata=session_metadata
        )
        
        logger.info(
            f"Validation completed. Session: {session.session_id}, "
            f"Success rate: {session.success_rate:.1%}, "
            f"Duration: {session.duration:.2f}s"
        )
        
        return session
    
    async def run_prisma_validation_only(
        self,
        research_output: Any,
        **kwargs: Any
    ) -> ValidationSession:
        """Run only PRISMA systematic review validation."""
        session = await self.framework.start_validation_session(
            metadata={"test_type": "prisma_only", **kwargs}
        )
        
        # Run only PRISMA validator
        prisma_validator = PRISMAValidator()
        await prisma_validator.initialize()
        
        prisma_results = await prisma_validator.validate(research_output)
        if isinstance(prisma_results, list):
            session.results.extend(prisma_results)
        else:
            session.results.append(prisma_results)
        
        await self.framework.end_validation_session()
        return session
    
    async def run_citation_validation_only(
        self,
        research_output: Any,
        citation_style: Optional[str] = None,
        **kwargs: Any
    ) -> ValidationSession:
        """Run only citation accuracy validation."""
        session = await self.framework.start_validation_session(
            metadata={
                "test_type": "citation_only", 
                "citation_style": citation_style,
                **kwargs
            }
        )
        
        # Run only citation validator
        from .validators.base import ValidationContext
        citation_validator = CitationAccuracyValidator()
        await citation_validator.initialize()
        
        context = ValidationContext(
            research_output=research_output,
            citation_style=citation_style
        )
        
        citation_results = await citation_validator.validate(research_output, context)
        if isinstance(citation_results, list):
            session.results.extend(citation_results)
        else:
            session.results.append(citation_results)
        
        await self.framework.end_validation_session()
        return session
    
    async def run_performance_benchmarks_only(
        self,
        research_output: Any,
        **kwargs: Any
    ) -> ValidationSession:
        """Run only performance benchmarks."""
        session = await self.framework.start_validation_session(
            metadata={"test_type": "performance_only", **kwargs}
        )
        
        # Run only performance benchmark
        performance_benchmark = PerformanceBenchmarkSuite()
        await performance_benchmark.initialize()
        
        benchmark_results = await performance_benchmark.run_benchmarks(research_output)
        if isinstance(benchmark_results, list):
            session.results.extend(benchmark_results)
        else:
            session.results.append(benchmark_results)
        
        await self.framework.end_validation_session()
        return session
    
    async def run_database_integration_tests_only(
        self,
        research_output: Any,
        **kwargs: Any
    ) -> ValidationSession:
        """Run only database integration tests."""
        session = await self.framework.start_validation_session(
            metadata={"test_type": "database_integration_only", **kwargs}
        )
        
        # Run database integration tests
        for tester in self.framework.database_testers:
            try:
                integration_results = await tester.test_integration(research_output)
                if isinstance(integration_results, list):
                    session.results.extend(integration_results)
                else:
                    session.results.append(integration_results)
            except Exception as e:
                logger.error(f"Database tester {tester.name} failed: {e}")
        
        await self.framework.end_validation_session()
        return session
    
    async def run_cross_disciplinary_validation(
        self,
        research_output: Any,
        disciplines: List[str],
        **kwargs: Any
    ) -> Dict[str, ValidationSession]:
        """
        Run validation across multiple disciplines.
        
        Args:
            research_output: The research output to validate
            disciplines: List of disciplines to test against
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping discipline to validation session
        """
        results = {}
        
        for discipline in disciplines:
            logger.info(f"Running validation for discipline: {discipline}")
            
            session = await self.run_comprehensive_validation(
                research_output=research_output,
                discipline=discipline,
                session_id=f"{discipline.lower().replace(' ', '_')}_validation",
                **kwargs
            )
            
            results[discipline] = session
        
        return results
    
    def get_validation_summary(
        self, 
        sessions: List[ValidationSession]
    ) -> Dict[str, Any]:
        """Get summary across multiple validation sessions."""
        if not sessions:
            return {}
        
        total_tests = sum(s.total_count for s in sessions)
        total_passed = sum(s.passed_count for s in sessions)
        total_failed = sum(s.failed_count for s in sessions)
        
        avg_success_rate = sum(s.success_rate for s in sessions) / len(sessions)
        avg_duration = sum(s.duration for s in sessions if s.duration) / len([s for s in sessions if s.duration])
        
        return {
            "total_sessions": len(sessions),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0.0,
            "average_success_rate": avg_success_rate,
            "average_duration": avg_duration,
            "session_summaries": [
                {
                    "session_id": s.session_id,
                    "success_rate": s.success_rate,
                    "duration": s.duration,
                    "total_tests": s.total_count
                }
                for s in sessions
            ]
        }
    
    async def generate_comprehensive_reports(
        self, 
        session: ValidationSession,
        output_dir: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Generate comprehensive reports for a validation session.
        
        Returns:
            Dictionary mapping report type to list of generated file paths
        """
        if output_dir:
            # Update output directory for all report generators
            for generator in self.framework.report_generators:
                generator.output_dir = Path(output_dir)
        
        report_files = {}
        
        for generator in self.framework.report_generators:
            try:
                files = await generator.generate_report(session)
                report_files[generator.name] = list(files.values())
            except Exception as e:
                logger.error(f"Report generator {generator.name} failed: {e}")
                report_files[generator.name] = []
        
        return report_files
    
    async def cleanup(self) -> None:
        """Cleanup all framework resources."""
        await self.framework.cleanup()
    
    def get_framework_info(self) -> Dict[str, Any]:
        """Get comprehensive framework information."""
        return {
            "framework_stats": self.framework.get_framework_statistics(),
            "config": self.config.to_dict(),
            "registered_components": {
                "validators": len(self.framework.validators),
                "benchmarks": len(self.framework.benchmarks),
                "database_testers": len(self.framework.database_testers),
                "credibility_assessors": len(self.framework.credibility_assessors),
                "report_generators": len(self.framework.report_generators),
            },
            "component_details": {
                "validators": [v.get_validator_info() for v in self.framework.validators],
                "benchmarks": [b.get_benchmark_info() for b in self.framework.benchmarks],
                "database_testers": [t.get_tester_info() for t in self.framework.database_testers],
                "credibility_assessors": [a.get_assessment_info() for a in self.framework.credibility_assessors],
                "report_generators": [g.name for g in self.framework.report_generators],
            }
        }


# Convenience functions for common use cases

async def validate_systematic_review(
    research_output: Any,
    discipline: Optional[str] = None,
    **kwargs: Any
) -> ValidationSession:
    """Convenience function for systematic review validation."""
    runner = ComprehensiveTestRunner()
    try:
        return await runner.run_comprehensive_validation(
            research_output=research_output,
            discipline=discipline,
            methodology="Systematic Review",
            test_categories=["validation"],
            **kwargs
        )
    finally:
        await runner.cleanup()


async def validate_research_paper(
    research_output: Any,
    discipline: Optional[str] = None,
    citation_style: Optional[str] = None,
    **kwargs: Any
) -> ValidationSession:
    """Convenience function for general research paper validation."""
    runner = ComprehensiveTestRunner()
    try:
        return await runner.run_comprehensive_validation(
            research_output=research_output,
            discipline=discipline,
            citation_style=citation_style,
            **kwargs
        )
    finally:
        await runner.cleanup()


async def benchmark_system_performance(
    research_output: Any,
    **kwargs: Any
) -> ValidationSession:
    """Convenience function for performance benchmarking."""
    runner = ComprehensiveTestRunner()
    try:
        return await runner.run_performance_benchmarks_only(
            research_output=research_output,
            **kwargs
        )
    finally:
        await runner.cleanup()


async def test_database_integrations(
    research_output: Any,
    **kwargs: Any
) -> ValidationSession:
    """Convenience function for database integration testing."""
    runner = ComprehensiveTestRunner()
    try:
        return await runner.run_database_integration_tests_only(
            research_output=research_output,
            **kwargs
        )
    finally:
        await runner.cleanup()