"""
Test cases for ProjectVersionManager
Tests version management functionality in isolation
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from project_version_manager import ProjectVersionManager, ProjectVersion


class TestProjectVersionManager(unittest.TestCase):
    """Test cases for ProjectVersionManager"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.version_manager = ProjectVersionManager()
        self.project_id = "test_project_123"
        self.user_id = "test_user"
    
    def test_create_version_returns_id(self):
        """Test that create_version returns a version ID"""
        version_id = self.version_manager.create_version(
            self.project_id, "Test version", self.user_id
        )
        self.assertIsInstance(version_id, str)
        self.assertTrue(len(version_id) > 0)
    
    def test_create_version_stores_version(self):
        """Test that create_version stores the version correctly"""
        description = "Test version"
        version_id = self.version_manager.create_version(
            self.project_id, description, self.user_id
        )
        
        version = self.version_manager.get_version(version_id)
        self.assertIsNotNone(version)
        self.assertEqual(version.project_id, self.project_id)
        self.assertEqual(version.description, description)
        self.assertEqual(version.created_by, self.user_id)
        self.assertEqual(version.version_number, 1)
    
    def test_create_multiple_versions_increments_number(self):
        """Test that version numbers increment correctly"""
        version1_id = self.version_manager.create_version(
            self.project_id, "Version 1", self.user_id
        )
        version2_id = self.version_manager.create_version(
            self.project_id, "Version 2", self.user_id
        )
        
        version1 = self.version_manager.get_version(version1_id)
        version2 = self.version_manager.get_version(version2_id)
        
        self.assertEqual(version1.version_number, 1)
        self.assertEqual(version2.version_number, 2)
    
    def test_get_project_versions_returns_all_versions(self):
        """Test that get_project_versions returns all versions for a project"""
        # Create versions for different projects
        version1_id = self.version_manager.create_version(
            self.project_id, "Version 1", self.user_id
        )
        version2_id = self.version_manager.create_version(
            self.project_id, "Version 2", self.user_id
        )
        other_project_version = self.version_manager.create_version(
            "other_project", "Other version", self.user_id
        )
        
        project_versions = self.version_manager.get_project_versions(self.project_id)
        
        self.assertEqual(len(project_versions), 2)
        version_ids = [v.id for v in project_versions]
        self.assertIn(version1_id, version_ids)
        self.assertIn(version2_id, version_ids)
        self.assertNotIn(other_project_version, version_ids)
    
    def test_compare_versions_returns_comparison(self):
        """Test that compare_versions returns comparison data"""
        version1_id = self.version_manager.create_version(
            self.project_id, "Version 1", self.user_id
        )
        version2_id = self.version_manager.create_version(
            self.project_id, "Version 2", self.user_id
        )
        
        comparison = self.version_manager.compare_versions(
            self.project_id, version1_id, version2_id
        )
        
        self.assertIn("version1", comparison)
        self.assertIn("version2", comparison)
        self.assertIn("differences", comparison)
        self.assertEqual(comparison["version1"]["description"], "Version 1")
        self.assertEqual(comparison["version2"]["description"], "Version 2")
    
    def test_compare_versions_with_invalid_versions(self):
        """Test that compare_versions handles invalid version IDs"""
        comparison = self.version_manager.compare_versions(
            self.project_id, "invalid_id", "another_invalid_id"
        )
        
        self.assertEqual(comparison, {})
    
    def test_rollback_to_version_sets_current(self):
        """Test that rollback_to_version sets the current version"""
        version1_id = self.version_manager.create_version(
            self.project_id, "Version 1", self.user_id
        )
        version2_id = self.version_manager.create_version(
            self.project_id, "Version 2", self.user_id
        )
        
        # Version 2 should be current after creation
        self.assertEqual(
            self.version_manager.get_current_version(self.project_id),
            version2_id
        )
        
        # Rollback to version 1
        self.version_manager.rollback_to_version(self.project_id, version1_id)
        
        # Version 1 should now be current
        self.assertEqual(
            self.version_manager.get_current_version(self.project_id),
            version1_id
        )
    
    def test_rollback_to_invalid_version_does_nothing(self):
        """Test that rollback to invalid version doesn't change current version"""
        version_id = self.version_manager.create_version(
            self.project_id, "Version 1", self.user_id
        )
        
        original_current = self.version_manager.get_current_version(self.project_id)
        
        # Try to rollback to invalid version
        self.version_manager.rollback_to_version(self.project_id, "invalid_id")
        
        # Current version should remain unchanged
        self.assertEqual(
            self.version_manager.get_current_version(self.project_id),
            original_current
        )
    
    def test_get_current_version_returns_empty_for_unknown_project(self):
        """Test that get_current_version returns empty string for unknown project"""
        current_version = self.version_manager.get_current_version("unknown_project")
        self.assertEqual(current_version, "")
    
    def test_thread_safety(self):
        """Test that version operations are thread-safe"""
        import threading
        import time
        
        results = []
        
        def create_version_worker(worker_id):
            version_id = self.version_manager.create_version(
                self.project_id, f"Version {worker_id}", f"user_{worker_id}"
            )
            results.append(version_id)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_version_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all versions were created
        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10)  # All IDs should be unique
        
        # Verify version numbers are correct
        versions = self.version_manager.get_project_versions(self.project_id)
        self.assertEqual(len(versions), 10)
        version_numbers = [v.version_number for v in versions]
        self.assertEqual(sorted(version_numbers), list(range(1, 11)))


if __name__ == "__main__":
    unittest.main()