"""
Test suite for ResearchQueryGenerator following TDD principles.
These tests define the exact behavior before implementation.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from research.query_generator import ResearchQueryGenerator
from research.models import QueryGenerationConfig, GeneratedQuery


class TestResearchQueryGenerator:
    """Test ResearchQueryGenerator following Sandi Metz rules (<100 lines)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = QueryGenerationConfig(
            topic="AI in healthcare",
            query_count=8,
            temperature=0.7
        )
        self.mock_llm = Mock()
        self.generator = ResearchQueryGenerator(self.mock_llm)
    
    def test_generate_queries_returns_correct_count(self):
        """Should generate exact number of queries specified"""
        self.mock_llm.generate.return_value = self._mock_llm_response()
        
        result = self.generator.generate(self.config)
        
        assert len(result) == 8
        assert all(isinstance(q, GeneratedQuery) for q in result)
    
    def test_generate_queries_with_valid_topic(self):
        """Should generate focused queries for valid topic"""
        self.mock_llm.generate.return_value = self._mock_llm_response()
        
        result = self.generator.generate(self.config)
        
        assert all(len(q.text) > 10 for q in result)
        assert all("AI" in q.text or "healthcare" in q.text for q in result)
    
    def test_generate_handles_llm_failure(self):
        """Should handle LLM API failures gracefully"""
        self.mock_llm.generate.side_effect = Exception("API Error")
        
        with pytest.raises(QueryGenerationError):
            self.generator.generate(self.config)
    
    def test_generate_validates_empty_topic(self):
        """Should reject empty topic"""
        config = QueryGenerationConfig(topic="", query_count=8)
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            self.generator.generate(config)
    
    def _mock_llm_response(self) -> str:
        """Mock LLM response with 8 queries"""
        return """1. AI diagnostic tools in healthcare
2. Machine learning medical imaging
3. Healthcare AI ethics and privacy
4. AI drug discovery and development
5. Electronic health records AI
6. AI-powered patient monitoring
7. Healthcare AI regulatory frameworks
8. AI telemedicine and remote care"""