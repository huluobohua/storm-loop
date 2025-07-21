"""
Query generation following Sandi Metz rules - methods ≤5 lines.

Secure, testable implementation with dependency injection.
"""

import re
from typing import List
from .interfaces import QueryGenerator, LLMService


class AIQueryGenerator(QueryGenerator):
    """AI-powered query generator with injected LLM service."""
    
    def __init__(self, llm_service: LLMService):
        """Initialize with injected LLM service."""
        self.llm_service = llm_service
    
    async def generate_queries(self, topic: str) -> List[str]:
        """Generate exactly 8 focused queries."""
        try:
            prompt = self._build_prompt(topic)
            response = await self.llm_service.generate_completion(prompt)
            return self._parse_queries(response)
        except Exception as e:
            from .exceptions import QueryGenerationError
            raise QueryGenerationError(f"Failed to generate queries: {e}")
    
    def _build_prompt(self, topic: str) -> str:
        """Build LLM prompt for query generation."""
        return f"""Generate 8 search queries for: "{topic}"
Requirements: focused, specific, one per line
Topic: {topic}"""
    
    def _parse_queries(self, response: str) -> List[str]:
        """Parse exactly 8 queries from LLM response."""
        lines = response.strip().split('\n')
        queries = self._clean_queries(lines)
        return queries[:8] if len(queries) >= 8 else self._pad_queries(queries)
    
    def _clean_queries(self, lines: List[str]) -> List[str]:
        """Clean and filter query lines."""
        cleaned = []
        for line in lines:
            clean_line = self._clean_line(line)
            if len(clean_line) > 10:
                cleaned.append(clean_line)
        return cleaned
    
    def _clean_line(self, line: str) -> str:
        """Clean individual query line.""" 
        clean = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
        clean = re.sub(r'^[-*]\s*', '', clean)
        return clean.strip('"\'')
    
    def _pad_queries(self, queries: List[str]) -> List[str]:
        """Ensure exactly 8 queries by padding if needed."""
        while len(queries) < 8:
            base_query = queries[0] if queries else "research topic"
            queries.append(f"{base_query} aspect {len(queries) + 1}")
        return queries[:8]