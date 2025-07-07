"""
Component registry for managing validators, benchmarks, and other components.
"""
from typing import Dict, List, Optional, Type
import logging

from .interfaces import (
    ValidatorProtocol,
    BenchmarkProtocol,
    CredibilityAssessorProtocol,
    ReportGeneratorProtocol,
    DatabaseIntegrationProtocol
)

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """Registry for managing framework components."""
    
    def __init__(self):
        """Initialize the component registry."""
        self._validators: Dict[str, ValidatorProtocol] = {}
        self._benchmarks: Dict[str, BenchmarkProtocol] = {}
        self._assessors: Dict[str, CredibilityAssessorProtocol] = {}
        self._report_generators: Dict[str, ReportGeneratorProtocol] = {}
        self._database_integrations: Dict[str, DatabaseIntegrationProtocol] = {}
        
    def register_validator(self, validator: ValidatorProtocol) -> None:
        """
        Register a validator.
        
        Args:
            validator: Validator instance to register
            
        Raises:
            ValueError: If validator with same name already exists
        """
        if validator.name in self._validators:
            raise ValueError(f"Validator '{validator.name}' already registered")
        
        self._validators[validator.name] = validator
        logger.info(f"Registered validator: {validator.name} v{validator.version}")
    
    def register_benchmark(self, benchmark: BenchmarkProtocol) -> None:
        """
        Register a benchmark.
        
        Args:
            benchmark: Benchmark instance to register
            
        Raises:
            ValueError: If benchmark with same name already exists
        """
        if benchmark.name in self._benchmarks:
            raise ValueError(f"Benchmark '{benchmark.name}' already registered")
        
        self._benchmarks[benchmark.name] = benchmark
        logger.info(f"Registered benchmark: {benchmark.name}")
    
    def register_assessor(self, assessor: CredibilityAssessorProtocol) -> None:
        """Register a credibility assessor."""
        name = assessor.__class__.__name__
        if name in self._assessors:
            raise ValueError(f"Assessor '{name}' already registered")
        
        self._assessors[name] = assessor
        logger.info(f"Registered assessor: {name}")
    
    def register_report_generator(self, generator: ReportGeneratorProtocol) -> None:
        """Register a report generator."""
        name = generator.__class__.__name__
        if name in self._report_generators:
            raise ValueError(f"Report generator '{name}' already registered")
        
        self._report_generators[name] = generator
        logger.info(f"Registered report generator: {name}")
    
    def register_database_integration(self, integration: DatabaseIntegrationProtocol) -> None:
        """Register a database integration."""
        if integration.database_name in self._database_integrations:
            raise ValueError(f"Database integration '{integration.database_name}' already registered")
        
        self._database_integrations[integration.database_name] = integration
        logger.info(f"Registered database integration: {integration.database_name}")
    
    def get_validator(self, name: str) -> Optional[ValidatorProtocol]:
        """Get a validator by name."""
        return self._validators.get(name)
    
    def get_benchmark(self, name: str) -> Optional[BenchmarkProtocol]:
        """Get a benchmark by name."""
        return self._benchmarks.get(name)
    
    def get_assessor(self, name: str) -> Optional[CredibilityAssessorProtocol]:
        """Get an assessor by name."""
        return self._assessors.get(name)
    
    def get_report_generator(self, name: str) -> Optional[ReportGeneratorProtocol]:
        """Get a report generator by name."""
        return self._report_generators.get(name)
    
    def get_database_integration(self, name: str) -> Optional[DatabaseIntegrationProtocol]:
        """Get a database integration by name."""
        return self._database_integrations.get(name)
    
    def get_validators(self) -> List[ValidatorProtocol]:
        """Get all registered validators."""
        return list(self._validators.values())
    
    def get_benchmarks(self) -> List[BenchmarkProtocol]:
        """Get all registered benchmarks."""
        return list(self._benchmarks.values())
    
    def get_assessors(self) -> List[CredibilityAssessorProtocol]:
        """Get all registered assessors."""
        return list(self._assessors.values())
    
    def get_report_generators(self) -> List[ReportGeneratorProtocol]:
        """Get all registered report generators."""
        return list(self._report_generators.values())
    
    def get_database_integrations(self) -> List[DatabaseIntegrationProtocol]:
        """Get all registered database integrations."""
        return list(self._database_integrations.values())
    
    def list_validators(self) -> List[str]:
        """List names of all registered validators."""
        return list(self._validators.keys())
    
    def list_benchmarks(self) -> List[str]:
        """List names of all registered benchmarks."""
        return list(self._benchmarks.keys())
    
    def unregister_validator(self, name: str) -> bool:
        """
        Unregister a validator.
        
        Args:
            name: Name of validator to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._validators:
            del self._validators[name]
            logger.info(f"Unregistered validator: {name}")
            return True
        return False
    
    def unregister_benchmark(self, name: str) -> bool:
        """
        Unregister a benchmark.
        
        Args:
            name: Name of benchmark to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._benchmarks:
            del self._benchmarks[name]
            logger.info(f"Unregistered benchmark: {name}")
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all registered components."""
        self._validators.clear()
        self._benchmarks.clear()
        self._assessors.clear()
        self._report_generators.clear()
        self._database_integrations.clear()
        logger.info("Cleared all registered components")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about registered components."""
        return {
            "validators": len(self._validators),
            "benchmarks": len(self._benchmarks),
            "assessors": len(self._assessors),
            "report_generators": len(self._report_generators),
            "database_integrations": len(self._database_integrations),
            "total": (
                len(self._validators) + 
                len(self._benchmarks) + 
                len(self._assessors) +
                len(self._report_generators) +
                len(self._database_integrations)
            )
        }