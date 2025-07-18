"""
CrossRef Database Client
Concrete implementation for CrossRef metadata database
"""

from typing import Dict, Any, List, Optional
import requests
from .abstract_database_client import AbstractDatabaseClient


class CrossRefClient(AbstractDatabaseClient):
    """
    CrossRef database client implementation
    Provides access to CrossRef metadata for scholarly publications
    """
    
    def __init__(self):
        self.base_url = "https://api.crossref.org"
        self._authenticated = True  # CrossRef is public API
        self.session = requests.Session()
        # Set user agent for CrossRef API compliance
        self.session.headers.update({
            'User-Agent': 'StormLoop/1.0 (mailto:support@stormloop.ai)'
        })
    
    def search_papers(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for papers in CrossRef
        
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
            
            for work in data.get('message', {}).get('items', []):
                normalized_paper = self.normalize_paper_data(work)
                papers.append(normalized_paper)
            
            return papers
            
        except requests.RequestException as e:
            # Return empty list on API failure
            return []
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper from CrossRef
        
        Args:
            paper_id: DOI or CrossRef work ID
            
        Returns:
            Detailed paper information or None if not found
        """
        if not self.is_authenticated():
            return None
        
        try:
            # Clean DOI if it includes URL prefix
            clean_doi = paper_id.replace('https://doi.org/', '')
            response = self.session.get(f"{self.base_url}/works/{clean_doi}")
            response.raise_for_status()
            
            data = response.json()
            work = data.get('message', {})
            return self.normalize_paper_data(work)
            
        except requests.RequestException:
            return None
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with CrossRef (public API, always succeeds)
        
        Args:
            credentials: Not used for CrossRef (public API)
            
        Returns:
            Always True for CrossRef
        """
        self._authenticated = True
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated
        
        Returns:
            Always True for CrossRef (public API)
        """
        return self._authenticated
    
    def normalize_paper_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize CrossRef paper data to standard format
        
        Args:
            raw_data: Raw CrossRef work data
            
        Returns:
            Normalized paper data
        """
        # Extract authors
        authors = []
        for author in raw_data.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        
        # Extract title
        title_list = raw_data.get('title', [])
        title = title_list[0] if title_list else ''
        
        # Extract publication year
        published = raw_data.get('published-print') or raw_data.get('published-online')
        year = None
        if published and 'date-parts' in published:
            date_parts = published['date-parts'][0]
            if date_parts:
                year = date_parts[0]
        
        # Extract DOI
        doi = raw_data.get('DOI', '')
        
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "abstract": raw_data.get('abstract'),  # CrossRef rarely has abstracts
            "url": f"https://doi.org/{doi}" if doi else None,
            "database_id": doi,
            "database_source": "crossref",
            "journal": raw_data.get('container-title', [None])[0],
            "publisher": raw_data.get('publisher'),
            "type": raw_data.get('type'),
            "citation_count": raw_data.get('is-referenced-by-count', 0)
        }
    
    def _build_search_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Build search parameters for CrossRef API
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            'query': query,
            'rows': kwargs.get('limit', 25),
            'offset': (kwargs.get('page', 1) - 1) * kwargs.get('limit', 25)
        }
        
        # Add sorting if provided
        if 'sort' in kwargs:
            params['sort'] = kwargs['sort']
        
        # Add filters if provided
        if 'filter' in kwargs:
            params['filter'] = kwargs['filter']
        
        return params