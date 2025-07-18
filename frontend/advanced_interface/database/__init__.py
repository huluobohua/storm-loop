"""
Database clients package
Provides abstract interface and concrete implementations for various academic databases
"""

from .abstract_database_client import AbstractDatabaseClient
from .database_client_factory import DatabaseClientFactory
from .openalex_client import OpenAlexClient
from .crossref_client import CrossRefClient

__all__ = [
    'AbstractDatabaseClient',
    'DatabaseClientFactory', 
    'OpenAlexClient',
    'CrossRefClient'
]