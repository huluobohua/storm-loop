"""
Test Config Validator - TDD Implementation
Tests for proper exception handling and validation behavior
"""

import pytest
from pydantic import ValidationError
from frontend.advanced_interface.config_validator import ConfigValidator


class TestConfigValidatorExceptionHandling:
    """Test proper exception handling in ConfigValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()
    
    def test_research_config_validation_error_preserved(self):
        """Test that ValidationError details are preserved, not wrapped."""
        # Red: Test should fail - current code catches Exception and wraps it
        invalid_config = {
            "storm_mode": "invalid_mode",  # Invalid enum value
            "max_papers": -5,  # Invalid range
            "quality_threshold": 2.0  # Invalid range
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_research_config(invalid_config)
        
        # Should be ValidationError, not ValueError
        assert isinstance(exc_info.value, ValidationError)
        
        # Should contain specific field errors
        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Multiple validation errors
        
        # Should have specific error types
        error_types = [error['type'] for error in errors]
        assert any('enum' in error_type for error_type in error_types)
        assert any('greater_than_equal' in error_type for error_type in error_types)
    
    def test_session_config_validation_error_preserved(self):
        """Test that session config ValidationError details are preserved."""
        # Red: Test should fail - current code catches Exception and wraps it
        invalid_config = {
            "session_name": "",  # Empty name should fail
            "user_id": "",  # Empty user_id should fail
            "session_timeout": 60,  # Below minimum
            "priority": "invalid_priority"  # Invalid enum
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_session_config(invalid_config)
        
        # Should be ValidationError, not ValueError
        assert isinstance(exc_info.value, ValidationError)
        
        # Should contain specific field errors
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Multiple validation errors
    
    def test_research_config_nested_error_context(self):
        """Test that nested validation errors maintain context."""
        # Red: Test should fail - current code loses nested context
        invalid_config = {
            "agents": [],  # Empty list should fail min_length validation
            "databases": [],  # Empty list should fail min_length validation
            "timeout_minutes": 2000  # Exceeds maximum
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_research_config(invalid_config)
        
        errors = exc_info.value.errors()
        
        # Should have specific field locations
        field_names = [error['loc'][0] for error in errors]
        assert 'agents' in field_names
        assert 'databases' in field_names
        assert 'timeout_minutes' in field_names
    
    def test_successful_validation_returns_dict(self):
        """Test that successful validation returns properly formatted dict."""
        valid_config = {
            "storm_mode": "hybrid",
            "max_papers": 25,
            "quality_threshold": 0.8
        }
        
        result = self.validator.validate_research_config(valid_config)
        
        # Should return dict
        assert isinstance(result, dict)
        
        # Should contain expected fields
        assert result["storm_mode"] == "hybrid"
        assert result["max_papers"] == 25
        assert result["quality_threshold"] == 0.8
    
    def test_session_config_with_nested_research_config_errors(self):
        """Test that nested research config errors are properly propagated."""
        # Red: Test should fail - current code may lose nested context
        invalid_config = {
            "session_name": "Test Session",
            "user_id": "user123",
            "research_config": {
                "storm_mode": "invalid_mode",  # This should cause ValidationError
                "max_papers": -10
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate_session_config(invalid_config)
        
        # Should preserve nested validation context
        errors = exc_info.value.errors()
        assert len(errors) >= 1
        
        # Should have research_config in error location path
        nested_errors = [error for error in errors if 'research_config' in str(error['loc'])]
        assert len(nested_errors) >= 1


class TestConfigValidatorAsyncCompatibility:
    """Test async/await compatibility for future integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()
    
    @pytest.mark.asyncio
    async def test_validator_works_in_async_context(self):
        """Test that validator works correctly in async context."""
        # This test ensures our validator is async-compatible
        valid_config = {
            "storm_mode": "academic",
            "max_papers": 100,
            "quality_threshold": 0.9
        }
        
        # Should work in async context
        result = self.validator.validate_research_config(valid_config)
        assert isinstance(result, dict)
        assert result["storm_mode"] == "academic"


class TestConfigValidatorConcurrency:
    """Test concurrent validation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_safety(self):
        """Test that multiple concurrent validations don't interfere."""
        import asyncio
        
        configs = [
            {"storm_mode": "fast", "max_papers": 10},
            {"storm_mode": "thorough", "max_papers": 50},
            {"storm_mode": "hybrid", "max_papers": 25}
        ]
        
        async def validate_config(config):
            """Async wrapper for validation."""
            return self.validator.validate_research_config(config)
        
        # Run concurrent validations
        tasks = [validate_config(config) for config in configs]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)
        
        # Results should match inputs
        assert results[0]["storm_mode"] == "fast"
        assert results[1]["storm_mode"] == "thorough"
        assert results[2]["storm_mode"] == "hybrid"