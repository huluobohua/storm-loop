"""
Citation Formatter Interface
Abstract base class for citation formatting strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class CitationFormatterInterface(ABC):
    """
    Abstract interface for citation formatters
    Follows Strategy pattern for extensible citation formatting
    """
    
    @abstractmethod
    def format_citation(self, paper_data: Dict[str, Any]) -> str:
        """
        Format a paper citation according to the specific style
        
        Args:
            paper_data: Dictionary containing paper information
                       Expected keys: title, authors, year, journal, doi, etc.
        
        Returns:
            Formatted citation string
        """
        pass
    
    @abstractmethod
    def get_style_name(self) -> str:
        """
        Get the name of this citation style
        
        Returns:
            Citation style name (e.g., "APA", "MLA", "Chicago")
        """
        pass
    
    def validate_paper_data(self, paper_data: Dict[str, Any]) -> None:
        """
        Validate that paper data contains minimum required fields
        Can be overridden by subclasses for style-specific validation
        
        Args:
            paper_data: Paper data dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['title']
        missing_fields = [field for field in required_fields if not paper_data.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields for citation: {missing_fields}")
    
    def get_authors_string(self, authors: list, max_authors: int = None) -> str:
        """
        Helper method to format authors list
        Can be overridden by subclasses for style-specific author formatting
        
        Args:
            authors: List of author names
            max_authors: Maximum number of authors to display
            
        Returns:
            Formatted authors string
        """
        if not authors:
            return "Unknown Author"
        
        if max_authors and len(authors) > max_authors:
            return f"{', '.join(authors[:max_authors])}, et al."
        
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]}"
        else:
            return f"{', '.join(authors[:-1])}, & {authors[-1]}"