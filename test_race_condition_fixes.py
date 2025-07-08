#!/usr/bin/env python3
"""
Test suite to verify race condition fixes in CitationFormatRegistry.
Tests the fixes for all critical race conditions identified by Opus review.
"""

import threading
import time
import random
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from academic_validation_framework.strategies.registry import CitationFormatRegistry
from academic_validation_framework.strategies.base import CitationFormatStrategy, FormatValidationResult


class TestStrategy(CitationFormatStrategy):
    """Test strategy for race condition testing."""
    
    def __init__(self, name="test", strict_mode=False):
        self._name = name
        self._strict_mode = strict_mode
    
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
        # Simulate some processing time
        time.sleep(random.uniform(0.001, 0.005))
        return FormatValidationResult(
            format_name=self._name,
            is_valid=True,
            confidence=random.uniform(0.7, 0.95)
        )


def test_get_strategy_race_condition():
    """Test that get_strategy() properly locks metadata updates."""
    print("\n=== Testing get_strategy() Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    registry.register_strategy(TestStrategy, priority=50)
    
    # Shared state to track issues
    errors = []
    usage_counts = []
    
    def get_strategy_concurrent(thread_id):
        try:
            for _ in range(100):
                strategy = registry.get_strategy("test")
                if strategy is None:
                    errors.append(f"Thread {thread_id}: Strategy was None")
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    # Run concurrent get_strategy calls
    threads = []
    for i in range(10):
        thread = threading.Thread(target=get_strategy_concurrent, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Check results
    metadata = registry._strategies.get("test")
    expected_usage = 10 * 100  # 10 threads * 100 calls each
    
    print(f"  Expected usage count: {expected_usage}")
    print(f"  Actual usage count: {metadata.usage_count}")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print(f"  ❌ Errors occurred: {errors[:5]}...")  # Show first 5 errors
    
    assert metadata.usage_count == expected_usage, f"Usage count mismatch: {metadata.usage_count} != {expected_usage}"
    assert len(errors) == 0, f"Race condition errors occurred: {errors}"
    
    print("  ✅ get_strategy() race condition fixed!")


def test_unregister_strategy_race_condition():
    """Test that unregister_strategy() properly locks deletion."""
    print("\n=== Testing unregister_strategy() Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    
    # Register multiple strategies
    for i in range(20):
        strategy_class = type(f'TestStrategy{i}', (TestStrategy,), {
            'format_name': property(lambda self, i=i: f'test_{i}')
        })
        registry.register_strategy(strategy_class)
    
    errors = []
    successes = []
    
    def unregister_concurrent(format_name):
        try:
            result = registry.unregister_strategy(format_name)
            if result:
                successes.append(format_name)
            return result
        except Exception as e:
            errors.append((format_name, str(e)))
            return False
    
    # Concurrent unregistration
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(20):
            future = executor.submit(unregister_concurrent, f'test_{i}')
            futures.append(future)
        
        # Wait for all to complete
        for future in as_completed(futures):
            pass
    
    print(f"  Successfully unregistered: {len(successes)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Remaining strategies: {len(registry._strategies)}")
    
    assert len(errors) == 0, f"Errors during unregistration: {errors}"
    assert len(registry._strategies) == 0, f"Some strategies not unregistered: {list(registry._strategies.keys())}"
    
    print("  ✅ unregister_strategy() race condition fixed!")


def test_enable_disable_race_condition():
    """Test that enable/disable_strategy() properly lock metadata changes."""
    print("\n=== Testing enable/disable_strategy() Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    registry.register_strategy(TestStrategy)
    
    errors = []
    state_changes = []
    
    def toggle_strategy(thread_id):
        try:
            for i in range(50):
                if i % 2 == 0:
                    result = registry.disable_strategy("test")
                    state_changes.append(("disable", result))
                else:
                    result = registry.enable_strategy("test")
                    state_changes.append(("enable", result))
                # Small delay to increase chance of race
                time.sleep(0.001)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    # Run concurrent enable/disable
    threads = []
    for i in range(10):
        thread = threading.Thread(target=toggle_strategy, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print(f"  Total state changes: {len(state_changes)}")
    print(f"  Errors: {len(errors)}")
    
    # Verify final state is consistent
    metadata = registry._strategies.get("test")
    assert metadata is not None, "Strategy disappeared during toggle"
    assert isinstance(metadata.is_enabled, bool), f"is_enabled corrupted: {metadata.is_enabled}"
    assert len(errors) == 0, f"Errors occurred: {errors}"
    
    print("  ✅ enable/disable_strategy() race condition fixed!")


def test_auto_detect_format_race_condition():
    """Test that auto_detect_format() properly handles concurrent cache access."""
    print("\n=== Testing auto_detect_format() Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    
    # Register multiple strategies
    for i in range(5):
        strategy_class = type(f'Format{i}Strategy', (TestStrategy,), {
            'format_name': property(lambda self, i=i: f'format_{i}')
        })
        registry.register_strategy(strategy_class, priority=50 + i*10)
    
    errors = []
    detections = []
    
    # Test citations
    test_citations = [
        ["Author, A. (2023). Title 1. Journal."],
        ["Author, B. (2023). Title 2. Journal."],
        ["Author, C. (2023). Title 3. Journal."]
    ]
    
    def detect_concurrent(thread_id):
        try:
            for _ in range(50):
                # Randomly pick citations
                citations = random.choice(test_citations)
                result = registry.auto_detect_format(citations)
                if result:
                    detections.append((thread_id, result))
                
                # Randomly enable/disable strategies to stress test
                if random.random() < 0.1:
                    format_name = f"format_{random.randint(0, 4)}"
                    if random.random() < 0.5:
                        registry.disable_strategy(format_name)
                    else:
                        registry.enable_strategy(format_name)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    # Run concurrent detection
    threads = []
    for i in range(10):
        thread = threading.Thread(target=detect_concurrent, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print(f"  Total detections: {len(detections)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Cache stats: {registry.get_cache_stats()}")
    
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(detections) > 0, "No formats detected"
    
    print("  ✅ auto_detect_format() race condition fixed!")


def test_statistics_update_race_condition():
    """Test that statistics updates are properly synchronized."""
    print("\n=== Testing Statistics Update Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    registry.register_strategy(TestStrategy)
    
    errors = []
    
    def update_stats_concurrent(thread_id):
        try:
            for i in range(100):
                result = FormatValidationResult(
                    format_name="test",
                    is_valid=i % 2 == 0,
                    confidence=0.8
                )
                registry._update_statistics("test", result, 1.0)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    # Run concurrent statistics updates
    threads = []
    for i in range(10):
        thread = threading.Thread(target=update_stats_concurrent, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Verify statistics
    stats = registry.get_statistics()
    expected_total = 10 * 100  # 10 threads * 100 updates
    
    print(f"  Total validations: {stats['total_validations']}")
    print(f"  Expected: {expected_total}")
    print(f"  Successful: {stats['successful_validations']}")
    print(f"  Failed: {stats['failed_validations']}")
    print(f"  Errors: {len(errors)}")
    
    assert stats['total_validations'] == expected_total, f"Total mismatch: {stats['total_validations']} != {expected_total}"
    assert stats['successful_validations'] + stats['failed_validations'] == expected_total, "Success + Failed != Total"
    assert len(errors) == 0, f"Errors occurred: {errors}"
    
    print("  ✅ Statistics update race condition fixed!")


def test_reset_statistics_race_condition():
    """Test that reset_statistics() is thread-safe."""
    print("\n=== Testing reset_statistics() Race Condition Fix ===")
    
    registry = CitationFormatRegistry()
    registry.register_strategy(TestStrategy)
    
    # Populate some data
    for _ in range(10):
        registry.get_strategy("test")
    
    errors = []
    
    def reset_and_update(thread_id):
        try:
            if thread_id % 2 == 0:
                registry.reset_statistics()
            else:
                # Try to update while reset might be happening
                result = FormatValidationResult(
                    format_name="test",
                    is_valid=True,
                    confidence=0.8
                )
                registry._update_statistics("test", result, 1.0)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    # Run concurrent reset and updates
    threads = []
    for i in range(20):
        thread = threading.Thread(target=reset_and_update, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print(f"  Errors: {len(errors)}")
    
    # Verify registry is in consistent state
    stats = registry.get_statistics()
    assert isinstance(stats['total_validations'], int), "Statistics corrupted"
    assert len(errors) == 0, f"Errors occurred: {errors}"
    
    print("  ✅ reset_statistics() race condition fixed!")


def test_security_module_check():
    """Test that the strengthened _is_trusted_module() prevents bypasses."""
    print("\n=== Testing Strengthened Module Security Check ===")
    
    registry = CitationFormatRegistry()
    
    # Test cases that should be blocked
    dangerous_attempts = [
        "os",
        "sys",
        "subprocess",
        "os.path",  # Nested dangerous module
        "mymodule.os",  # Dangerous module in path
        "urllib",
        "urllib.request",
        "pickle",
        "eval",
        "exec"
    ]
    
    # Test cases that should be allowed
    safe_modules = [
        "academic_validation_framework",
        "academic_validation_framework.strategies",
        "__main__",
        "test_module",
        "tests.test_registry"
    ]
    
    # Test dangerous modules are blocked
    for module in dangerous_attempts:
        result = registry._is_trusted_module(module)
        assert not result, f"Dangerous module '{module}' was incorrectly trusted!"
        print(f"  ✅ Blocked dangerous module: {module}")
    
    # Test safe modules are allowed
    for module in safe_modules:
        result = registry._is_trusted_module(module)
        assert result, f"Safe module '{module}' was incorrectly blocked!"
        print(f"  ✅ Allowed safe module: {module}")
    
    # Test that prefix matching doesn't allow bypasses
    bypass_attempts = [
        "academic_validation_frameworkos",  # Trying to append dangerous module
        "osacademic_validation_framework",  # Prepending dangerous module
    ]
    
    for module in bypass_attempts:
        result = registry._is_trusted_module(module)
        assert not result, f"Bypass attempt '{module}' was incorrectly trusted!"
        print(f"  ✅ Blocked bypass attempt: {module}")
    
    print("  ✅ Module security check properly strengthened!")


def main():
    """Run all race condition tests."""
    print("=" * 60)
    print("RACE CONDITION FIX VERIFICATION TEST SUITE")
    print("=" * 60)
    
    try:
        test_get_strategy_race_condition()
        test_unregister_strategy_race_condition()
        test_enable_disable_race_condition()
        test_auto_detect_format_race_condition()
        test_statistics_update_race_condition()
        test_reset_statistics_race_condition()
        test_security_module_check()
        
        print("\n" + "=" * 60)
        print("✅ ALL RACE CONDITION FIXES VERIFIED!")
        print("=" * 60)
        
        print("\nSummary of fixes verified:")
        print("  ✅ get_strategy() properly locks metadata updates")
        print("  ✅ unregister_strategy() uses _strategy_lock for deletion")
        print("  ✅ enable/disable_strategy() lock metadata modifications")
        print("  ✅ auto_detect_format() handles concurrent cache access safely")
        print("  ✅ Statistics updates are properly synchronized")
        print("  ✅ reset_statistics() is thread-safe")
        print("  ✅ Module security check prevents bypass attempts")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)