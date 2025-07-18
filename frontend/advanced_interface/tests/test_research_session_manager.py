"""
Test cases for ResearchSessionManager
Tests session management functionality in isolation
"""

import unittest
import threading
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from research_session_manager import ResearchSessionManager


class TestResearchSessionManager(unittest.TestCase):
    """Test cases for ResearchSessionManager"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.session_manager = ResearchSessionManager()
        self.user_id = "test_user_123"
        self.session_name = "Test Session"
    
    def test_create_session_returns_id(self):
        """Test that create_session returns a session ID"""
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        self.assertIsInstance(session_id, str)
        self.assertTrue(len(session_id) > 0)
    
    def test_create_session_stores_data(self):
        """Test that create_session stores session data correctly"""
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        
        session_data = self.session_manager.get_session_data(session_id)
        self.assertEqual(session_data['user_id'], self.user_id)
        self.assertEqual(session_data['session_name'], self.session_name)
        self.assertTrue(session_data['active'])
        self.assertIn('created_at', session_data)
    
    def test_session_exists(self):
        """Test session_exists functionality"""
        # Non-existent session
        self.assertFalse(self.session_manager.session_exists("non_existent_id"))
        
        # Create session and test it exists
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        self.assertTrue(self.session_manager.session_exists(session_id))
    
    def test_get_session_config_default(self):
        """Test that sessions get default configuration"""
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        
        config = self.session_manager.get_session_config(session_id)
        self.assertEqual(config['storm_mode'], 'hybrid')
        self.assertEqual(config['agents'], ['academic_researcher'])
        self.assertEqual(config['databases'], ['openalex'])
    
    def test_configure_session(self):
        """Test session configuration updates"""
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        
        new_config = {
            'storm_mode': 'academic',
            'agents': ['researcher', 'critic'],
            'custom_setting': 'value'
        }
        
        self.session_manager.configure_session(session_id, new_config)
        
        updated_config = self.session_manager.get_session_config(session_id)
        self.assertEqual(updated_config['storm_mode'], 'academic')
        self.assertEqual(updated_config['agents'], ['researcher', 'critic'])
        self.assertEqual(updated_config['custom_setting'], 'value')
        # Default databases should still be there
        self.assertEqual(updated_config['databases'], ['openalex'])
    
    def test_configure_nonexistent_session(self):
        """Test configuring a non-existent session does nothing"""
        self.session_manager.configure_session("non_existent", {"test": "value"})
        # Should not raise an exception
        config = self.session_manager.get_session_config("non_existent")
        self.assertEqual(config, {})
    
    def test_get_nonexistent_session_data(self):
        """Test getting data for non-existent session returns empty dict"""
        session_data = self.session_manager.get_session_data("non_existent")
        self.assertEqual(session_data, {})
    
    def test_get_nonexistent_session_config(self):
        """Test getting config for non-existent session returns empty dict"""
        config = self.session_manager.get_session_config("non_existent")
        self.assertEqual(config, {})
    
    def test_thread_safety_session_creation(self):
        """Test that session creation is thread-safe"""
        results = []
        
        def create_session_worker(worker_id):
            session_id = self.session_manager.create_session(
                f"user_{worker_id}", f"Session {worker_id}"
            )
            results.append(session_id)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all sessions were created uniquely
        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10)  # All IDs should be unique
        
        # Verify all sessions exist
        for session_id in results:
            self.assertTrue(self.session_manager.session_exists(session_id))
    
    def test_thread_safety_session_configuration(self):
        """Test that session configuration is thread-safe"""
        session_id = self.session_manager.create_session(self.user_id, self.session_name)
        
        def configure_session_worker(worker_id):
            config = {f"setting_{worker_id}": f"value_{worker_id}"}
            self.session_manager.configure_session(session_id, config)
        
        # Create multiple threads updating the same session
        threads = []
        for i in range(5):
            thread = threading.Thread(target=configure_session_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify configuration contains settings from all threads
        final_config = self.session_manager.get_session_config(session_id)
        for i in range(5):
            self.assertIn(f"setting_{i}", final_config)
            self.assertEqual(final_config[f"setting_{i}"], f"value_{i}")


if __name__ == "__main__":
    unittest.main()