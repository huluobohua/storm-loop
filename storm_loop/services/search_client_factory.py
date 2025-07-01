from dataclasses import dataclass
import aiohttp

from .openalex_client import OpenAlexClient
from .crossref_client import CrossrefClient
from .perplexity_client import PerplexityClient


@dataclass
class SearchClients:
    openalex: OpenAlexClient
    crossref: CrossrefClient
    perplexity: PerplexityClient

    async def __aenter__(self):
        await self.openalex.__aenter__()
        await self.crossref.__aenter__()
        await self.perplexity.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.openalex.__aexit__(exc_type, exc_val, exc_tb)
        await self.crossref.__aexit__(exc_type, exc_val, exc_tb)
        await self.perplexity.__aexit__(exc_type, exc_val, exc_tb)


class SearchClientFactory:
    """Factory for creating all search clients."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    def create(self) -> SearchClients:
        return SearchClients(
            openalex=OpenAlexClient(session=self.session),
            crossref=CrossrefClient(session=self.session),
            perplexity=PerplexityClient(session=self.session),
        )
