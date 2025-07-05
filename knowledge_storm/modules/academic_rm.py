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

    async def _search_all(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        tasks = [self.service.search_works(q, self.k) for q in queries]
        return await asyncio.gather(*tasks)

    def _include(self, doi_url: str, exclude_urls: List[str]) -> bool:
        return not (doi_url and doi_url in exclude_urls)

    def _build_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": self._doi_url(item),
            "title": self._parse_title(item),
            "description": item.get("abstract", ""),
            "snippets": [item.get("abstract", "")],
            "score": self.scorer.score_source(item),
            "doi": item.get("DOI"),
        }

    def _parse_title(self, item: Dict[str, Any]) -> str:
        title = item.get("title", [""])
        return title[0] if isinstance(title, list) and title else title or ""

    def _doi_url(self, item: Dict[str, Any]) -> str:
        doi = item.get("DOI")
        return f"https://doi.org/{doi}" if doi else ""

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        self.usage += len(queries)
        results = asyncio.get_event_loop().run_until_complete(self._search_all(queries))
        return self._process_results(results, exclude_urls or [])

    def _process_results(self, results: List[List[Dict[str, Any]]], exclude_urls: List[str]) -> List[Dict[str, Any]]:
        collected = self._collect_items(results, exclude_urls)
        collected.sort(key=lambda r: r.get("score", 0), reverse=True)
        return collected[: self.k] if self.k else collected

    def _collect_items(self, results: List[List[Dict[str, Any]]], exclude_urls: List[str]) -> List[Dict[str, Any]]:
        return [self._build_result(item)
                for items in results
                for item in items
                if self._include(self._doi_url(item), exclude_urls)]
