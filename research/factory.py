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
        llm_service = OpenAIService(config.llm_api_key)
        query_generator = AIQueryGenerator(llm_service)
        search_engine = SecureSearchEngine(config.search_api_key)  
        content_processor = AIContentProcessor(llm_service)
        
        return ResearchService(
            query_generator=query_generator,
            search_engine=search_engine,
            content_processor=content_processor
        )