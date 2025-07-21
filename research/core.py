"""
Core research service following SOLID principles.

Small, focused classes with dependency injection.
"""

from typing import Dict, Any
from .interfaces import QueryGenerator, SearchEngine, ContentProcessor
from .exceptions import QueryGenerationError, SearchEngineError


class ResearchService:
    """Main research service with injected dependencies."""
    
    def __init__(self, query_generator: QueryGenerator, 
                 search_engine: SearchEngine, 
                 content_processor: ContentProcessor):
        """Initialize with injected dependencies."""
        self.query_generator = query_generator
        self.search_engine = search_engine  
        self.content_processor = content_processor
    
    async def generate_research(self, topic: str) -> Dict[str, Any]:
        """Generate complete research report."""
        try:
            queries = await self._generate_queries(topic)
            search_results = await self._search_all(queries)  
            outline = await self._generate_outline(topic, search_results)
            article = await self._generate_article(outline, search_results)
            polished = await self._polish_article(article)
            return self._build_result(topic, queries, search_results, 
                                      outline, article, polished)
        except Exception as e:
            self._handle_error(e)
    
    async def _generate_queries(self, topic: str):
        """Generate queries using injected generator."""
        try:
            return await self.query_generator.generate_queries(topic)
        except Exception as e:
            raise QueryGenerationError(f"Query generation failed: {e}")
    
    async def _search_all(self, queries):
        """Search using injected search engine."""  
        try:
            results = []
            for query in queries:
                query_results = await self.search_engine.search(query)
                results.extend(query_results)
            return results
        except Exception as e:
            raise SearchEngineError(f"Search failed: {e}")
    
    async def _generate_outline(self, topic, results):
        """Generate outline using injected processor."""
        return await self.content_processor.generate_outline(topic, results)
    
    async def _generate_article(self, outline, results):
        """Generate article using injected processor."""
        return await self.content_processor.generate_article(outline, results)
    
    async def _polish_article(self, article):
        """Polish article using injected processor."""
        return await self.content_processor.polish_content(article)
    
    def _build_result(self, topic, queries, results, outline, article, polished):
        """Build final result dictionary."""
        return {
            'topic': topic,
            'queries': queries,
            'search_results': results,
            'outline': outline,
            'article': article, 
            'polished_article': polished
        }
    
    def _handle_error(self, error):
        """Handle and re-raise errors appropriately."""
        if isinstance(error, (QueryGenerationError, SearchEngineError)):
            raise error
        raise Exception(f"Research generation failed: {error}")