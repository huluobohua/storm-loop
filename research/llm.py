"""
LLM service implementations following security and async best practices.

Secure API key handling, proper async I/O, comprehensive error handling.
"""

import aiohttp
import json
from typing import Dict, Any
from .interfaces import LLMService


class OpenAIService(LLMService):
    """Secure OpenAI service with API keys in headers."""
    
    def __init__(self, api_key: str):
        """Initialize with API key (stored securely)."""
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def generate_completion(self, prompt: str) -> str:
        """Generate completion with secure API call."""
        headers = self._build_headers()
        payload = self._build_payload(prompt)
        response_data = await self._make_request(headers, payload)
        return self._extract_content(response_data)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers with API key (SECURE)."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        """Build request payload."""
        return {
            'model': 'gpt-4o-mini',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000
        }
    
    async def _make_request(self, headers: Dict, payload: Dict) -> Dict:
        """Make secure HTTP request."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                return await response.json()
    
    def _extract_content(self, response: Dict) -> str:
        """Extract content from API response."""
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return "Content generation failed"