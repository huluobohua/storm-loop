"""
Custom exception classes for the academic validation framework.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


class AcademicValidationError(Exception):
    """Base exception for all academic validation errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.message = message
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(AcademicValidationError):
    """Raised when there's an issue with configuration."""
    pass


class ValidationError(AcademicValidationError):
    """Raised when validation fails due to invalid input or process errors."""
    pass


class DataValidationError(ValidationError):
    """Raised when input data is invalid or incomplete."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, invalid_value: Optional[Any] = None):
        super().__init__(message, error_code="DATA_VALIDATION_ERROR")
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.details.update({
            "field_name": field_name,
            "invalid_value": str(invalid_value) if invalid_value is not None else None
        })


class TimeoutError(AcademicValidationError):
    """Raised when a validation operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, error_code="TIMEOUT_ERROR")
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.details.update({
            "operation": operation,
            "timeout_seconds": timeout_seconds
        })


class NetworkError(AcademicValidationError):
    """Raised when network-related operations fail."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, error_code="NETWORK_ERROR")
        self.url = url
        self.status_code = status_code
        self.details.update({
            "url": url,
            "status_code": status_code
        })


class RateLimitError(NetworkError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, service: str, retry_after: Optional[float] = None):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message, error_code="RATE_LIMIT_ERROR")
        self.service = service
        self.retry_after = retry_after
        self.details.update({
            "service": service,
            "retry_after": retry_after
        })


class ProtocolComplianceError(ValidationError):
    """Raised when a validator doesn't comply with the expected protocol."""
    
    def __init__(self, validator_name: str, missing_methods: List[str]):
        message = f"Validator '{validator_name}' missing required methods: {', '.join(missing_methods)}"
        super().__init__(message, error_code="PROTOCOL_COMPLIANCE_ERROR")
        self.validator_name = validator_name
        self.missing_methods = missing_methods
        self.details.update({
            "validator_name": validator_name,
            "missing_methods": missing_methods
        })


class ResourceExhaustedError(AcademicValidationError):
    """Raised when system resources are exhausted."""
    
    def __init__(self, resource_type: str, limit: Optional[Any] = None):
        message = f"Resource exhausted: {resource_type}"
        if limit:
            message += f" (limit: {limit})"
        super().__init__(message, error_code="RESOURCE_EXHAUSTED")
        self.resource_type = resource_type
        self.limit = limit
        self.details.update({
            "resource_type": resource_type,
            "limit": limit
        })


class CitationFormatError(ValidationError):
    """Raised when citation format validation fails."""
    
    def __init__(self, citation: str, format_name: str, issues: List[str]):
        message = f"Citation format error in {format_name}: {'; '.join(issues)}"
        super().__init__(message, error_code="CITATION_FORMAT_ERROR")
        self.citation = citation
        self.format_name = format_name
        self.issues = issues
        self.details.update({
            "citation": citation,
            "format_name": format_name,
            "issues": issues
        })


class PRISMAComplianceError(ValidationError):
    """Raised when PRISMA compliance validation fails."""
    
    def __init__(self, checkpoint: str, reason: str):
        message = f"PRISMA compliance failure at checkpoint '{checkpoint}': {reason}"
        super().__init__(message, error_code="PRISMA_COMPLIANCE_ERROR")
        self.checkpoint = checkpoint
        self.reason = reason
        self.details.update({
            "checkpoint": checkpoint,
            "reason": reason
        })


class BiasDetectionError(ValidationError):
    """Raised when bias detection fails."""
    
    def __init__(self, bias_type: str, reason: str):
        message = f"Bias detection error for {bias_type}: {reason}"
        super().__init__(message, error_code="BIAS_DETECTION_ERROR")
        self.bias_type = bias_type
        self.reason = reason
        self.details.update({
            "bias_type": bias_type,
            "reason": reason
        })


@dataclass
class ErrorContext:
    """Context information for error handling."""
    validator_name: str
    operation: str
    data_type: str
    timestamp: float
    config_snapshot: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "operation": self.operation,
            "data_type": self.data_type,
            "timestamp": self.timestamp,
            "config_snapshot": self.config_snapshot
        }


class ErrorHandler:
    """Centralized error handling for the validation framework."""
    
    @staticmethod
    def handle_validation_error(
        error: Exception,
        context: ErrorContext,
        logger,
        fail_fast: bool = False
    ) -> Dict[str, Any]:
        """
        Handle validation errors with appropriate logging and response.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            logger: Logger instance for error reporting
            fail_fast: Whether to re-raise the exception
            
        Returns:
            Error information dictionary
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context.to_dict(),
            "recoverable": ErrorHandler._is_recoverable_error(error)
        }
        
        # Add exception-specific details
        if hasattr(error, 'details'):
            error_info["details"] = error.details
        
        if hasattr(error, 'error_code'):
            error_info["error_code"] = error.error_code
        
        # Log the error
        if isinstance(error, (TimeoutError, NetworkError, ResourceExhaustedError)):
            logger.warning(f"Recoverable error in {context.validator_name}: {error}")
        else:
            logger.error(f"Validation error in {context.validator_name}: {error}")
        
        # Re-raise if fail_fast is enabled
        if fail_fast:
            raise error
        
        return error_info
    
    @staticmethod
    def _is_recoverable_error(error: Exception) -> bool:
        """Determine if an error is recoverable."""
        recoverable_types = (
            TimeoutError,
            NetworkError,
            RateLimitError,
            ResourceExhaustedError
        )
        return isinstance(error, recoverable_types)
    
    @staticmethod
    def create_error_result(
        validator_name: str,
        error_info: Dict[str, Any],
        execution_time: float = 0.0
    ) -> Dict[str, Any]:
        """Create a standardized error result."""
        from academic_validation_framework.models import ValidationResult, ValidationStatus
        
        return ValidationResult(
            validator_name=validator_name,
            test_name=f"{validator_name}_validation",
            status=ValidationStatus.ERROR,
            score=0.0,
            details={
                "error_info": error_info,
                "execution_time": execution_time,
                "recoverable": error_info.get("recoverable", False)
            }
        )
    
    @staticmethod
    def should_retry(error: Exception, attempt: int, max_attempts: int) -> bool:
        """Determine if an operation should be retried."""
        if attempt >= max_attempts:
            return False
        
        # Retry on network errors, timeouts, and rate limits
        retry_types = (TimeoutError, NetworkError, RateLimitError, ResourceExhaustedError)
        return isinstance(error, retry_types)
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int, backoff_factor: float = 2.0) -> float:
        """Calculate delay before retrying."""
        if isinstance(error, RateLimitError) and error.retry_after:
            return error.retry_after
        
        # Exponential backoff
        return min(backoff_factor ** attempt, 60.0)  # Max 60 seconds


class ValidationErrorCollector:
    """Collects and manages validation errors during batch operations."""
    
    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def add_error(self, error_info: Dict[str, Any]):
        """Add an error to the collection."""
        self.errors.append(error_info)
        
        if len(self.errors) >= self.max_errors:
            raise ResourceExhaustedError("error_collection", self.max_errors)
    
    def add_warning(self, warning_info: Dict[str, Any]):
        """Add a warning to the collection."""
        self.warnings.append(warning_info)
    
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings have been collected."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected errors and warnings."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "error_types": list(set(e.get("error_type", "unknown") for e in self.errors))
        }
    
    def clear(self):
        """Clear all collected errors and warnings."""
        self.errors.clear()
        self.warnings.clear()