"""
OpenAlex Database Client
Concrete implementation for OpenAlex academic database
"""

from typing import Dict, Any, List, Optional
import requests
from .abstract_database_client import AbstractDatabaseClient


class OpenAlexClient(AbstractDatabaseClient):
    """
    OpenAlex database client implementation
    Provides access to the OpenAlex scholarly database
    """
    
    def __init__(self):
        self.base_url = "https://api.openalex.org"
        self._authenticated = True  # OpenAlex is public API
        self.session = requests.Session()
        # Set user agent for API compliance
        self.session.headers.update({
            'User-Agent': 'StormLoop/1.0 (mailto:support@stormloop.ai)'
        })
    
    def search_papers(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for papers in OpenAlex
        
        Args:
            query: Search query string
            **kwargs: Additional parameters (limit, page, filter, etc.)
            
        Returns:
            List of normalized paper dictionaries
        """
        if not self.is_authenticated():
            raise RuntimeError("Client not authenticated")
        
        try:
            params = self._build_search_params(query, **kwargs)
            response = self.session.get(f"{self.base_url}/works", params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for work in data.get('results', []):
                normalized_paper = self.normalize_paper_data(work)
                papers.append(normalized_paper)
            
            return papers
            
        except requests.RequestException as e:
            # For now, return empty list on API failure
            # In production, you might want to log this error
            return []
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper from OpenAlex
        
        Args:
            paper_id: OpenAlex work ID
            
        Returns:
            Detailed paper information or None if not found
        """
        if not self.is_authenticated():
            return None
        
        try:
            response = self.session.get(f"{self.base_url}/works/{paper_id}")
            response.raise_for_status()
            
            work = response.json()
            return self.normalize_paper_data(work)
            
        except requests.RequestException:
            return None
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with OpenAlex (public API, always succeeds)
        
        Args:
            credentials: Not used for OpenAlex (public API)
            
        Returns:
            Always True for OpenAlex
        """
        self._authenticated = True
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated
        
        Returns:
            Always True for OpenAlex (public API)
        """
        return self._authenticated
    
    def normalize_paper_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OpenAlex paper data to standard format
        
        Args:
            raw_data: Raw OpenAlex work data
            
        Returns:
            Normalized paper data
        """
        # Extract authors
        authors = []
        for authorship in raw_data.get('authorships', []):
            author = authorship.get('author', {})
            if author.get('display_name'):
                authors.append(author['display_name'])
        
        # Extract publication year
        pub_date = raw_data.get('publication_date')
        year = None
        if pub_date:
            year = int(pub_date.split('-')[0]) if pub_date else None
        
        return {
            "title": raw_data.get('title', ''),
            "authors": authors,
            "year": year,
            "doi": raw_data.get('doi', '').replace('https://doi.org/', '') if raw_data.get('doi') else None,
            "abstract": raw_data.get('abstract'),
            "url": raw_data.get('doi'),
            "database_id": raw_data.get('id'),
            "database_source": "openalex",
            "open_access": raw_data.get('open_access', {}).get('is_oa', False),
            "citation_count": raw_data.get('cited_by_count', 0),
            "concepts": [concept.get('display_name') for concept in raw_data.get('concepts', [])]
        }
    
    def _build_search_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Build search parameters for OpenAlex API
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            'search': query,
            'per-page': kwargs.get('limit', 25),
            'page': kwargs.get('page', 1)
        }
        
        # Add filters if provided
        if 'filter' in kwargs:
            params['filter'] = kwargs['filter']
        
        # Add sorting if provided
        if 'sort' in kwargs:
            params['sort'] = kwargs['sort']
        
        return params