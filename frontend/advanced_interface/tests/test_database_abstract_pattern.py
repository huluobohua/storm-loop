"""
Test cases for Database Abstract Pattern Implementation
Tests the factory pattern and concrete client implementations
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'frontend'))

# Set development environment for testing
os.environ['ENVIRONMENT'] = 'development'

from advanced_interface.database import (
    AbstractDatabaseClient, 
    DatabaseClientFactory,
    OpenAlexClient,
    CrossRefClient
)
from advanced_interface.database_manager import DatabaseManager


class TestDatabaseAbstractPattern(unittest.TestCase):
    """Test cases for database abstract pattern implementation"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.manager = DatabaseManager()
    
    def test_factory_creates_openalex_client(self):
        """Test that factory creates OpenAlex client correctly"""
        client = DatabaseClientFactory.create_client('openalex')
        self.assertIsInstance(client, OpenAlexClient)
        self.assertIsInstance(client, AbstractDatabaseClient)
    
    def test_factory_creates_crossref_client(self):
        """Test that factory creates CrossRef client correctly"""
        client = DatabaseClientFactory.create_client('crossref')
        self.assertIsInstance(client, CrossRefClient)
        self.assertIsInstance(client, AbstractDatabaseClient)
    
    def test_factory_raises_error_for_invalid_database(self):
        """Test that factory raises error for unsupported database"""
        with self.assertRaises(ValueError) as context:
            DatabaseClientFactory.create_client('invalid_db')
        
        self.assertIn("Unsupported database type", str(context.exception))
    
    def test_factory_get_available_databases(self):
        """Test that factory returns available database types"""
        available = DatabaseClientFactory.get_available_databases()
        self.assertIn('openalex', available)
        self.assertIn('crossref', available)
        self.assertIsInstance(available, list)
    
    def test_factory_register_new_client(self):
        """Test that factory can register new client types"""
        # Create mock client class
        class MockClient(AbstractDatabaseClient):
            def search_papers(self, query, **kwargs):
                return [{"title": "Mock Paper"}]
            
            def get_paper_details(self, paper_id):
                return {"title": "Mock Details"}
            
            def authenticate(self, credentials):
                return True
            
            def is_authenticated(self):
                return True
        
        # Register new client type
        DatabaseClientFactory.register_client('mock_db', MockClient)
        
        # Verify registration worked
        self.assertIn('mock_db', DatabaseClientFactory.get_available_databases())
        
        # Verify client creation works
        client = DatabaseClientFactory.create_client('mock_db')
        self.assertIsInstance(client, MockClient)
    
    def test_factory_register_invalid_client_raises_error(self):
        """Test that registering invalid client raises TypeError"""
        class InvalidClient:  # Doesn't inherit from AbstractDatabaseClient
            pass
        
        with self.assertRaises(TypeError) as context:
            DatabaseClientFactory.register_client('invalid', InvalidClient)
        
        self.assertIn("must inherit from AbstractDatabaseClient", str(context.exception))
    
    def test_database_manager_uses_factory_pattern(self):
        """Test that DatabaseManager uses factory pattern correctly"""
        # Select a database
        self.manager.select_database('openalex')
        
        # Mock the factory to return a mock client
        mock_client = Mock(spec=AbstractDatabaseClient)
        mock_client.search_papers.return_value = [
            {"title": "Test Paper", "authors": ["Test Author"]}
        ]
        
        with patch.object(DatabaseClientFactory, 'create_client', return_value=mock_client):
            # Perform search
            results = self.manager.search_papers("test query")
            
            # Verify factory was used
            DatabaseClientFactory.create_client.assert_called_once_with('openalex')
            
            # Verify client method was called
            mock_client.search_papers.assert_called_once_with("test query")
            
            # Verify results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Test Paper")
    
    def test_database_manager_caches_clients(self):
        """Test that DatabaseManager caches client instances"""
        self.manager.select_database('openalex')
        
        with patch.object(DatabaseClientFactory, 'create_client') as mock_factory:
            mock_client = Mock(spec=AbstractDatabaseClient)
            mock_client.search_papers.return_value = []
            mock_factory.return_value = mock_client
            
            # First search should create client
            self.manager.search_papers("query1")
            self.assertEqual(mock_factory.call_count, 1)
            
            # Second search should reuse cached client
            self.manager.search_papers("query2")
            self.assertEqual(mock_factory.call_count, 1)  # Still 1, not 2
    
    def test_database_manager_search_requires_database_selection(self):
        """Test that search requires database to be selected"""
        with self.assertRaises(ValueError) as context:
            self.manager.search_papers("test query")
        
        self.assertIn("No database selected", str(context.exception))
    
    def test_database_manager_search_validates_database(self):
        """Test that search validates database type"""
        with self.assertRaises(ValueError) as context:
            self.manager.search_papers("test query", database="invalid_db")
        
        self.assertIn("Invalid database", str(context.exception))
    
    def test_database_manager_get_paper_details(self):
        """Test that get_paper_details uses abstract client"""
        self.manager.select_database('crossref')
        
        mock_client = Mock(spec=AbstractDatabaseClient)
        mock_client.get_paper_details.return_value = {"title": "Detailed Paper"}
        
        with patch.object(DatabaseClientFactory, 'create_client', return_value=mock_client):
            result = self.manager.get_paper_details("test_id")
            
            # Verify client method was called
            mock_client.get_paper_details.assert_called_once_with("test_id")
            
            # Verify result
            self.assertEqual(result["title"], "Detailed Paper")
    
    def test_openalex_client_authentication(self):
        """Test OpenAlex client authentication (public API)"""
        client = OpenAlexClient()
        
        # OpenAlex is public API, should always be authenticated
        self.assertTrue(client.is_authenticated())
        self.assertTrue(client.authenticate({}))
    
    def test_crossref_client_authentication(self):
        """Test CrossRef client authentication (public API)"""
        client = CrossRefClient()
        
        # CrossRef is public API, should always be authenticated
        self.assertTrue(client.is_authenticated())
        self.assertTrue(client.authenticate({}))
    
    def test_client_normalization_includes_database_source(self):
        """Test that normalized paper data includes database source"""
        openalex_client = OpenAlexClient()
        crossref_client = CrossRefClient()
        
        # Test OpenAlex normalization
        openalex_raw = {"title": "Test Paper", "authorships": []}
        openalex_normalized = openalex_client.normalize_paper_data(openalex_raw)
        self.assertEqual(openalex_normalized["database_source"], "openalex")
        
        # Test CrossRef normalization  
        crossref_raw = {"title": ["Test Paper"], "author": []}
        crossref_normalized = crossref_client.normalize_paper_data(crossref_raw)
        self.assertEqual(crossref_normalized["database_source"], "crossref")


if __name__ == "__main__":
    unittest.main()