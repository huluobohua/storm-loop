"""
Unit tests for error handling and exception classes.
"""

import pytest
import time
from unittest.mock import Mock, patch
from academic_validation_framework.exceptions import (
    AcademicValidationError, ConfigurationError, ValidationError,
    DataValidationError, TimeoutError, NetworkError, RateLimitError,
    ProtocolComplianceError, ResourceExhaustedError, CitationFormatError,
    PRISMAComplianceError, BiasDetectionError, ErrorContext, ErrorHandler,
    ValidationErrorCollector
)
from academic_validation_framework.models import ValidationResult, ValidationStatus


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_academic_validation_error_base(self):
        """Test base exception functionality."""
        error = AcademicValidationError(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert error.message == "Test error"
    
    def test_data_validation_error(self):
        """Test data validation error."""
        error = DataValidationError(
            "Invalid field",
            field_name="test_field",
            invalid_value="invalid_data"
        )
        
        assert error.field_name == "test_field"
        assert error.invalid_value == "invalid_data"
        assert error.error_code == "DATA_VALIDATION_ERROR"
        assert error.details["field_name"] == "test_field"
        assert error.details["invalid_value"] == "invalid_data"
    
    def test_timeout_error(self):
        """Test timeout error."""
        error = TimeoutError("validation_operation", 30.0)
        
        assert error.operation == "validation_operation"
        assert error.timeout_seconds == 30.0
        assert error.error_code == "TIMEOUT_ERROR"
        assert "timed out after 30.0 seconds" in str(error)
    
    def test_network_error(self):
        """Test network error."""
        error = NetworkError(
            "Connection failed",
            url="https://api.example.com",
            status_code=500
        )
        
        assert error.url == "https://api.example.com"
        assert error.status_code == 500
        assert error.error_code == "NETWORK_ERROR"
        assert error.details["url"] == "https://api.example.com"
        assert error.details["status_code"] == 500
    
    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError("openai_api", retry_after=60.0)
        
        assert error.service == "openai_api"
        assert error.retry_after == 60.0
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert "Rate limit exceeded for openai_api" in str(error)
        assert "retry after 60.0 seconds" in str(error)
    
    def test_protocol_compliance_error(self):
        """Test protocol compliance error."""
        error = ProtocolComplianceError(
            "TestValidator",
            ["validate", "name"]
        )
        
        assert error.validator_name == "TestValidator"
        assert error.missing_methods == ["validate", "name"]
        assert error.error_code == "PROTOCOL_COMPLIANCE_ERROR"
        assert "TestValidator" in str(error)
        assert "validate, name" in str(error)
    
    def test_resource_exhausted_error(self):
        """Test resource exhausted error."""
        error = ResourceExhaustedError("memory", "2GB")
        
        assert error.resource_type == "memory"
        assert error.limit == "2GB"
        assert error.error_code == "RESOURCE_EXHAUSTED"
        assert "Resource exhausted: memory" in str(error)
        assert "limit: 2GB" in str(error)
    
    def test_citation_format_error(self):
        """Test citation format error."""
        error = CitationFormatError(
            "Smith, J. (2023). Title",
            "APA",
            ["Missing DOI", "Incorrect punctuation"]
        )
        
        assert error.citation == "Smith, J. (2023). Title"
        assert error.format_name == "APA"
        assert error.issues == ["Missing DOI", "Incorrect punctuation"]
        assert error.error_code == "CITATION_FORMAT_ERROR"
        assert "Citation format error in APA" in str(error)
    
    def test_prisma_compliance_error(self):
        """Test PRISMA compliance error."""
        error = PRISMAComplianceError(
            "protocol_registration",
            "No protocol registration found"
        )
        
        assert error.checkpoint == "protocol_registration"
        assert error.reason == "No protocol registration found"
        assert error.error_code == "PRISMA_COMPLIANCE_ERROR"
        assert "protocol_registration" in str(error)
    
    def test_bias_detection_error(self):
        """Test bias detection error."""
        error = BiasDetectionError(
            "confirmation_bias",
            "Insufficient data for analysis"
        )
        
        assert error.bias_type == "confirmation_bias"
        assert error.reason == "Insufficient data for analysis"
        assert error.error_code == "BIAS_DETECTION_ERROR"
        assert "confirmation_bias" in str(error)


class TestErrorContext:
    """Test error context functionality."""
    
    def test_error_context_creation(self):
        """Test creating error context."""
        context = ErrorContext(
            validator_name="test_validator",
            operation="validation",
            data_type="ResearchData",
            timestamp=time.time(),
            config_snapshot={"timeout": 30}
        )
        
        assert context.validator_name == "test_validator"
        assert context.operation == "validation"
        assert context.data_type == "ResearchData"
        assert isinstance(context.timestamp, float)
        assert context.config_snapshot == {"timeout": 30}
    
    def test_error_context_to_dict(self):
        """Test converting error context to dictionary."""
        context = ErrorContext(
            validator_name="test_validator",
            operation="validation",
            data_type="ResearchData",
            timestamp=1234567890.0
        )
        
        result = context.to_dict()
        
        assert result["validator_name"] == "test_validator"
        assert result["operation"] == "validation"
        assert result["data_type"] == "ResearchData"
        assert result["timestamp"] == 1234567890.0
        assert result["config_snapshot"] is None


class TestErrorHandler:
    """Test error handler functionality."""
    
    def test_handle_validation_error(self):
        """Test handling validation errors."""
        error = DataValidationError("Invalid data", field_name="test")
        context = ErrorContext(
            validator_name="test_validator",
            operation="validation",
            data_type="ResearchData",
            timestamp=time.time()
        )
        mock_logger = Mock()
        
        result = ErrorHandler.handle_validation_error(
            error, context, mock_logger, fail_fast=False
        )
        
        assert result["error_type"] == "DataValidationError"
        assert result["error_message"] == "[DATA_VALIDATION_ERROR] Invalid data"
        assert result["recoverable"] is False
        assert "context" in result
        assert "details" in result
        
        # Check logger was called
        mock_logger.error.assert_called_once()
    
    def test_handle_validation_error_fail_fast(self):
        """Test handling validation errors with fail_fast=True."""
        error = ValidationError("Test error")
        context = ErrorContext(
            validator_name="test_validator",
            operation="validation",
            data_type="ResearchData",
            timestamp=time.time()
        )
        mock_logger = Mock()
        
        with pytest.raises(ValidationError):
            ErrorHandler.handle_validation_error(
                error, context, mock_logger, fail_fast=True
            )
    
    def test_handle_recoverable_error(self):
        """Test handling recoverable errors."""
        error = TimeoutError("operation", 30.0)
        context = ErrorContext(
            validator_name="test_validator",
            operation="validation",
            data_type="ResearchData",
            timestamp=time.time()
        )
        mock_logger = Mock()
        
        result = ErrorHandler.handle_validation_error(
            error, context, mock_logger, fail_fast=False
        )
        
        assert result["recoverable"] is True
        # Should log as warning, not error
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
    
    def test_is_recoverable_error(self):
        """Test recoverable error detection."""
        assert ErrorHandler._is_recoverable_error(TimeoutError("op", 30)) is True
        assert ErrorHandler._is_recoverable_error(NetworkError("fail")) is True
        assert ErrorHandler._is_recoverable_error(RateLimitError("api")) is True
        assert ErrorHandler._is_recoverable_error(ResourceExhaustedError("memory")) is True
        assert ErrorHandler._is_recoverable_error(ValidationError("fail")) is False
        assert ErrorHandler._is_recoverable_error(ValueError("fail")) is False
    
    def test_create_error_result(self):
        """Test creating error result."""
        error_info = {
            "error_type": "ValidationError",
            "error_message": "Test error",
            "recoverable": False
        }
        
        result = ErrorHandler.create_error_result(
            "test_validator",
            error_info,
            execution_time=1.5
        )
        
        assert isinstance(result, ValidationResult)
        assert result.validator_name == "test_validator"
        assert result.status == ValidationStatus.ERROR
        assert result.score == 0.0
        assert result.details["error_info"] == error_info
        assert result.details["execution_time"] == 1.5
        assert result.details["recoverable"] is False
    
    def test_should_retry(self):
        """Test retry decision logic."""
        # Should retry on recoverable errors
        assert ErrorHandler.should_retry(TimeoutError("op", 30), 1, 3) is True
        assert ErrorHandler.should_retry(NetworkError("fail"), 2, 3) is True
        assert ErrorHandler.should_retry(RateLimitError("api"), 0, 3) is True
        
        # Should not retry on non-recoverable errors
        assert ErrorHandler.should_retry(ValidationError("fail"), 1, 3) is False
        assert ErrorHandler.should_retry(ValueError("fail"), 1, 3) is False
        
        # Should not retry if max attempts reached
        assert ErrorHandler.should_retry(TimeoutError("op", 30), 3, 3) is False
    
    def test_get_retry_delay(self):
        """Test retry delay calculation."""
        # Rate limit error with retry_after
        error = RateLimitError("api", retry_after=120.0)
        assert ErrorHandler.get_retry_delay(error, 1) == 120.0
        
        # Exponential backoff
        error = TimeoutError("op", 30)
        assert ErrorHandler.get_retry_delay(error, 0, 2.0) == 1.0  # 2^0
        assert ErrorHandler.get_retry_delay(error, 1, 2.0) == 2.0  # 2^1
        assert ErrorHandler.get_retry_delay(error, 2, 2.0) == 4.0  # 2^2
        
        # Max delay cap
        assert ErrorHandler.get_retry_delay(error, 10, 2.0) == 60.0  # Capped at 60


class TestValidationErrorCollector:
    """Test validation error collector."""
    
    def test_error_collector_initialization(self):
        """Test error collector initialization."""
        collector = ValidationErrorCollector(max_errors=50)
        
        assert collector.max_errors == 50
        assert len(collector.errors) == 0
        assert len(collector.warnings) == 0
        assert not collector.has_errors()
        assert not collector.has_warnings()
    
    def test_add_error(self):
        """Test adding errors."""
        collector = ValidationErrorCollector()
        error_info = {
            "error_type": "ValidationError",
            "error_message": "Test error"
        }
        
        collector.add_error(error_info)
        
        assert len(collector.errors) == 1
        assert collector.has_errors()
        assert collector.errors[0] == error_info
    
    def test_add_warning(self):
        """Test adding warnings."""
        collector = ValidationErrorCollector()
        warning_info = {
            "warning_type": "ConfigurationWarning",
            "warning_message": "Test warning"
        }
        
        collector.add_warning(warning_info)
        
        assert len(collector.warnings) == 1
        assert collector.has_warnings()
        assert collector.warnings[0] == warning_info
    
    def test_max_errors_limit(self):
        """Test maximum errors limit."""
        collector = ValidationErrorCollector(max_errors=2)
        
        # Add two errors (within limit)
        collector.add_error({"error": "Error 1"})
        collector.add_error({"error": "Error 2"})
        
        # Third error should raise ResourceExhaustedError
        with pytest.raises(ResourceExhaustedError) as exc_info:
            collector.add_error({"error": "Error 3"})
        
        assert exc_info.value.resource_type == "error_collection"
        assert exc_info.value.limit == 2
    
    def test_get_summary(self):
        """Test getting error summary."""
        collector = ValidationErrorCollector()
        
        collector.add_error({"error_type": "ValidationError", "message": "Error 1"})
        collector.add_error({"error_type": "TimeoutError", "message": "Error 2"})
        collector.add_warning({"warning_type": "ConfigWarning", "message": "Warning 1"})
        
        summary = collector.get_summary()
        
        assert summary["total_errors"] == 2
        assert summary["total_warnings"] == 1
        assert len(summary["errors"]) == 2
        assert len(summary["warnings"]) == 1
        assert set(summary["error_types"]) == {"ValidationError", "TimeoutError"}
    
    def test_clear_collector(self):
        """Test clearing the collector."""
        collector = ValidationErrorCollector()
        
        collector.add_error({"error": "Error"})
        collector.add_warning({"warning": "Warning"})
        
        assert collector.has_errors()
        assert collector.has_warnings()
        
        collector.clear()
        
        assert not collector.has_errors()
        assert not collector.has_warnings()
        assert len(collector.errors) == 0
        assert len(collector.warnings) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])