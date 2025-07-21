"""
Configuration for research system.

Following SOLID principles with proper validation.
"""

from dataclasses import dataclass
from .exceptions import ConfigurationError


@dataclass
class ResearchConfig:
    """Configuration for research system."""
    
    search_api_key: str
    llm_api_key: str
    max_queries: int = 8
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        if not self.search_api_key:
            raise ConfigurationError("search_api_key is required")
        
        if not self.llm_api_key:
            raise ConfigurationError("llm_api_key is required")
        
        if self.max_queries != 8:
            raise ConfigurationError("max_queries must be 8")