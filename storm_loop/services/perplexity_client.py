"""Perplexity API client for general knowledge retrieval"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional

from storm_loop.config import get_config
from storm_loop.utils.logging import storm_logger


class PerplexityClient:
    """Simple async client for the Perplexity search API."""

    BASE_URL = "https://api.perplexity.ai"

    def __init__(self, api_key: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self.config = get_config()
        self.api_key = api_key or self.config.perplexity_api_key
        self.session = session
        self._own_session = session is None
        self._request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self._disabled = False

    async def __aenter__(self):
        if self._own_session:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

        if not self.api_key:
            storm_logger.warning(
                "Perplexity API key not configured, fallback search disabled"
            )
            self._disabled = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self.session:
            await self.session.close()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Perplexity for general information."""
        if self._disabled:
            return self._disabled_response()

        request = self._build_request(query, limit)
        async with self._request_semaphore:
            return await self._execute_request(request)

    def is_disabled(self) -> bool:
        return self._disabled

    def _disabled_response(self) -> List[Dict[str, Any]]:
        storm_logger.debug("Perplexity client disabled; returning empty result")
        return []

    def _build_request(self, query: str, limit: int) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        return {
            "url": f"{self.BASE_URL}/search",
            "params": {"q": query, "limit": limit},
            "headers": headers,
        }

    async def _execute_request(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            async with self.session.get(**request) as resp:
                return await self._handle_response(resp)
        except Exception as e:
            storm_logger.error(f"Perplexity request failed: {e}")
            raise

    async def _handle_response(self, resp: aiohttp.ClientResponse) -> List[Dict[str, Any]]:
        if resp.ok:
            data = await resp.json()
            return data.get("results", [])

        text = await resp.text()
        if resp.status == 401:
            storm_logger.error("Perplexity API authentication failed")
        elif resp.status == 429:
            storm_logger.warning("Perplexity API rate limit exceeded")
        else:
            storm_logger.error(f"Perplexity API error {resp.status}: {text}")
        raise aiohttp.ClientResponseError(
            request_info=resp.request_info,
            history=resp.history,
            status=resp.status,
            message=text,
        )
