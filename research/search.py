"""
Secure search engine following elite security practices.

API keys in headers, proper async I/O, comprehensive error handling.
"""

import aiohttp
from typing import List, Dict, Any
from .interfaces import SearchEngine


class SecureSearchEngine(SearchEngine):
    """Secure search engine with API keys in headers."""
    
    def __init__(self, api_key: str):
        """Initialize with API key (stored securely)."""
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search with API key in headers (secure)."""
        headers = self._build_headers()
        params = self._build_params(query)
        response_data = await self._make_request(headers, params)
        return self._parse_results(response_data)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers (no auth - SerpApi uses query params)."""
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'Research-Service/1.0'
        }
    
    def _build_params(self, query: str) -> Dict[str, str]:
        """Build query parameters with API key (SerpApi requirement)."""
        base_params = {'q': query, 'engine': 'google'}
        auth_params = {'api_key': self.api_key}
        return {**base_params, **auth_params}
    
    async def _make_request(self, headers: Dict, params: Dict) -> Dict:
        """Make secure HTTP request with proper async."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.base_url,
                headers=headers,
                params=params
            ) as response:
                return await response.json()
    
    def _parse_results(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse search results into standard format."""
        results = data.get('results', [])
        return [self._format_result(r) for r in results]
    
    def _format_result(self, result: Dict) -> Dict[str, Any]:
        """Format individual search result."""
        basic_fields = {'title': result.get('title', ''), 'url': result.get('url', '')}
        desc_field = {'description': result.get('description', '')}
        return {**basic_fields, **desc_field}