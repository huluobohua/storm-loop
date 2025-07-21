"""
Factory for creating research service with proper dependency injection.

Follows SOLID principles and provides clean object creation.
"""

from .core import ResearchService
from .query import AIQueryGenerator
from .search import SecureSearchEngine
from .content import AIContentProcessor
from .llm import OpenAIService
from .config import ResearchConfig


class ResearchServiceFactory:
    """Factory for creating configured research service."""
    
    @staticmethod
    def create(config: ResearchConfig) -> ResearchService:
        """Create fully configured research service."""
        components = ResearchServiceFactory._create_components(config)
        return ResearchServiceFactory._assemble_service(components)
    
    @staticmethod
    def _create_components(config: ResearchConfig) -> dict:
        """Create service components from configuration."""
        llm_service = OpenAIService(config.llm_api_key)
        return {
            'llm': llm_service,
            'query_gen': AIQueryGenerator(llm_service),
            'search': SecureSearchEngine(config.search_api_key),
            'processor': AIContentProcessor(llm_service)
        }
    
    @staticmethod
    def _assemble_service(components: dict) -> ResearchService:
        """Assemble service from components."""
        return ResearchService(
            query_generator=components['query_gen'],
            search_engine=components['search'],
            content_processor=components['processor']
        )