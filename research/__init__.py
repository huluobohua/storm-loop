"""
Elite research backend following TDD, SOLID, and Sandi Metz principles.

This module provides a secure, testable, and maintainable research generation system.
"""

from .core import ResearchService
from .config import ResearchConfig

__all__ = ["ResearchService", "ResearchConfig"]