"""
Validation manager for handling cross-cutting concerns like logging, config management, and error handling.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Type

from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.exceptions import (
    ErrorHandler, ErrorContext, TimeoutError, DataValidationError,
    ProtocolComplianceError, ResourceExhaustedError
)
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ValidationResult, ValidationStatus


@dataclass
class ValidationMetrics:
    """Metrics for validation performance tracking."""
    start_time: float
    end_time: float
    validator_name: str
    data_type: str
    success: bool
    error_message: Optional[str] = None
    
    @property
    def execution_time(self) -> float:
        """Calculate execution time in seconds."""
        return self.end_time - self.start_time


class ValidationManager:
    """Manages validation execution with cross-cutting concerns."""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, ValidationMetrics] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on config settings."""
        log_level = getattr(logging, self.config.log_level.upper())
        self.logger.setLevel(log_level)
        
        if self.config.enable_detailed_logging:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def execute_validation(
        self,
        validator: ValidatorProtocol,
        data: Any,
        validation_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Execute validation with comprehensive error handling and metrics.
        
        Args:
            validator: The validator instance to execute
            data: The data to validate
            validation_id: Optional ID for tracking this validation
            
        Returns:
            ValidationResult with execution metrics and error handling
        """
        start_time = time.time()
        validator_name = validator.name
        data_type = type(data).__name__
        
        # Generate validation ID if not provided
        if validation_id is None:
            validation_id = f"{validator_name}_{int(start_time)}"
        
        self.logger.info(f"Starting validation: {validator_name} for {data_type}")
        
        try:
            # Validate input data type
            if not self._is_supported_data_type(validator, data):
                raise DataValidationError(
                    f"Unsupported data type {data_type} for validator {validator_name}",
                    field_name="data_type",
                    invalid_value=data_type
                )
            
            # Execute validation with timeout and retry logic
            result = await self._execute_with_retry(validator, data)
            
            # Log success
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.logger.info(
                f"Validation completed: {validator_name} - "
                f"Score: {result.score:.3f} - "
                f"Time: {execution_time:.3f}s"
            )
            
            # Track metrics
            if self.config.track_performance_metrics:
                self._record_metrics(
                    validation_id,
                    start_time,
                    end_time,
                    validator_name,
                    data_type,
                    True
                )
            
            # Add execution time to result
            result.execution_time_seconds = execution_time
            return result
            
        except Exception as e:
            end_time = time.time()
            
            # Create error context
            context = ErrorContext(
                validator_name=validator_name,
                operation="validation",
                data_type=data_type,
                timestamp=start_time,
                config_snapshot={
                    "timeout_seconds": self.config.timeout_seconds,
                    "retry_attempts": self.config.retry_attempts,
                    "fail_fast": self.config.fail_fast
                }
            )
            
            # Handle error with comprehensive error handling
            error_info = ErrorHandler.handle_validation_error(
                e, context, self.logger, self.config.fail_fast
            )
            
            # Track error metrics
            if self.config.track_performance_metrics:
                self._record_metrics(
                    validation_id,
                    start_time,
                    end_time,
                    validator_name,
                    data_type,
                    False,
                    error_info["error_message"]
                )
            
            # Return error result
            return ErrorHandler.create_error_result(
                validator_name,
                error_info,
                end_time - start_time
            )
    
    def _is_supported_data_type(self, validator: ValidatorProtocol, data: Any) -> bool:
        """Check if the data type is supported by the validator."""
        return type(data) in validator.supported_data_types
    
    async def _execute_with_retry(
        self, 
        validator: ValidatorProtocol, 
        data: Any
    ) -> ValidationResult:
        """Execute validation with retry logic and timeout handling."""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                return await asyncio.wait_for(
                    validator.validate(data),
                    timeout=self.config.timeout_seconds
                )
            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(
                    f"validation_{validator.name}",
                    self.config.timeout_seconds
                )
                if not ErrorHandler.should_retry(last_exception, attempt, self.config.retry_attempts):
                    break
            except Exception as e:
                last_exception = e
                if not ErrorHandler.should_retry(e, attempt, self.config.retry_attempts):
                    break
            
            # Wait before retrying
            if attempt < self.config.retry_attempts:
                delay = ErrorHandler.get_retry_delay(last_exception, attempt, self.config.backoff_factor)
                self.logger.info(f"Retrying validation in {delay:.2f} seconds (attempt {attempt + 1})")
                await asyncio.sleep(delay)
        
        # Re-raise the last exception if all retries failed
        raise last_exception
    
    def _create_error_result(
        self,
        validator_name: str,
        error_message: str,
        start_time: float,
        error_type: str
    ) -> ValidationResult:
        """Create a standardized error result."""
        return ValidationResult(
            validator_name=validator_name,
            test_name=f"{validator_name}_validation",
            status=ValidationStatus.ERROR,
            score=0.0,
            details={
                "error": error_message,
                "error_type": error_type,
                "execution_time": time.time() - start_time
            }
        )
    
    def _record_metrics(
        self,
        validation_id: str,
        start_time: float,
        end_time: float,
        validator_name: str,
        data_type: str,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record validation metrics."""
        metrics = ValidationMetrics(
            start_time=start_time,
            end_time=end_time,
            validator_name=validator_name,
            data_type=data_type,
            success=success,
            error_message=error_message
        )
        
        self.metrics[validation_id] = metrics
    
    def get_metrics(self, validator_name: Optional[str] = None) -> Dict[str, ValidationMetrics]:
        """Get validation metrics, optionally filtered by validator name."""
        if validator_name:
            return {
                k: v for k, v in self.metrics.items()
                if v.validator_name == validator_name
            }
        return self.metrics.copy()
    
    def clear_metrics(self):
        """Clear all recorded metrics."""
        self.metrics.clear()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of validation performance."""
        if not self.metrics:
            return {"message": "No validation metrics recorded"}
        
        total_validations = len(self.metrics)
        successful_validations = sum(1 for m in self.metrics.values() if m.success)
        failed_validations = total_validations - successful_validations
        
        execution_times = [m.execution_time for m in self.metrics.values()]
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        validator_counts = {}
        for metric in self.metrics.values():
            validator_counts[metric.validator_name] = validator_counts.get(metric.validator_name, 0) + 1
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "average_execution_time": avg_execution_time,
            "validator_usage": validator_counts
        }