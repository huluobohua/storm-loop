"""
Test cases for refactored AdvancedAcademicInterface
Tests the simplified facade with dependency injection and delegation
"""

import unittest
import asyncio
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'frontend'))
from advanced_interface.main_interface import AdvancedAcademicInterface
from advanced_interface.research_session_manager import ResearchSessionManager
from advanced_interface.error_handling_service import ErrorHandlingService


class TestRefactoredAdvancedAcademicInterface(unittest.TestCase):
    """Test cases for refactored AdvancedAcademicInterface"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.mock_session_manager = Mock(spec=ResearchSessionManager)
        self.mock_error_service = Mock(spec=ErrorHandlingService)
        
        # Create interface with mocked dependencies
        self.interface = AdvancedAcademicInterface(
            session_manager=self.mock_session_manager,
            error_service=self.mock_error_service
        )
    
    def test_init_with_dependency_injection(self):
        """Test that interface properly injects dependencies"""
        self.assertIs(self.interface.session_manager, self.mock_session_manager)
        self.assertIs(self.interface.error_service, self.mock_error_service)
        
        # Other components should be created if not provided
        self.assertIsNotNone(self.interface.database_manager)
        self.assertIsNotNone(self.interface.project_manager)
        self.assertIsNotNone(self.interface.quality_dashboard)
        self.assertIsNotNone(self.interface.process_orchestrator)
    
    def test_init_without_dependencies(self):
        """Test interface creates default dependencies when none provided"""
        interface = AdvancedAcademicInterface()
        
        self.assertIsNotNone(interface.session_manager)
        self.assertIsNotNone(interface.error_service)
        self.assertIsNotNone(interface.database_manager)
        self.assertIsNotNone(interface.project_manager)
        self.assertIsNotNone(interface.quality_dashboard)
        self.assertIsNotNone(interface.process_orchestrator)
    
    def test_session_management_delegation(self):
        """Test that session management is properly delegated"""
        # Mock return values
        self.mock_session_manager.create_session.return_value = "session_123"
        self.mock_session_manager.get_session_config.return_value = {"test": "config"}
        
        # Test delegation
        session_id = self.interface.create_research_session("user_123", "Test Session")
        self.assertEqual(session_id, "session_123")
        self.mock_session_manager.create_session.assert_called_once_with("user_123", "Test Session")
        
        config = self.interface.get_session_config("session_123")
        self.assertEqual(config, {"test": "config"})
        self.mock_session_manager.get_session_config.assert_called_once_with("session_123")
        
        self.interface.configure_session("session_123", {"new": "config"})
        self.mock_session_manager.configure_session.assert_called_once_with("session_123", {"new": "config"})
    
    def test_error_handling_delegation(self):
        """Test that error handling is properly delegated"""
        # Mock return values
        self.mock_error_service.handle_api_error.return_value = {"status": "error"}
        self.mock_error_service.is_fallback_mode_enabled.return_value = True
        
        # Test delegation
        error_response = self.interface.handle_api_error("test_api", "test error")
        self.assertEqual(error_response, {"status": "error"})
        self.mock_error_service.handle_api_error.assert_called_once_with("test_api", "test error")
        
        self.interface.enable_fallback_mode()
        self.mock_error_service.enable_fallback_mode.assert_called_once()
        
        self.interface.disable_fallback_mode()
        self.mock_error_service.disable_fallback_mode.assert_called_once()
        
        fallback_status = self.interface.is_fallback_mode_enabled()
        self.assertTrue(fallback_status)
        self.mock_error_service.is_fallback_mode_enabled.assert_called_once()
    
    async def test_research_process_delegation(self):
        """Test that research processes are properly delegated to orchestrator"""
        # Test start research
        research_id = await self.interface.start_research("test query")
        self.assertIsInstance(research_id, str)
        self.assertTrue(len(research_id) > 0)
        
        # Test get research status  
        status = await self.interface.get_research_status(research_id)
        self.assertIn("research_id", status)
        self.assertIn("status", status)
        
        # Test generate output
        output_result = await self.interface.generate_output(research_id, ["pdf", "html"])
        self.assertIn("research_id", output_result)
        self.assertIn("formats", output_result)
    
    def test_all_methods_are_delegations(self):
        """Verify that all public methods are simple delegations (≤5 lines)"""
        import inspect
        
        public_methods = [method for method in dir(AdvancedAcademicInterface) 
                         if not method.startswith('_') and callable(getattr(AdvancedAcademicInterface, method))]
        
        for method_name in public_methods:
            method = getattr(AdvancedAcademicInterface, method_name)
            if hasattr(method, '__func__'):
                try:
                    source_lines = inspect.getsourcelines(method)[0]
                    # Count only code lines (not comments/docstrings)
                    code_lines = [line.strip() for line in source_lines 
                                 if line.strip() and not line.strip().startswith('#') 
                                 and not line.strip().startswith('"""') 
                                 and '"""' not in line.strip()]
                    
                    # Should be simple delegation (≤5 lines)
                    self.assertLessEqual(len(code_lines), 5, 
                                       f"Method {method_name} has {len(code_lines)} lines, should be ≤5")
                except OSError:
                    # Skip built-in methods
                    pass
    
    def test_interface_maintains_backwards_compatibility(self):
        """Test that the refactored interface maintains the same public API"""
        # Create interface with real dependencies to test full functionality
        interface = AdvancedAcademicInterface()
        
        # Test session methods exist and work
        session_id = interface.create_research_session("test_user", "test_session")
        self.assertIsInstance(session_id, str)
        
        interface.configure_session(session_id, {"test": "config"})
        config = interface.get_session_config(session_id)
        self.assertEqual(config.get("test"), "config")
        
        # Test error handling methods exist and work
        error_response = interface.handle_api_error("test_api", "test error")
        self.assertEqual(error_response["status"], "error")
        
        interface.enable_fallback_mode()
        self.assertTrue(interface.is_fallback_mode_enabled())
        
        interface.disable_fallback_mode()
        self.assertFalse(interface.is_fallback_mode_enabled())
    
    def test_async_methods_work_correctly(self):
        """Test that async methods work correctly after refactoring"""
        async def run_async_tests():
            interface = AdvancedAcademicInterface()
            
            # Test async research methods
            research_id = await interface.start_research("test query")
            self.assertIsInstance(research_id, str)
            
            status = await interface.get_research_status(research_id)
            self.assertIn("research_id", status)
            
            output = await interface.generate_output(research_id, ["pdf"])
            self.assertIn("research_id", output)
            
            # Test async configuration
            await interface.configure_research({"test_config": "value"})
        
        # Run the async test
        asyncio.run(run_async_tests())
    
    def test_class_size_meets_requirements(self):
        """Test that the refactored interface meets size requirements"""
        import inspect
        
        lines = inspect.getsourcelines(AdvancedAcademicInterface)[0]
        line_count = len(lines)
        
        # Should be significantly smaller than original (was 203 lines)
        self.assertLess(line_count, 100, f"Interface should be <100 lines, got {line_count}")
        
        # Should be primarily delegation methods
        method_count = len([line for line in lines if line.strip().startswith('def ') 
                           and not line.strip().startswith('def __')])
        
        # Should have reasonable method density
        self.assertGreater(method_count, 5, 
                          "Interface should have multiple public methods")


if __name__ == "__main__":
    unittest.main()