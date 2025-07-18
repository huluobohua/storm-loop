"""
Database Client Factory
Creates appropriate database client instances following Factory Pattern
"""

from typing import Dict, Type
from .abstract_database_client import AbstractDatabaseClient
from .openalex_client import OpenAlexClient
from .crossref_client import CrossRefClient


class DatabaseClientFactory:
    """
    Factory for creating database client instances
    Follows Factory Pattern and Open/Closed Principle
    """
    
    # Registry of available database clients
    _clients: Dict[str, Type[AbstractDatabaseClient]] = {
        'openalex': OpenAlexClient,
        'crossref': CrossRefClient,
    }
    
    @classmethod
    def create_client(cls, database_type: str) -> AbstractDatabaseClient:
        """
        Create a database client instance
        
        Args:
            database_type: Type of database client to create
            
        Returns:
            Database client instance
            
        Raises:
            ValueError: If database type is not supported
        """
        database_type = database_type.lower()
        
        if database_type not in cls._clients:
            raise ValueError(
                f"Unsupported database type: {database_type}. "
                f"Available types: {list(cls._clients.keys())}"
            )
        
        client_class = cls._clients[database_type]
        return client_class()
    
    @classmethod
    def get_available_databases(cls) -> list:
        """
        Get list of available database types
        
        Returns:
            List of supported database type strings
        """
        return list(cls._clients.keys())
    
    @classmethod
    def register_client(cls, database_type: str, client_class: Type[AbstractDatabaseClient]):
        """
        Register a new database client type
        Allows extension without modifying existing code
        
        Args:
            database_type: Name for the database type
            client_class: Client class implementing AbstractDatabaseClient
        """
        if not issubclass(client_class, AbstractDatabaseClient):
            raise TypeError("Client class must inherit from AbstractDatabaseClient")
        
        cls._clients[database_type.lower()] = client_class