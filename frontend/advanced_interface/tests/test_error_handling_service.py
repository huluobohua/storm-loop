"""
Test cases for ErrorHandlingService
Tests error handling and fallback mode functionality
"""

import unittest
import threading
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from error_handling_service import ErrorHandlingService


class TestErrorHandlingService(unittest.TestCase):
    """Test cases for ErrorHandlingService"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.error_service = ErrorHandlingService()
    
    def test_initial_state(self):
        """Test initial state of error service"""
        self.assertFalse(self.error_service.is_fallback_mode_enabled())
    
    def test_enable_fallback_mode(self):
        """Test enabling fallback mode"""
        self.error_service.enable_fallback_mode()
        self.assertTrue(self.error_service.is_fallback_mode_enabled())
    
    def test_disable_fallback_mode(self):
        """Test disabling fallback mode"""
        self.error_service.enable_fallback_mode()
        self.assertTrue(self.error_service.is_fallback_mode_enabled())
        
        self.error_service.disable_fallback_mode()
        self.assertFalse(self.error_service.is_fallback_mode_enabled())
    
    def test_handle_api_error_structure(self):
        """Test API error handling returns correct structure"""
        api_name = "test_api"
        error_message = "Connection failed"
        
        result = self.error_service.handle_api_error(api_name, error_message)
        
        # Verify response structure
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["api"], api_name)
        self.assertEqual(result["error"], error_message)
        self.assertTrue(result["fallback_enabled"])
        self.assertIn("message", result)
        self.assertIn(api_name, result["message"])
    
    def test_handle_api_error_enables_fallback(self):
        """Test that handling API error enables fallback mode"""
        self.assertFalse(self.error_service.is_fallback_mode_enabled())
        
        self.error_service.handle_api_error("test_api", "test error")
        
        self.assertTrue(self.error_service.is_fallback_mode_enabled())
    
    def test_error_message_formatting(self):
        """Test error message is formatted correctly"""
        api_name = "authentication_service"
        error_message = "Token expired"
        
        result = self.error_service.handle_api_error(api_name, error_message)
        
        expected_message = f"API {api_name} error handled, fallback mode enabled"
        self.assertEqual(result["message"], expected_message)
    
    def test_multiple_api_errors(self):
        """Test handling multiple API errors"""
        apis = ["auth_api", "data_api", "storage_api"]
        errors = ["auth failed", "data corrupted", "storage full"]
        
        results = []
        for api, error in zip(apis, errors):
            result = self.error_service.handle_api_error(api, error)
            results.append(result)
        
        # Verify all errors were handled correctly
        for i, result in enumerate(results):
            self.assertEqual(result["api"], apis[i])
            self.assertEqual(result["error"], errors[i])
            self.assertEqual(result["status"], "error")
        
        # Fallback mode should still be enabled
        self.assertTrue(self.error_service.is_fallback_mode_enabled())
    
    def test_thread_safety_fallback_toggle(self):
        """Test that fallback mode toggling is thread-safe"""
        results = []
        
        def toggle_fallback_worker(worker_id):
            if worker_id % 2 == 0:
                self.error_service.enable_fallback_mode()
                results.append(('enable', worker_id))
            else:
                self.error_service.disable_fallback_mode()
                results.append(('disable', worker_id))
        
        # Create multiple threads toggling fallback mode
        threads = []
        for i in range(10):
            thread = threading.Thread(target=toggle_fallback_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        self.assertEqual(len(results), 10)
        
        # Final state should be consistent
        final_state = self.error_service.is_fallback_mode_enabled()
        self.assertIsInstance(final_state, bool)
    
    def test_thread_safety_error_handling(self):
        """Test that error handling is thread-safe"""
        results = []
        
        def handle_error_worker(worker_id):
            api_name = f"api_{worker_id}"
            error_message = f"error_{worker_id}"
            result = self.error_service.handle_api_error(api_name, error_message)
            results.append(result)
        
        # Create multiple threads handling errors
        threads = []
        for i in range(5):
            thread = threading.Thread(target=handle_error_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all errors were handled
        self.assertEqual(len(results), 5)
        
        # Verify each result is correctly formatted
        for i, result in enumerate(results):
            self.assertEqual(result["api"], f"api_{i}")
            self.assertEqual(result["error"], f"error_{i}")
            self.assertEqual(result["status"], "error")
            self.assertTrue(result["fallback_enabled"])
        
        # Fallback mode should be enabled after any error
        self.assertTrue(self.error_service.is_fallback_mode_enabled())
    
    def test_edge_cases(self):
        """Test edge cases for error handling"""
        # Empty strings
        result = self.error_service.handle_api_error("", "")
        self.assertEqual(result["api"], "")
        self.assertEqual(result["error"], "")
        self.assertEqual(result["status"], "error")
        
        # Special characters
        result = self.error_service.handle_api_error("api@#$", "error with spaces & symbols!")
        self.assertEqual(result["api"], "api@#$")
        self.assertEqual(result["error"], "error with spaces & symbols!")
        
        # Very long strings
        long_api = "a" * 1000
        long_error = "b" * 1000
        result = self.error_service.handle_api_error(long_api, long_error)
        self.assertEqual(result["api"], long_api)
        self.assertEqual(result["error"], long_error)


if __name__ == "__main__":
    unittest.main()