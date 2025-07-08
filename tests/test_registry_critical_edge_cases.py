"""
Critical edge case tests for CitationFormatRegistry.
Tests thread safety, security, resource limits, and error conditions.
"""
import pytest
import threading
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_validation_framework.strategies.registry import CitationFormatRegistry
from academic_validation_framework.strategies.base import CitationFormatStrategy, FormatValidationResult


class MockStrategy(CitationFormatStrategy):
    """Mock strategy for testing."""
    
    def __init__(self, name="test", fail_init=False):
        if fail_init:
            raise RuntimeError("Initialization failed")
        self._name = name
    
    @property
    def format_name(self) -> str:
        return self._name
    
    @property
    def format_version(self) -> str:
        return "1.0"
    
    @property
    def supported_types(self) -> list:
        return ["test"]
    
    def validate(self, citations):
        return FormatValidationResult(
            format_name=self._name,
            is_valid=True,
            confidence=0.9
        )


class MaliciousStrategy:
    """Malicious non-strategy class for security testing."""
    
    def __init__(self):
        # This would be malicious code in a real attack
        pass
    
    def format_name(self):
        return "malicious"


class TestRegistrySecurityEdgeCases:
    """Test security-related edge cases."""
    
    def test_malicious_class_registration_blocked(self):
        """Test that non-strategy classes are rejected."""
        registry = CitationFormatRegistry()
        
        # Try to register a malicious class
        with pytest.raises(ValueError, match="Strategy class must inherit from CitationFormatStrategy"):
            registry.register_strategy(MaliciousStrategy)
    
    def test_invalid_class_name_blocked(self):
        """Test that classes with suspicious names are blocked."""
        registry = CitationFormatRegistry()
        
        # Create a class with invalid name
        class _SuspiciousStrategy(CitationFormatStrategy):
            def format_name(self):
                return "suspicious"
        
        with pytest.raises(ValueError, match="Invalid class name"):
            registry.register_strategy(_SuspiciousStrategy)
    
    def test_untrusted_module_blocked(self):
        """Test that strategies from untrusted modules are blocked."""
        registry = CitationFormatRegistry()
        
        # Mock a strategy from an untrusted module
        strategy = type('UntrustedStrategy', (CitationFormatStrategy,), {
            'format_name': property(lambda self: 'untrusted'),
            'format_version': property(lambda self: '1.0'),
            'supported_types': property(lambda self: ['test'])
        })
        strategy.__module__ = 'os'  # Dangerous module
        
        with pytest.raises(ValueError, match="Strategy from untrusted module"):
            registry.register_strategy(strategy)
    
    def test_invalid_priority_blocked(self):
        """Test that invalid priority values are blocked."""
        registry = CitationFormatRegistry()
        
        with pytest.raises(ValueError, match="Priority must be an integer between 0 and 100"):
            registry.register_strategy(MockStrategy, priority=-1)
        
        with pytest.raises(ValueError, match="Priority must be an integer between 0 and 100"):
            registry.register_strategy(MockStrategy, priority=101)
        
        with pytest.raises(ValueError, match="Priority must be an integer between 0 and 100"):
            registry.register_strategy(MockStrategy, priority="invalid")


class TestRegistryThreadSafety:
    """Test thread safety of registry operations."""
    
    def test_concurrent_registration(self):
        """Test that concurrent registrations don't corrupt state."""
        registry = CitationFormatRegistry()
        errors = []
        successes = []
        
        def register_strategy(strategy_id):
            try:
                strategy = type(f'TestStrategy{strategy_id}', (MockStrategy,), {})
                result = registry.register_strategy(strategy, priority=strategy_id % 100)
                successes.append(strategy_id)
            except Exception as e:
                errors.append((strategy_id, str(e)))
        
        # Create multiple threads registering strategies
        threads = []
        for i in range(20):
            thread = threading.Thread(target=register_strategy, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(successes) > 0, "No successful registrations"
        
        # Verify registry state is consistent
        formats = registry.get_available_formats()
        assert len(formats) == len(successes), "Registry state inconsistent"
    
    def test_concurrent_statistics_updates(self):
        """Test that concurrent statistics updates are thread-safe."""
        registry = CitationFormatRegistry()
        
        # Register a test strategy
        registry.register_strategy(MockStrategy)
        
        def update_statistics():
            # Simulate validation to trigger statistics updates
            result = FormatValidationResult(
                format_name="test",
                is_valid=True,
                confidence=0.8
            )
            registry._update_statistics("test", result, 1.0)
        
        # Run concurrent updates
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=update_statistics)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify statistics are consistent
        stats = registry.get_statistics()
        assert stats['total_validations'] == 100
        assert stats['successful_validations'] == 100


class TestRegistryResourceLimits:
    """Test resource limit enforcement."""
    
    def test_statistics_cleanup_triggered(self):
        """Test that statistics cleanup is triggered when limits are reached."""
        registry = CitationFormatRegistry()
        
        # Mock the performance constants to trigger cleanup quickly
        with patch('academic_validation_framework.strategies.registry.ValidationConstants') as mock_constants:
            mock_constants.PERFORMANCE.STATISTICS_CLEANUP_THRESHOLD = 5
            mock_constants.PERFORMANCE.MAX_STATISTICS_ENTRIES = 3
            mock_constants.PERFORMANCE.MAX_ERROR_PATTERNS = 3
            
            # Add many format distributions to trigger cleanup
            for i in range(10):
                registry._statistics.format_distribution[f"format_{i}"] = i + 1
            
            # Trigger cleanup by updating statistics
            result = FormatValidationResult(format_name="test", is_valid=True, confidence=0.8)
            registry._update_statistics("test", result, 1.0)
            
            # Verify cleanup occurred
            assert len(registry._statistics.format_distribution) <= 4  # 3 max + 1 new entry
    
    def test_cache_eviction_under_memory_pressure(self):
        """Test that cache properly evicts entries under memory pressure."""
        registry = CitationFormatRegistry(cache_size=2, cache_ttl=1)
        
        # Fill cache beyond capacity
        citations1 = ["Citation 1", "Citation 2"]
        citations2 = ["Citation 3", "Citation 4"] 
        citations3 = ["Citation 5", "Citation 6"]
        
        # These should trigger cache eviction
        registry.auto_detect_format(citations1)
        registry.auto_detect_format(citations2)
        registry.auto_detect_format(citations3)
        
        # Verify cache size is bounded
        cache_stats = registry.get_cache_stats()
        assert cache_stats['size'] <= 2
    
    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        registry = CitationFormatRegistry(cache_size=10, cache_ttl=1)  # 1 second TTL
        
        citations = ["Test citation"]
        
        # Add entry to cache
        registry.auto_detect_format(citations)
        
        # Should hit cache
        cache_stats = registry.get_cache_stats()
        initial_hits = cache_stats['hits']
        
        registry.auto_detect_format(citations)
        cache_stats = registry.get_cache_stats()
        assert cache_stats['hits'] > initial_hits
        
        # Wait for TTL expiration
        time.sleep(1.1)
        
        # Should miss cache due to expiration
        misses_before = cache_stats['misses']
        registry.auto_detect_format(citations)
        cache_stats = registry.get_cache_stats()
        assert cache_stats['misses'] > misses_before


class TestRegistryErrorHandling:
    """Test error handling edge cases."""
    
    def test_strategy_initialization_failure(self):
        """Test handling of strategy initialization failures."""
        registry = CitationFormatRegistry()
        
        # Create a strategy that fails to initialize
        failing_strategy = type('FailingStrategy', (MockStrategy,), {
            '__init__': lambda self: MockStrategy.__init__(self, fail_init=True)
        })
        
        # Should handle initialization failure gracefully
        result = registry.register_strategy(failing_strategy)
        assert result is False
    
    def test_validation_error_handling(self):
        """Test handling of validation errors in multi-format validation."""
        registry = CitationFormatRegistry()
        
        # Create a strategy that raises errors during validation
        class ErrorStrategy(MockStrategy):
            def validate(self, citations):
                raise RuntimeError("Validation failed")
        
        registry.register_strategy(ErrorStrategy)
        
        # Should handle errors gracefully and return results for working strategies
        results = registry.validate_multi_format(["test citation"])
        
        # Should have error result for the failing strategy
        assert "test" in results
        assert not results["test"].is_valid
        assert "error" in results["test"].errors[0].lower()
    
    def test_auto_detection_failure_handling(self):
        """Test handling of auto-detection failures."""
        registry = CitationFormatRegistry()
        
        # Mock strategy that fails during scoring
        with patch.object(MockStrategy, 'validate', side_effect=RuntimeError("Scoring failed")):
            registry.register_strategy(MockStrategy)
            
            # Should handle failure gracefully
            result = registry.auto_detect_format(["test citation"])
            assert result is None  # No format detected due to failure


class TestRegistryDataIntegrity:
    """Test data integrity under various conditions."""
    
    def test_duplicate_strategy_handling(self):
        """Test proper handling of duplicate strategy registrations."""
        registry = CitationFormatRegistry()
        
        # Register same strategy twice
        result1 = registry.register_strategy(MockStrategy)
        result2 = registry.register_strategy(MockStrategy)
        
        assert result1 is True
        assert result2 is True  # Should update existing registration
        
        # Should have only one entry
        formats = registry.get_available_formats()
        assert formats.count("test") == 1
    
    def test_strategy_metadata_consistency(self):
        """Test that strategy metadata remains consistent."""
        registry = CitationFormatRegistry()
        
        registry.register_strategy(MockStrategy, priority=75)
        
        # Get strategy and verify metadata
        strategy = registry.get_strategy("test")
        assert strategy is not None
        
        # Check internal metadata
        metadata = registry._strategies["test"]
        assert metadata.priority == 75
        assert metadata.name == "test"
        assert metadata.version == "1.0"
    
    def test_statistics_accuracy_under_load(self):
        """Test that statistics remain accurate under heavy load."""
        registry = CitationFormatRegistry()
        registry.register_strategy(MockStrategy)
        
        # Simulate many validations
        for i in range(100):
            result = FormatValidationResult(
                format_name="test",
                is_valid=i % 2 == 0,  # Alternate success/failure
                confidence=0.5 + (i % 50) / 100.0
            )
            registry._update_statistics("test", result, 1.0 + i % 10)
        
        stats = registry.get_statistics()
        assert stats['total_validations'] == 100
        assert stats['successful_validations'] == 50
        assert stats['failed_validations'] == 50
        assert 0 < stats['average_confidence'] < 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])