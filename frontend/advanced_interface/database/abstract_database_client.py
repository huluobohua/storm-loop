"""
Abstract Database Client
Defines interface for database implementations following Open/Closed Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AbstractDatabaseClient(ABC):
    """
    Abstract base class for database clients
    Follows Open/Closed Principle - open for extension, closed for modification
    """
    
    @abstractmethod
    def search_papers(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for papers in the database
        
        Args:
            query: Search query string
            **kwargs: Database-specific parameters
            
        Returns:
            List of paper dictionaries with standardized fields
        """
        pass
    
    @abstractmethod
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper
        
        Args:
            paper_id: Unique identifier for the paper
            
        Returns:
            Paper details dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with the database service
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        pass
    
    def normalize_paper_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize paper data to standardized format
        Can be overridden by subclasses for database-specific normalization
        
        Args:
            raw_data: Raw paper data from database
            
        Returns:
            Normalized paper data with standard fields
        """
        return {
            "title": raw_data.get("title", ""),
            "authors": raw_data.get("authors", []),
            "year": raw_data.get("year"),
            "doi": raw_data.get("doi"),
            "abstract": raw_data.get("abstract", ""),
            "url": raw_data.get("url"),
            "database_id": raw_data.get("id"),
            "database_source": self.__class__.__name__.replace("Client", "").lower()
        }