"""
Citation Factory
Factory for creating citation formatter instances following Factory Pattern
"""

from typing import Dict, Type, List
from .citation_formatter_interface import CitationFormatterInterface
from .apa_formatter import ApaFormatter
from .mla_formatter import MlaFormatter
from .chicago_formatter import ChicagoFormatter


class CitationFactory:
    """
    Factory for creating citation formatter instances
    Follows Factory Pattern and Open/Closed Principle for extensibility
    """
    
    # Registry of available citation formatters
    _formatters: Dict[str, Type[CitationFormatterInterface]] = {
        'apa': ApaFormatter,
        'mla': MlaFormatter,
        'chicago': ChicagoFormatter,
    }
    
    @classmethod
    def create_formatter(cls, style: str) -> CitationFormatterInterface:
        """
        Create a citation formatter instance
        
        Args:
            style: Citation style name (case-insensitive)
            
        Returns:
            Citation formatter instance
            
        Raises:
            ValueError: If citation style is not supported
        """
        style = style.lower()
        
        if style not in cls._formatters:
            raise ValueError(
                f"Unsupported citation style: {style}. "
                f"Available styles: {list(cls._formatters.keys())}"
            )
        
        formatter_class = cls._formatters[style]
        return formatter_class()
    
    @classmethod
    def get_available_styles(cls) -> List[str]:
        """
        Get list of available citation styles
        
        Returns:
            List of supported citation style names
        """
        return list(cls._formatters.keys())
    
    @classmethod
    def register_formatter(cls, style: str, formatter_class: Type[CitationFormatterInterface]):
        """
        Register a new citation formatter
        Allows extension without modifying existing code
        
        Args:
            style: Name for the citation style (will be converted to lowercase)
            formatter_class: Formatter class implementing CitationFormatterInterface
            
        Raises:
            TypeError: If formatter class doesn't implement the interface
        """
        if not issubclass(formatter_class, CitationFormatterInterface):
            raise TypeError("Formatter class must inherit from CitationFormatterInterface")
        
        cls._formatters[style.lower()] = formatter_class
    
    @classmethod
    def is_style_supported(cls, style: str) -> bool:
        """
        Check if a citation style is supported
        
        Args:
            style: Citation style name
            
        Returns:
            True if style is supported, False otherwise
        """
        return style.lower() in cls._formatters