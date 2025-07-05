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

    def _doi_url(self, doi: str | None) -> str:
        return f"https://doi.org/{doi}" if doi else ""

    def _parse_title(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        if isinstance(title, list):
            return title[0] if title else ""
        return title or ""

    def _result_base(self, item: Dict[str, Any], doi: str | None) -> Dict[str, Any]:
        return {
            "url": self._doi_url(doi),
            "title": self._parse_title(item),
            "description": item.get("abstract", ""),
            "snippets": [item.get("abstract", "")],
        }

    def _build_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        doi = item.get("DOI")
        base = self._result_base(item, doi)
        return {**base, "score": self.scorer.score_source(item), "doi": doi}

    def _collect_results(self, results: List[List[Dict[str, Any]]], exclude: List[str]) -> List[Dict[str, Any]]:
        return [self._build_result(item)
                for items in results
                for item in items
                if self._include(self._doi_url(item.get("DOI")), exclude)]

    def _sort_and_limit(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return results[: self.k] if self.k else results

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        self.usage += len(queries)
        results = asyncio.get_event_loop().run_until_complete(self._search_all(queries))
        collected = self._collect_results(results, exclude_urls or [])
        return self._sort_and_limit(collected)
