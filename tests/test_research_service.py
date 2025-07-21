#!/usr/bin/env python3
"""
TDD tests for research service - written FIRST before implementation

Following Kent Beck TDD: Red -> Green -> Refactor
These tests specify the exact behavior we want before writing any code.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import List, Dict
import json


class TestResearchService:
    """Test the main research service following TDD principles"""
    
    def test_research_service_creation_requires_dependencies(self):
        """Test that ResearchService requires proper dependency injection"""
        from research.core import ResearchService
        
        # Should fail without dependencies - forces dependency injection
        with pytest.raises(TypeError):
            ResearchService()
    
    def test_research_service_accepts_injected_dependencies(self):
        """Test that ResearchService accepts injected dependencies"""
        from research.core import ResearchService
        from research.interfaces import QueryGenerator, SearchEngine, ContentProcessor
        
        query_gen = Mock(spec=QueryGenerator)
        search_engine = Mock(spec=SearchEngine)
        content_processor = Mock(spec=ContentProcessor)
        
        service = ResearchService(
            query_generator=query_gen,
            search_engine=search_engine, 
            content_processor=content_processor
        )
        
        assert service.query_generator is query_gen
        assert service.search_engine is search_engine
        assert service.content_processor is content_processor


class TestQueryGenerator:
    """Test query generation with proper behavior verification"""
    
    def test_query_generator_interface_exists(self):
        """Test that QueryGenerator interface is properly defined"""
        from research.interfaces import QueryGenerator
        
        # Interface should exist and be abstract
        assert hasattr(QueryGenerator, 'generate_queries')
    
    @pytest.mark.asyncio
    async def test_ai_query_generator_generates_exactly_eight_queries(self):
        """Test that AI query generator produces exactly 8 queries"""
        from research.query import AIQueryGenerator
        
        mock_llm = AsyncMock()
        mock_llm.generate_completion.return_value = """
        query one focused topic
        query two different angle  
        query three specific aspect
        query four technical details
        query five applications
        query six challenges
        query seven future trends
        query eight implications
        """
        
        generator = AIQueryGenerator(llm_service=mock_llm)
        queries = await generator.generate_queries("test topic")
        
        assert len(queries) == 8
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q.strip()) > 0 for q in queries)
    
    @pytest.mark.asyncio 
    async def test_ai_query_generator_handles_llm_failures(self):
        """Test that query generator handles LLM failures gracefully"""
        from research.query import AIQueryGenerator
        from research.exceptions import QueryGenerationError
        
        mock_llm = AsyncMock()
        mock_llm.generate_completion.side_effect = Exception("API Error")
        
        generator = AIQueryGenerator(llm_service=mock_llm)
        
        with pytest.raises(QueryGenerationError):
            await generator.generate_queries("test topic")


class TestSearchEngine:
    """Test search engine with proper mocking and assertions"""
    
    def test_search_engine_interface_exists(self):
        """Test that SearchEngine interface is properly defined"""  
        from research.interfaces import SearchEngine
        
        assert hasattr(SearchEngine, 'search')
    
    def test_secure_search_engine_uses_headers_not_url_params(self):
        """Test that search engine puts API keys in headers, not URL parameters"""
        from research.search import SecureSearchEngine
        
        engine = SecureSearchEngine(api_key="test-key")
        
        # Test header building (SECURE)
        headers = engine._build_headers()
        assert 'test-key' in str(headers)
        assert headers['Authorization'] == 'Bearer test-key'
        
        # Test parameter building (NO API KEYS)
        params = engine._build_params("test query")
        assert 'test-key' not in str(params)
        assert params['q'] == "test query"
    
    @pytest.mark.asyncio
    async def test_search_engine_returns_structured_results(self):
        """Test that search engine returns properly structured results"""
        from research.search import SecureSearchEngine
        from unittest.mock import patch
        
        mock_response = {
            'results': [
                {
                    'title': 'Test Result 1',
                    'url': 'https://example.com/1',
                    'description': 'Test description 1'
                },
                {
                    'title': 'Test Result 2', 
                    'url': 'https://example.com/2',
                    'description': 'Test description 2'
                }
            ]
        }
        
        engine = SecureSearchEngine(api_key="test-key")
        
        with patch.object(engine, '_make_request', return_value=mock_response):
            results = await engine.search("test query")
            
            assert len(results) == 2
            assert all('title' in r for r in results)
            assert all('url' in r for r in results)
            assert all('description' in r for r in results)


class TestContentProcessor:
    """Test content processing with small, focused methods"""
    
    def test_content_processor_interface_exists(self):
        """Test that ContentProcessor interface is properly defined"""
        from research.interfaces import ContentProcessor
        
        assert hasattr(ContentProcessor, 'generate_outline')
        assert hasattr(ContentProcessor, 'generate_article') 
        assert hasattr(ContentProcessor, 'polish_content')
    
    @pytest.mark.asyncio
    async def test_ai_content_processor_generates_outline(self):
        """Test that content processor generates structured outline"""
        from research.content import AIContentProcessor
        
        mock_llm = AsyncMock()
        mock_llm.generate_completion.return_value = """
        # Research Outline
        ## I. Introduction
        ## II. Main Topics
        ## III. Conclusion
        """
        
        processor = AIContentProcessor(llm_service=mock_llm)
        search_results = [{'title': 'test', 'description': 'test desc'}]
        
        outline = await processor.generate_outline("test topic", search_results)
        
        assert isinstance(outline, str)
        assert len(outline) > 0
        assert "Introduction" in outline
    
    def test_content_processor_methods_are_small(self):
        """Test that content processor methods follow Sandi Metz 5-line rule"""
        from research.content import AIContentProcessor
        import inspect
        
        # This test enforces the 5-line rule at test time
        methods = inspect.getmembers(AIContentProcessor, predicate=inspect.isfunction)
        
        for name, method in methods:
            if not name.startswith('_'):  # Skip private methods
                source_lines = inspect.getsourcelines(method)[0]
                # Count actual code lines (skip docstrings, empty lines, comments)
                code_lines = []
                in_docstring = False
                for line in source_lines:
                    stripped = line.strip()
                    if '"""' in stripped:
                        in_docstring = not in_docstring
                        continue
                    if not in_docstring and stripped and not stripped.startswith('#'):
                        code_lines.append(stripped)
                
                # Subtract method definition line
                actual_code_lines = len(code_lines) - 1
                assert actual_code_lines <= 5, f"Method {name} has {actual_code_lines} code lines, max 5 allowed"


class TestResearchWorkflow:
    """Test the complete research workflow end-to-end"""
    
    @pytest.mark.asyncio
    async def test_research_workflow_integration(self):
        """Test complete research workflow with all components"""
        from research.core import ResearchService
        from research.interfaces import QueryGenerator, SearchEngine, ContentProcessor
        
        # Mock all dependencies
        mock_query_gen = AsyncMock(spec=QueryGenerator)
        mock_query_gen.generate_queries.return_value = [
            "query 1", "query 2", "query 3", "query 4",
            "query 5", "query 6", "query 7", "query 8" 
        ]
        
        mock_search = AsyncMock(spec=SearchEngine)
        mock_search.search.return_value = [
            {'title': 'Result 1', 'url': 'http://test1.com', 'description': 'Desc 1'}
        ]
        
        mock_processor = AsyncMock(spec=ContentProcessor)
        mock_processor.generate_outline.return_value = "# Test Outline"
        mock_processor.generate_article.return_value = "Test article content"
        mock_processor.polish_content.return_value = "Polished article"
        
        # Test the complete workflow
        service = ResearchService(
            query_generator=mock_query_gen,
            search_engine=mock_search,
            content_processor=mock_processor
        )
        
        result = await service.generate_research("test topic")
        
        # Verify all components were called correctly
        mock_query_gen.generate_queries.assert_called_once_with("test topic")
        assert mock_search.search.call_count == 8  # Called for each query
        mock_processor.generate_outline.assert_called_once()
        mock_processor.generate_article.assert_called_once() 
        mock_processor.polish_content.assert_called_once()
        
        # Verify result structure
        assert 'topic' in result
        assert 'queries' in result
        assert 'search_results' in result
        assert 'outline' in result
        assert 'article' in result
        assert 'polished_article' in result


class TestErrorHandling:
    """Test comprehensive error handling throughout the system"""
    
    @pytest.mark.asyncio
    async def test_research_service_handles_query_generation_failure(self):
        """Test research service handles query generation failures gracefully"""
        from research.core import ResearchService
        from research.exceptions import QueryGenerationError
        
        mock_query_gen = AsyncMock()
        mock_query_gen.generate_queries.side_effect = Exception("LLM failure")
        
        mock_search = AsyncMock()
        mock_processor = AsyncMock()
        
        service = ResearchService(
            query_generator=mock_query_gen,
            search_engine=mock_search,
            content_processor=mock_processor
        )
        
        with pytest.raises(QueryGenerationError):
            await service.generate_research("test topic")
    
    @pytest.mark.asyncio
    async def test_research_service_handles_search_failure(self):
        """Test research service handles search failures gracefully"""
        from research.core import ResearchService
        from research.exceptions import SearchEngineError
        
        mock_query_gen = AsyncMock()
        mock_query_gen.generate_queries.return_value = ["query1", "query2"]
        
        mock_search = AsyncMock() 
        mock_search.search.side_effect = Exception("Search API failure")
        
        mock_processor = AsyncMock()
        
        service = ResearchService(
            query_generator=mock_query_gen,
            search_engine=mock_search,
            content_processor=mock_processor
        )
        
        with pytest.raises(SearchEngineError):
            await service.generate_research("test topic")


class TestConfiguration:
    """Test configuration and dependency injection"""
    
    def test_research_config_validates_api_keys(self):
        """Test that configuration validates required API keys"""
        from research.config import ResearchConfig
        from research.exceptions import ConfigurationError
        
        # Should require API keys
        with pytest.raises(ConfigurationError):
            ResearchConfig(search_api_key=None, llm_api_key=None)
    
    def test_research_config_creates_valid_configuration(self):
        """Test that configuration creates valid settings"""
        from research.config import ResearchConfig
        
        config = ResearchConfig(
            search_api_key="test-search-key",
            llm_api_key="test-llm-key"
        )
        
        assert config.search_api_key == "test-search-key"
        assert config.llm_api_key == "test-llm-key"
        assert hasattr(config, 'max_queries')
        assert config.max_queries == 8