import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .cache import RedisAcademicCache


@dataclass
class SearchResult:
    source: str
    query: str
    results: Any


class OpenAlexClient:
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Any:
        await asyncio.sleep(0.1)
        return {"source": "openalex", "query": query, "filters": filters or {}}


class CrossrefClient:
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Any:
        await asyncio.sleep(0.1)
        return {"source": "crossref", "query": query, "filters": filters or {}}


class PerplexityClient:
    async def search(self, query: str) -> Any:
        await asyncio.sleep(0.1)
        return {"source": "perplexity", "query": query}


class SearchClientFactory:
    def __init__(self, cache: Optional[RedisAcademicCache] = None) -> None:
        self.cache = cache
        self.openalex = OpenAlexClient()
        self.crossref = CrossrefClient()
        self.perplexity = PerplexityClient()

        if self.cache:
            from .cache import cache_decorator

            self.openalex.search = cache_decorator(self.cache, "openalex")(self.openalex.search)
            self.crossref.search = cache_decorator(self.cache, "crossref")(self.crossref.search)


class AcademicRetrieverAgent:
    def __init__(self, cache: RedisAcademicCache, clients: Optional[SearchClientFactory] = None) -> None:
        self.cache = cache
        self.clients = clients or SearchClientFactory(cache)

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> SearchResult:
        filters = filters or {}
        try:
            result = await self.clients.openalex.search(query, filters=filters)
            return SearchResult(source="openalex", query=query, results=result)
        except Exception:
            result = await self.clients.perplexity.search(query)
            return SearchResult(source="perplexity", query=query, results=result)
