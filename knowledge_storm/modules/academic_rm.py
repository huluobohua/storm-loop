from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Union

import dspy

from ..services.crossref_service import CrossrefService
from ..services.academic_source_service import SourceQualityScorer


class CrossrefRM(dspy.Retrieve):
    """Retrieve papers from Crossref and rank by quality."""

    def __init__(self, k: int = 3, service: CrossrefService | None = None, scorer: SourceQualityScorer | None = None):
        super().__init__(k=k)
        self.service = service or CrossrefService()
        self.scorer = scorer or SourceQualityScorer()
        self.usage = 0

    def get_usage_and_reset(self) -> Dict[str, int]:
        usage = self.usage
        self.usage = 0
        return {"CrossrefRM": usage}

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        self.usage += len(queries)
        exclude_urls = exclude_urls or []

        async def _search_all() -> List[List[Dict[str, Any]]]:
            tasks = [self.service.search_works(q, self.k) for q in queries]
            return await asyncio.gather(*tasks)

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(_search_all())

        collected: List[Dict[str, Any]] = []
        for items in results:
            for item in items:
                doi = item.get("DOI")
                url = f"https://doi.org/{doi}" if doi else ""
                if url and url in exclude_urls:
                    continue
                metadata = item
                score = self.scorer.score_source(metadata)
                title = metadata.get("title", [""])
                if isinstance(title, list):
                    title = title[0] if title else ""
                result = {
                    "url": url,
                    "title": title,
                    "description": metadata.get("abstract", ""),
                    "snippets": [metadata.get("abstract", "")],
                    "score": score,
                    "doi": doi,
                }
                collected.append(result)
        collected.sort(key=lambda r: r.get("score", 0), reverse=True)
        if self.k:
            return collected[: self.k]
        return collected
