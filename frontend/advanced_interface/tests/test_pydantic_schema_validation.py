"""
Test cases for Pydantic Schema Validation
Tests configuration validation using Pydantic schemas
"""

import unittest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'frontend'))

# Set development environment for testing
os.environ['ENVIRONMENT'] = 'development'

from advanced_interface.schemas import ResearchConfigSchema, SessionConfigSchema
from advanced_interface.main_interface import AdvancedAcademicInterface
from pydantic import ValidationError


class TestPydanticSchemaValidation(unittest.TestCase):
    """Test cases for Pydantic schema validation"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.interface = AdvancedAcademicInterface()
    
    def test_research_config_schema_valid_minimal(self):
        """Test that minimal valid config passes validation"""
        config = {}  # Should use all defaults
        
        validated = ResearchConfigSchema(**config)
        
        # Check defaults were applied
        self.assertEqual(validated.storm_mode, "hybrid")
        self.assertEqual(validated.agents, ["academic_researcher"])
        self.assertEqual(validated.databases, ["openalex"])
        self.assertEqual(validated.max_papers, 50)
    
    def test_research_config_schema_valid_complete(self):
        """Test that complete valid config passes validation"""
        config = {
            "storm_mode": "academic",
            "agents": ["researcher", "critic"],
            "databases": ["openalex", "crossref"],
            "output_formats": ["pdf", "html"],
            "max_papers": 100,
            "quality_threshold": 0.8,
            "citation_style": "mla",
            "include_abstracts": True,
            "language": "en",
            "timeout_minutes": 45
        }
        
        validated = ResearchConfigSchema(**config)
        
        # Check values were preserved
        self.assertEqual(validated.storm_mode, "academic")
        self.assertEqual(validated.agents, ["researcher", "critic"])
        self.assertEqual(validated.max_papers, 100)
        self.assertEqual(validated.citation_style, "mla")
    
    def test_research_config_schema_invalid_storm_mode(self):
        """Test that invalid storm mode raises validation error"""
        config = {"storm_mode": "invalid_mode"}
        
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config)
        
        self.assertIn("storm_mode", str(context.exception))
    
    def test_research_config_schema_invalid_max_papers(self):
        """Test that invalid max_papers values raise validation error"""
        # Too low
        config1 = {"max_papers": 0}
        with self.assertRaises(ValidationError):
            ResearchConfigSchema(**config1)
        
        # Too high
        config2 = {"max_papers": 2000}
        with self.assertRaises(ValidationError):
            ResearchConfigSchema(**config2)
    
    def test_research_config_schema_invalid_quality_threshold(self):
        """Test that invalid quality threshold raises validation error"""
        # Below 0
        config1 = {"quality_threshold": -0.1}
        with self.assertRaises(ValidationError):
            ResearchConfigSchema(**config1)
        
        # Above 1
        config2 = {"quality_threshold": 1.5}
        with self.assertRaises(ValidationError):
            ResearchConfigSchema(**config2)
    
    def test_research_config_schema_invalid_citation_style(self):
        """Test that invalid citation style raises validation error"""
        config = {"citation_style": "invalid_style"}
        
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config)
        
        self.assertIn("Citation style must be one of", str(context.exception))
    
    def test_research_config_schema_consistency_validation(self):
        """Test cross-field validation rules"""
        # Fast mode with too many agents
        config1 = {
            "storm_mode": "fast",
            "agents": ["researcher", "critic", "synthesizer"]  # 3 agents
        }
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config1)
        
        self.assertIn("Fast mode supports maximum 2 agents", str(context.exception))
        
        # Thorough mode with too few papers
        config2 = {
            "storm_mode": "thorough",
            "max_papers": 10  # Less than 20
        }
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config2)
        
        self.assertIn("Thorough mode requires at least 20 papers", str(context.exception))
    
    def test_research_config_schema_forbids_extra_fields(self):
        """Test that extra fields are rejected"""
        config = {
            "storm_mode": "hybrid",
            "unknown_field": "should_be_rejected"
        }
        
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config)
        
        self.assertIn("extra fields not permitted", str(context.exception))
    
    def test_session_config_schema_valid(self):
        """Test that valid session config passes validation"""
        config = {
            "session_name": "Test Research Session",
            "user_id": "user123",
            "research_config": {
                "storm_mode": "hybrid",
                "max_papers": 25
            },
            "session_timeout": 1800,
            "tags": ["test", "research"]
        }
        
        validated = SessionConfigSchema(**config)
        
        self.assertEqual(validated.session_name, "Test Research Session")
        self.assertEqual(validated.user_id, "user123")
        self.assertEqual(validated.research_config.storm_mode, "hybrid")
        self.assertEqual(validated.research_config.max_papers, 25)
    
    def test_session_config_schema_invalid_session_name(self):
        """Test that invalid session names raise validation error"""
        # Empty name
        config1 = {"session_name": "", "user_id": "user123"}
        with self.assertRaises(ValidationError):
            SessionConfigSchema(**config1)
        
        # Invalid characters
        config2 = {"session_name": "Test<>Session", "user_id": "user123"}
        with self.assertRaises(ValidationError):
            SessionConfigSchema(**config2)
    
    def test_session_config_schema_validates_nested_research_config(self):
        """Test that nested research config is validated"""
        config = {
            "session_name": "Test Session",
            "user_id": "user123",
            "research_config": {
                "storm_mode": "invalid_mode"  # Should fail validation
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            SessionConfigSchema(**config)
        
        self.assertIn("storm_mode", str(context.exception))
    
    async def test_interface_validates_research_config(self):
        """Test that interface validates research configuration"""
        # Valid config should work
        valid_config = {
            "storm_mode": "hybrid",
            "max_papers": 30,
            "citation_style": "apa"
        }
        
        try:
            await self.interface.configure_research(valid_config)
            # Should not raise exception
        except ValueError:
            self.fail("Valid config should not raise ValueError")
        
        # Invalid config should raise ValueError
        invalid_config = {
            "storm_mode": "invalid_mode"
        }
        
        with self.assertRaises(ValueError) as context:
            await self.interface.configure_research(invalid_config)
        
        self.assertIn("Invalid research configuration", str(context.exception))
    
    def test_interface_validates_session_config(self):
        """Test that interface validates session configuration"""
        session_id = self.interface.create_research_session("user123", "Test Session")
        
        # Valid config should work
        valid_config = {
            "research_config": {
                "storm_mode": "academic",
                "max_papers": 40
            }
        }
        
        try:
            self.interface.configure_session(session_id, valid_config)
            # Should not raise exception
        except ValueError:
            self.fail("Valid session config should not raise ValueError")
        
        # Invalid config should raise ValueError
        invalid_config = {
            "research_config": {
                "max_papers": -5  # Invalid value
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.interface.configure_session(session_id, invalid_config)
        
        self.assertIn("Invalid session configuration", str(context.exception))
    
    def test_schema_provides_helpful_error_messages(self):
        """Test that validation errors provide helpful messages"""
        config = {
            "max_papers": 2000,  # Too high
            "quality_threshold": 1.5,  # Too high
            "citation_style": "unknown",  # Invalid
            "agents": []  # Too few
        }
        
        with self.assertRaises(ValidationError) as context:
            ResearchConfigSchema(**config)
        
        error_message = str(context.exception)
        
        # Should contain details about each validation failure
        self.assertIn("max_papers", error_message)
        self.assertIn("quality_threshold", error_message)
        self.assertIn("citation_style", error_message)
        self.assertIn("agents", error_message)
    
    def test_schema_normalizes_values(self):
        """Test that schema normalizes values correctly"""
        config = {
            "citation_style": "APA",  # Should be lowercased
            "language": "EN",  # Should be lowercased
            "priority": "HIGH"  # Should be lowercased (for session config)
        }
        
        # Research config normalization
        research_validated = ResearchConfigSchema(**config)
        self.assertEqual(research_validated.citation_style, "apa")
        self.assertEqual(research_validated.language, "en")
        
        # Session config normalization
        session_config = {
            "session_name": "  Test Session  ",  # Should be stripped
            "user_id": "user123",
            "priority": "HIGH",
            "tags": ["  Tag1  ", "TAG2", "tag3  "]  # Should be normalized
        }
        
        session_validated = SessionConfigSchema(**session_config)
        self.assertEqual(session_validated.session_name, "Test Session")
        self.assertEqual(session_validated.priority, "high")
        self.assertEqual(session_validated.tags, ["tag1", "tag2", "tag3"])
    
    def test_schema_backward_compatibility(self):
        """Test that validated config maintains backward compatibility"""
        config = {
            "storm_mode": "academic",
            "agents": ["researcher"],
            "max_papers": 50
        }
        
        validated = ResearchConfigSchema(**config)
        config_dict = validated.dict()
        
        # Should be a regular dictionary that can be used with existing code
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict["storm_mode"], "academic")
        self.assertEqual(config_dict["agents"], ["researcher"])
        self.assertEqual(config_dict["max_papers"], 50)


if __name__ == "__main__":
    unittest.main()