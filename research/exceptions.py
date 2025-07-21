"""
Custom exceptions for research system.

Provides clear error types for different failure scenarios.
"""


class ResearchError(Exception):
    """Base exception for research system errors."""
    pass


class QueryGenerationError(ResearchError):
    """Raised when query generation fails."""
    pass


class SearchEngineError(ResearchError):
    """Raised when search operations fail."""
    pass


class ContentProcessingError(ResearchError):
    """Raised when content processing fails."""
    pass


class ConfigurationError(ResearchError):
    """Raised when configuration is invalid."""
    pass


class LLMServiceError(ResearchError):
    """Raised when LLM service operations fail."""
    pass