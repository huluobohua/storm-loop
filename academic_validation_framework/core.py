"""
Core Academic Validation Framework

Central orchestrator for comprehensive academic validation testing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import FrameworkConfig
from .models import ValidationResult, ValidationSession
from .interfaces import (
    ValidatorProtocol,
    BenchmarkProtocol,
    DatabaseIntegrationProtocol,
    CredibilityAssessorProtocol,
    ReportGeneratorProtocol
)


logger = logging.getLogger(__name__)


class AcademicValidationFramework:
    """
    Comprehensive Academic Validation Framework.
    
    Orchestrates all validation components including validators, benchmarks,
    database integrations, credibility assessments, and reporting.
    """
    
    def __init__(self, config: Optional[FrameworkConfig] = None):
        self.config = config or FrameworkConfig()
        
        # Get components from config
        self.validators = self.config.validators
        self.benchmarks = self.config.benchmarks
        self.database_testers = self.config.database_testers
        self.credibility_assessors = self.config.credibility_assessors
        self.report_generators = self.config.report_generators
        
        self.sessions: List[ValidationSession] = []
        self.current_session: Optional[ValidationSession] = None
        
        # Logging should be configured at application level, not here
        self._logging_configured = False
    
    def configure_logging(self) -> None:
        """Configure framework logging. Should be called once at application startup."""
        if self._logging_configured:
            logger.warning("Logging already configured, skipping reconfiguration")
            return
            
        log_level = getattr(logging, self.config.log_level.upper())
        
        # Get framework logger specifically, not root logger
        framework_logger = logging.getLogger('academic_validation_framework')
        framework_logger.setLevel(log_level)
        
        # Clear any existing handlers
        framework_logger.handlers.clear()
        
        # Add handlers based on config
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            framework_logger.addHandler(file_handler)
            
        if self.config.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            framework_logger.addHandler(console_handler)
            
        self._logging_configured = True
        logger.info("Logging configured successfully")
    
    def register_validator(self, validator: ValidatorProtocol) -> None:
        """Register a new validator."""
        self.validators.append(validator)
        logger.info(f"Registered validator: {validator.__class__.__name__}")
    
    def register_benchmark_suite(self, benchmark: BenchmarkProtocol) -> None:
        """Register a new benchmark suite."""
        self.benchmarks.append(benchmark)
        logger.info(f"Registered benchmark suite: {benchmark.__class__.__name__}")
    
    def register_database_tester(self, tester: DatabaseIntegrationProtocol) -> None:
        """Register a new database integration tester."""
        self.database_testers.append(tester)
        logger.info(f"Registered database tester: {tester.__class__.__name__}")
    
    def register_credibility_assessor(self, assessor: CredibilityAssessorProtocol) -> None:
        """Register a new credibility assessor."""
        self.credibility_assessors.append(assessor)
        logger.info(f"Registered credibility assessor: {assessor.__class__.__name__}")
    
    def register_report_generator(self, generator: ReportGeneratorProtocol) -> None:
        """Register a new report generator."""
        self.report_generators.append(generator)
        logger.info(f"Registered report generator: {generator.__class__.__name__}")
    
    async def start_validation_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationSession:
        """Start a new validation session."""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a minimal request for the session
        from .models import ValidationRequest, ResearchData
        
        minimal_request = ValidationRequest(
            research_data=ResearchData(
                title="Session Data",
                abstract="Session created for validation",
                methodology="Various"
            ),
            metadata=metadata or {}
        )
        
        self.current_session = ValidationSession(
            session_id=session_id,
            request=minimal_request,
            metadata=metadata or {},
        )
        
        self.sessions.append(self.current_session)
        logger.info(f"Started validation session: {session_id}")
        
        return self.current_session
    
    async def end_validation_session(self) -> Optional[ValidationSession]:
        """End the current validation session."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            logger.info(
                f"Ended validation session: {self.current_session.session_id}, "
                f"Duration: {self.current_session.duration:.2f}s, "
                f"Success rate: {self.current_session.success_rate:.1%}"
            )
            
            # Generate reports if configured
            if self.config.auto_generate_reports:
                await self._generate_session_reports(self.current_session)
            
            session = self.current_session
            self.current_session = None
            return session
        
        return None
    
    async def run_comprehensive_validation(
        self,
        research_output: Any,
        test_categories: Optional[List[str]] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationSession:
        """
        Run comprehensive validation on research output.
        
        Args:
            research_output: The research output to validate
            test_categories: Specific categories to test (all if None)
            session_metadata: Additional metadata for the session
        
        Returns:
            Complete validation session with all results
        """
        session = await self.start_validation_session(
            metadata=session_metadata
        )
        
        try:
            # Run validators
            if not test_categories or "validation" in test_categories:
                await self._run_validators(research_output)
            
            # Run benchmarks
            if not test_categories or "benchmarks" in test_categories:
                await self._run_benchmarks(research_output)
            
            # Run database integration tests
            if not test_categories or "database_integration" in test_categories:
                await self._run_database_integration_tests(research_output)
            
            # Run credibility assessments
            if not test_categories or "credibility" in test_categories:
                await self._run_credibility_assessments(research_output)
            
        except Exception as e:
            logger.error(f"Error during validation session: {e}")
            # Add error result
            error_result = ValidationResult(
                validator_name="framework",
                test_name="session_execution",
                status="failed",
                details={"error": str(e), "error_type": type(e).__name__}
            )
            session.results.append(error_result)
        
        finally:
            await self.end_validation_session()
        
        return session
    
    async def _run_validators(self, research_output: Any) -> None:
        """Run all registered validators."""
        logger.info("Running validation tests...")
        
        for validator in self.validators:
            try:
                validator_results = await validator.validate(research_output)
                if isinstance(validator_results, list):
                    self.current_session.results.extend(validator_results)
                else:
                    self.current_session.results.append(validator_results)
                    
            except Exception as e:
                logger.error(f"Validator {validator.__class__.__name__} failed: {e}")
                error_result = ValidationResult(
                    validator_name=validator.__class__.__name__,
                    test_name="validator_execution",
                    status="failed",
                    details={"error": str(e)}
                )
                self.current_session.results.append(error_result)
    
    async def _run_benchmarks(self, research_output: Any) -> None:
        """Run all registered benchmark suites."""
        logger.info("Running benchmark tests...")
        
        for benchmark in self.benchmarks:
            try:
                benchmark_results = await benchmark.run_benchmarks(research_output)
                if isinstance(benchmark_results, list):
                    self.current_session.results.extend(benchmark_results)
                else:
                    self.current_session.results.append(benchmark_results)
                    
            except Exception as e:
                logger.error(f"Benchmark {benchmark.__class__.__name__} failed: {e}")
                error_result = ValidationResult(
                    validator_name=benchmark.__class__.__name__,
                    test_name="benchmark_execution",
                    status="failed",
                    details={"error": str(e)}
                )
                self.current_session.results.append(error_result)
    
    async def _run_database_integration_tests(self, research_output: Any) -> None:
        """Run all registered database integration tests."""
        logger.info("Running database integration tests...")
        
        for tester in self.database_testers:
            try:
                integration_results = await tester.test_integration(research_output)
                if isinstance(integration_results, list):
                    self.current_session.results.extend(integration_results)
                else:
                    self.current_session.results.append(integration_results)
                    
            except Exception as e:
                logger.error(f"Database tester {tester.__class__.__name__} failed: {e}")
                error_result = ValidationResult(
                    validator_name=tester.__class__.__name__,
                    test_name="database_integration",
                    status="failed",
                    details={"error": str(e)}
                )
                self.current_session.results.append(error_result)
    
    async def _run_credibility_assessments(self, research_output: Any) -> None:
        """Run all registered credibility assessments."""
        logger.info("Running credibility assessments...")
        
        for assessor in self.credibility_assessors:
            try:
                credibility_results = await assessor.assess_credibility(research_output)
                if isinstance(credibility_results, list):
                    self.current_session.results.extend(credibility_results)
                else:
                    self.current_session.results.append(credibility_results)
                    
            except Exception as e:
                logger.error(f"Credibility assessor {assessor.__class__.__name__} failed: {e}")
                error_result = ValidationResult(
                    validator_name=assessor.__class__.__name__,
                    test_name="credibility_assessment",
                    status="failed",
                    details={"error": str(e)}
                )
                self.current_session.results.append(error_result)
    
    async def _generate_session_reports(self, session: ValidationSession) -> None:
        """Generate reports for a completed session."""
        logger.info("Generating session reports...")
        
        for generator in self.report_generators:
            try:
                await generator.generate_report(session)
            except Exception as e:
                logger.error(f"Report generator {generator.__class__.__name__} failed: {e}")
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a validation session."""
        session = next((s for s in self.sessions if s.session_id == session_id), None)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration": session.duration,
            "total_tests": session.total_count,
            "passed_tests": session.passed_count,
            "failed_tests": session.failed_count,
            "success_rate": session.success_rate,
            "metadata": session.metadata,
        }
    
    def get_framework_statistics(self) -> Dict[str, Any]:
        """Get overall framework statistics."""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_tests": 0,
                "overall_success_rate": 0.0,
            }
        
        total_tests = sum(s.total_count for s in self.sessions)
        total_passed = sum(s.passed_count for s in self.sessions)
        
        return {
            "total_sessions": len(self.sessions),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0.0,
            "average_session_duration": sum(
                s.duration for s in self.sessions if s.duration
            ) / len([s for s in self.sessions if s.duration]) if self.sessions else 0.0,
            "registered_validators": len(self.validators),
            "registered_benchmarks": len(self.benchmarks),
            "registered_database_testers": len(self.database_testers),
            "registered_credibility_assessors": len(self.credibility_assessors),
            "registered_report_generators": len(self.report_generators),
        }
    
    async def cleanup(self) -> None:
        """Cleanup framework resources."""
        logger.info("Cleaning up framework resources...")
        
        # Cleanup validators
        for validator in self.validators:
            if hasattr(validator, 'cleanup'):
                try:
                    await validator.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up validator {validator.__class__.__name__}: {e}")
        
        # Cleanup other components similarly
        for component_list in [self.benchmarks, self.database_testers, 
                             self.credibility_assessors, self.report_generators]:
            for component in component_list:
                if hasattr(component, 'cleanup'):
                    try:
                        await component.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up component {component.__class__.__name__}: {e}")
        
        logger.info("Framework cleanup completed")