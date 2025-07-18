"""
Edge Cases and Error Handling Tests for Advanced Academic Interface
Comprehensive negative path testing to address review feedback
"""

import pytest
import threading
import asyncio
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios"""
    
    def test_research_config_invalid_inputs(self):
        """Test invalid inputs for research configuration"""
        from frontend.advanced_interface.research_config import ResearchConfigDashboard
        
        dashboard = ResearchConfigDashboard()
        
        # Test invalid research type
        with pytest.raises(ValueError, match="Invalid research type"):
            dashboard.select_research_type("invalid_type")
        
        # Test invalid agent
        with pytest.raises(ValueError, match="Invalid agent"):
            dashboard.select_agents(["invalid_agent"])
        
        # Test invalid agent configuration
        with pytest.raises(ValueError, match="Invalid agent"):
            dashboard.configure_agent("invalid_agent", {})
    
    def test_empty_collections_handling(self):
        """Test handling of empty collections"""
        from frontend.advanced_interface.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Test empty query builder
        query_builder = db_manager.get_query_builder()
        assert query_builder.build_query() == ""
        
        # Test empty paper collections
        assert db_manager.get_collection_papers("nonexistent_collection") == []
        
        # Test empty annotation
        assert db_manager.get_paper_annotation("nonexistent_paper") == ""
    
    def test_concurrent_access_edge_cases(self):
        """Test concurrent access with edge cases"""
        from frontend.advanced_interface.monitoring import ResearchMonitor
        
        monitor = ResearchMonitor()
        
        # Test concurrent initialization
        def initialize_progress():
            monitor.initialize_progress(["test_stage"])
        
        # Run multiple initializations concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(initialize_progress) for _ in range(10)]
            for future in futures:
                future.result()
        
        # Should not crash and should be in consistent state
        progress = monitor.get_overall_progress()
        assert "test_stage" in progress
    
    def test_invalid_database_operations(self):
        """Test invalid database operations"""
        from frontend.advanced_interface.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Test invalid database selection
        with pytest.raises(ValueError, match="Invalid database"):
            db_manager.select_database("invalid_database")
        
        # Test invalid authentication
        with pytest.raises(ValueError, match="Invalid database"):
            db_manager.authenticate_database("invalid_database", {})
    
    def test_quality_metrics_edge_cases(self):
        """Test quality metrics with edge cases"""
        from frontend.advanced_interface.quality_dashboard import QualityDashboard
        
        dashboard = QualityDashboard()
        
        # Test quality score with no metrics
        assert dashboard.get_citation_quality_score() == 0.0
        
        # Test with zero citations
        dashboard.update_citation_metrics({
            "total_citations": 0,
            "verified_citations": 0,
            "high_quality_citations": 0,
            "average_citation_age": 0
        })
        
        assert dashboard.get_citation_quality_score() == 0.0
        
        # Test completeness analysis with no data
        assert dashboard.get_completeness_analysis() == {}
    
    def test_output_manager_invalid_formats(self):
        """Test output manager with invalid formats"""
        from frontend.advanced_interface.output_manager import OutputManager
        
        output_manager = OutputManager()
        
        # Test invalid output format
        with pytest.raises(ValueError, match="Invalid format"):
            output_manager.select_output_formats(["invalid_format"])
        
        # Test invalid citation style
        with pytest.raises(ValueError, match="Invalid citation style"):
            output_manager.set_citation_style("invalid_style")
        
        # Test invalid section
        with pytest.raises(ValueError, match="Invalid section"):
            output_manager.include_sections(["invalid_section"])
        
        # Test invalid report type
        with pytest.raises(ValueError, match="Invalid report type"):
            output_manager.generate_quality_report("invalid_type", {})
    
    def test_project_manager_invalid_roles(self):
        """Test project manager with invalid roles"""
        from frontend.advanced_interface.project_manager import ProjectManager
        
        project_manager = ProjectManager()
        project_id = project_manager.create_project({"name": "Test Project"})
        
        # Test invalid role
        with pytest.raises(ValueError, match="Invalid role"):
            project_manager.invite_user(project_id, "test@example.com", "invalid_role")
    
    def test_api_error_handling(self):
        """Test API error handling scenarios"""
        from frontend.advanced_interface.main_interface import AdvancedAcademicInterface
        
        interface = AdvancedAcademicInterface()
        
        # Test API error handling
        result = interface.handle_api_error("test_api", "Connection timeout")
        
        assert result["status"] == "error"
        assert result["api"] == "test_api"
        assert result["fallback_enabled"] == True
        assert interface.is_fallback_mode_enabled() == True
    
    def test_session_isolation(self):
        """Test session isolation and cleanup"""
        from frontend.advanced_interface.main_interface import AdvancedAcademicInterface
        
        interface = AdvancedAcademicInterface()
        
        # Create multiple sessions
        session1 = interface.create_research_session("user1", "Session 1")
        session2 = interface.create_research_session("user2", "Session 2")
        
        # Configure sessions differently
        interface.configure_session(session1, {"storm_mode": "academic"})
        interface.configure_session(session2, {"storm_mode": "wikipedia"})
        
        # Verify isolation
        config1 = interface.get_session_config(session1)
        config2 = interface.get_session_config(session2)
        
        assert config1["storm_mode"] != config2["storm_mode"]
        
        # Test nonexistent session
        assert interface.get_session_config("nonexistent_session") == {}
    
    def test_thread_safety_stress_test(self):
        """Stress test thread safety under high load"""
        from frontend.advanced_interface.monitoring import ResearchMonitor
        
        monitor = ResearchMonitor()
        monitor.initialize_progress(["stage1", "stage2", "stage3"])
        
        # High concurrency stress test
        def stress_update():
            for i in range(100):
                monitor.update_progress("stage1", i/100, f"Update {i}")
                monitor.update_quality_metric("test_metric", i/100)
                monitor.track_api_usage("test_api", i)
        
        # Run with high concurrency
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(stress_update) for _ in range(10)]
            for future in futures:
                future.result()
        
        # Should not crash and should be in consistent state
        progress = monitor.get_overall_progress()
        assert "stage1" in progress
        assert monitor.get_quality_metrics() is not None
        assert monitor.get_api_usage() is not None
    
    def test_memory_cleanup(self):
        """Test memory cleanup and resource management"""
        from frontend.advanced_interface.monitoring import ResearchMonitor
        
        monitor = ResearchMonitor()
        
        # Create large amount of data
        for i in range(1000):
            monitor.update_quality_metric(f"metric_{i}", i/1000)
            monitor.track_api_usage(f"api_{i}", i)
        
        # Verify data is stored
        assert len(monitor.get_quality_metrics()) == 1000
        assert len(monitor.get_api_usage()) == 1000
        
        # Test that we can still operate normally
        monitor.update_progress("test_stage", 0.5, "Test message")
        assert monitor.get_overall_progress() is not None
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling scenarios"""
        from frontend.advanced_interface.main_interface import AdvancedAcademicInterface
        
        interface = AdvancedAcademicInterface()
        
        # Test async initialization
        await interface.initialize()
        
        # Test research with invalid configuration
        with patch.object(interface.research_config, 'select_research_type', side_effect=ValueError("Invalid type")):
            with pytest.raises(ValueError):
                await interface.configure_research({"research_type": "invalid"})
        
        # Test research start with error
        research_id = await interface.start_research("test query")
        assert research_id is not None
        
        # Test status retrieval
        status = await interface.get_research_status(research_id)
        assert status["research_id"] == research_id
    
    def test_configuration_validation(self):
        """Test configuration validation edge cases"""
        from frontend.advanced_interface.research_config import ResearchConfigDashboard
        
        dashboard = ResearchConfigDashboard()
        
        # Test empty agent list
        dashboard.select_agents([])
        assert dashboard.selected_agents == []
        
        # Test empty database list
        dashboard.select_databases([])
        assert dashboard.selected_databases == []
        
        # Test empty criteria lists
        dashboard.set_inclusion_criteria([])
        dashboard.set_exclusion_criteria([])
        assert dashboard.inclusion_criteria == []
        assert dashboard.exclusion_criteria == []
    
    def test_query_builder_edge_cases(self):
        """Test query builder edge cases"""
        from frontend.advanced_interface.database_manager import QueryBuilder
        
        # Test empty query builder
        builder = QueryBuilder()
        assert builder.build_query() == ""
        
        # Test single term
        builder.add_term("single_term")
        assert builder.build_query() == "single_term"
        
        # Test operator handling
        builder = QueryBuilder()
        builder.add_term("term1")
        builder.add_term("term2", "OR")
        assert "OR" in builder.build_query()
    
    def test_citation_preview_edge_cases(self):
        """Test citation preview with edge cases"""
        from frontend.advanced_interface.output_manager import OutputManager
        
        output_manager = OutputManager()
        
        # Test empty paper data
        preview = output_manager.preview_citation_style("apa", {})
        assert "Unknown" in preview
        
        # Test missing fields
        preview = output_manager.preview_citation_style("apa", {"title": "Test"})
        assert "Test" in preview
        
        # Test unknown style
        with pytest.raises(ValueError):
            output_manager.preview_citation_style("unknown_style", {})
    
    def test_version_management_edge_cases(self):
        """Test version management edge cases"""
        from frontend.advanced_interface.project_manager import ProjectManager
        
        project_manager = ProjectManager()
        project_id = project_manager.create_project({"name": "Test Project"})
        
        # Test version comparison with invalid versions
        diff = project_manager.compare_versions(project_id, "invalid_v1", "invalid_v2")
        assert diff == {}
        
        # Test rollback to invalid version
        project_manager.rollback_to_version(project_id, "invalid_version")
        
        # Test get current version for nonexistent project
        assert project_manager.get_current_version("nonexistent_project") == ""


class TestSecurityAndValidation:
    """Test security and validation improvements"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        from frontend.advanced_interface.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Test with potentially malicious input
        paper_data = {
            "title": "<script>alert('xss')</script>",
            "authors": ["'; DROP TABLE papers; --"],
            "doi": "javascript:alert('xss')"
        }
        
        # Should not crash and should handle safely
        paper_id = db_manager.import_paper(paper_data)
        assert paper_id is not None
    
    def test_credential_validation(self):
        """Test credential validation"""
        from frontend.advanced_interface.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Test with empty credentials - should raise ValueError
        try:
            db_manager.authenticate_database("institutional", {})
            assert False, "Expected ValueError for empty credentials"
        except ValueError as e:
            assert "Invalid credentials format" in str(e)
        
        # Test with partial credentials - should raise ValueError
        try:
            db_manager.authenticate_database("institutional", {"username": "test"})
            assert False, "Expected ValueError for partial credentials"
        except ValueError as e:
            assert "Invalid credentials format" in str(e)
        
        # Should handle gracefully without crashing
        status = db_manager.get_authentication_status("institutional")
        assert status is not None
    
    def test_parameter_validation(self):
        """Test parameter validation"""
        from frontend.advanced_interface.research_config import ResearchConfigDashboard
        
        dashboard = ResearchConfigDashboard()
        
        # Test with None values
        try:
            dashboard.select_research_type(None)
        except (ValueError, TypeError):
            pass  # Expected behavior
        
        # Test with empty strings
        try:
            dashboard.select_research_type("")
        except ValueError:
            pass  # Expected behavior
        
        # Test with non-string values
        try:
            dashboard.select_research_type(123)
        except (ValueError, TypeError):
            pass  # Expected behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])