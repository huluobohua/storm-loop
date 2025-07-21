"""
Interfaces defining contracts for research system components.

Following SOLID principles - depend on abstractions, not concretions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class QueryGenerator(ABC):
    """Abstract interface for query generation."""
    
    @abstractmethod
    async def generate_queries(self, topic: str) -> List[str]:
        """Generate focused search queries for a research topic."""
        pass


class SearchEngine(ABC):  
    """Abstract interface for search operations."""
    
    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Execute search query and return structured results."""
        pass


class ContentProcessor(ABC):
    """Abstract interface for content processing."""
    
    @abstractmethod 
    async def generate_outline(self, topic: str, search_results: List[Dict]) -> str:
        """Generate research outline from search results."""
        pass
    
    @abstractmethod
    async def generate_article(self, outline: str, search_results: List[Dict]) -> str:
        """Generate article from outline and search results."""
        pass
    
    @abstractmethod
    async def polish_content(self, article: str) -> str:
        """Polish and enhance article content."""
        pass


class LLMService(ABC):
    """Abstract interface for LLM operations."""
    
    @abstractmethod
    async def generate_completion(self, prompt: str) -> str:
        """Generate text completion from prompt."""
        pass