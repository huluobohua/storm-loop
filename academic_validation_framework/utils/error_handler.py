"""
Comprehensive error handling utilities for the academic validation framework.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Callable, Type, List
from functools import wraps
import asyncio
from datetime import datetime
from enum import Enum

from ..models import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationError(Exception):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()


class DataError(ValidationError):
    """Error related to input data issues."""
    pass


class ProcessingError(ValidationError):
    """Error during processing/validation."""
    pass


class ConfigurationError(ValidationError):
    """Error in configuration or setup."""
    pass


class ResourceError(ValidationError):
    """Error related to resource availability."""
    pass


class ErrorHandler:
    """Centralized error handling for validation framework."""
    
    def __init__(self):
        self._error_history: List[Dict[str, Any]] = []
        self._error_callbacks: List[Callable] = []
        self._max_history = 1000
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        # Add to history
        self._error_history.append(error_info)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        # Log based on severity
        if isinstance(error, ValidationError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"Critical error: {error}", exc_info=True)
            elif error.severity == ErrorSeverity.HIGH:
                logger.error(f"High severity error: {error}", exc_info=True)
            else:
                logger.warning(f"Validation error: {error}")
        else:
            logger.error(f"Unexpected error: {error}", exc_info=True)
        
        # Call registered callbacks
        for callback in self._error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def register_error_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for error events."""
        self._error_callbacks.append(callback)
    
    def get_error_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get error history."""
        if limit:
            return self._error_history[-limit:]
        return self._error_history.copy()
    
    def clear_error_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
    
    def create_error_result(
        self,
        validator_name: str,
        test_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Create a standardized error validation result."""
        self.log_error(error, context)
        
        # Determine appropriate recommendations based on error type
        recommendations = self._generate_error_recommendations(error)
        
        return ValidationResult(
            validator_name=validator_name,
            test_name=test_name,
            status=ValidationStatus.ERROR,
            score=0.0,
            error_message=str(error),
            details={
                "error_type": type(error).__name__,
                "error_severity": error.severity.value if isinstance(error, ValidationError) else "unknown",
                "error_details": error.details if isinstance(error, ValidationError) else {},
                "context": context or {}
            },
            recommendations=recommendations,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc() if logger.level <= logging.DEBUG else None
            }
        )
    
    def _generate_error_recommendations(self, error: Exception) -> List[str]:
        """Generate recommendations based on error type."""
        recommendations = []
        
        if isinstance(error, DataError):
            recommendations.extend([
                "Verify input data format and completeness",
                "Check data encoding and special characters",
                "Ensure all required fields are present"
            ])
        elif isinstance(error, ProcessingError):
            recommendations.extend([
                "Check system resources (memory, CPU)",
                "Verify processing pipeline configuration",
                "Consider reducing data size or complexity"
            ])
        elif isinstance(error, ConfigurationError):
            recommendations.extend([
                "Review configuration settings",
                "Ensure all required dependencies are installed",
                "Check environment variables and paths"
            ])
        elif isinstance(error, ResourceError):
            recommendations.extend([
                "Check network connectivity",
                "Verify API keys and credentials",
                "Ensure sufficient system resources"
            ])
        else:
            recommendations.extend([
                "Check logs for detailed error information",
                "Verify system requirements are met",
                "Contact support if issue persists"
            ])
        
        return recommendations


# Global error handler instance
error_handler = ErrorHandler()


def handle_validation_errors(
    exceptions: tuple = (Exception,),
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    default_result: Optional[Callable] = None
):
    """
    Decorator for handling errors in validation methods.
    
    Args:
        exceptions: Tuple of exception types to catch
        severity: Default severity for caught exceptions
        default_result: Callable to generate default result on error
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                # Extract validator instance if available
                validator = args[0] if args and hasattr(args[0], 'name') else None
                validator_name = validator.name if validator else "Unknown"
                test_name = func.__name__
                
                # Log error
                context = {
                    "function": func.__name__,
                    "args": str(args[1:])[:200],  # Limit size
                    "kwargs": str(kwargs)[:200]
                }
                
                if isinstance(e, ValidationError):
                    e.severity = e.severity or severity
                else:
                    # Wrap in ValidationError
                    e = ProcessingError(str(e), severity=severity)
                
                # Generate error result
                if default_result:
                    return default_result(validator_name, test_name, e)
                else:
                    return error_handler.create_error_result(
                        validator_name, test_name, e, context
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Similar handling for sync functions
                validator = args[0] if args and hasattr(args[0], 'name') else None
                validator_name = validator.name if validator else "Unknown"
                test_name = func.__name__
                
                context = {
                    "function": func.__name__,
                    "args": str(args[1:])[:200],
                    "kwargs": str(kwargs)[:200]
                }
                
                if isinstance(e, ValidationError):
                    e.severity = e.severity or severity
                else:
                    e = ProcessingError(str(e), severity=severity)
                
                if default_result:
                    return default_result(validator_name, test_name, e)
                else:
                    return error_handler.create_error_result(
                        validator_name, test_name, e, context
                    )
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_input(
    required_fields: List[str],
    data_type: Type = dict
):
    """
    Decorator to validate input data.
    
    Args:
        required_fields: List of required field names
        data_type: Expected data type
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get data argument (usually first after self)
            data = args[1] if len(args) > 1 else kwargs.get('data')
            
            if data is None:
                raise DataError("No data provided", severity=ErrorSeverity.HIGH)
            
            if not isinstance(data, data_type):
                raise DataError(
                    f"Invalid data type: expected {data_type.__name__}, got {type(data).__name__}",
                    severity=ErrorSeverity.HIGH
                )
            
            # Check required fields for dict-like objects
            if hasattr(data, '__getitem__'):
                missing_fields = []
                for field in required_fields:
                    if not hasattr(data, field) and field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    raise DataError(
                        f"Missing required fields: {', '.join(missing_fields)}",
                        severity=ErrorSeverity.HIGH,
                        details={"missing_fields": missing_fields}
                    )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar validation for sync functions
            data = args[1] if len(args) > 1 else kwargs.get('data')
            
            if data is None:
                raise DataError("No data provided", severity=ErrorSeverity.HIGH)
            
            if not isinstance(data, data_type):
                raise DataError(
                    f"Invalid data type: expected {data_type.__name__}, got {type(data).__name__}",
                    severity=ErrorSeverity.HIGH
                )
            
            if hasattr(data, '__getitem__'):
                missing_fields = []
                for field in required_fields:
                    if not hasattr(data, field) and field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    raise DataError(
                        f"Missing required fields: {', '.join(missing_fields)}",
                        severity=ErrorSeverity.HIGH,
                        details={"missing_fields": missing_fields}
                    )
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_get(data: Any, path: str, default: Any = None) -> Any:
    """
    Safely get nested value from data structure.
    
    Args:
        data: Data structure to query
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    try:
        parts = path.split('.')
        value = data
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif hasattr(value, '__getitem__'):
                value = value[part]
            else:
                return default
        
        return value
    except (KeyError, AttributeError, TypeError, IndexError):
        return default


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on error.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delays
        exceptions: Tuple of exceptions to retry on
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_error
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator