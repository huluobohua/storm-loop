"""
Content processor following Sandi Metz rules strictly.

All methods ≤5 lines, focused responsibilities.
"""

from typing import List, Dict
from .interfaces import ContentProcessor, LLMService


class AIContentProcessor(ContentProcessor):
    """AI content processor with small, focused methods."""
    
    def __init__(self, llm_service: LLMService):
        """Initialize with injected LLM service."""
        self.llm_service = llm_service
    
    async def generate_outline(self, topic: str, search_results: List[Dict]) -> str:
        """Generate outline (≤5 lines per Sandi Metz)."""
        prompt = self._build_outline_prompt(topic, search_results)
        return await self.llm_service.generate_completion(prompt)
    
    async def generate_article(self, outline: str, search_results: List[Dict]) -> str:
        """Generate article (≤5 lines per Sandi Metz)."""
        prompt = self._build_article_prompt(outline, search_results)
        return await self.llm_service.generate_completion(prompt)
    
    async def polish_content(self, article: str) -> str:
        """Polish content (≤5 lines per Sandi Metz)."""
        prompt = self._build_polish_prompt(article)
        return await self.llm_service.generate_completion(prompt)
    
    def _build_outline_prompt(self, topic: str, results: List[Dict]) -> str:
        """Build outline prompt (≤5 lines)."""
        context = self._format_search_context(results)
        return f"Generate outline for: {topic}\nContext: {context[:1000]}"
    
    def _build_article_prompt(self, outline: str, results: List[Dict]) -> str:
        """Build article prompt (≤5 lines)."""
        context = self._format_search_context(results)
        return f"Write article using outline:\n{outline}\nSources: {context[:2000]}"
    
    def _build_polish_prompt(self, article: str) -> str:
        """Build polish prompt (≤5 lines)."""
        return f"Polish this article:\n{article[:3000]}\nImprove structure and flow."
    
    def _format_search_context(self, results: List[Dict]) -> str:
        """Format search results (≤5 lines)."""
        if not results:
            return "No results available"
        formatted = [f"{r.get('title', '')}: {r.get('description', '')}" for r in results[:5]]
        return "\n".join(formatted)