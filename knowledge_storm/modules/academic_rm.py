from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Union

try:
    import dspy  # type: ignore
    RetrieveBase = getattr(dspy, "Retrieve", object)
except Exception:  # pragma: no cover - optional dependency
    dspy = None

    class RetrieveBase:  # type: ignore
        pass

from ..services.crossref_service import CrossrefService
from ..services.academic_source_service import SourceQualityScorer


class CrossrefRM(RetrieveBase):
    """Retrieve papers from Crossref and rank by quality."""

    def __init__(self, k: int = 3, service: CrossrefService | None = None, scorer: SourceQualityScorer | None = None):
        if dspy is not None and hasattr(RetrieveBase, "__init__"):
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

    def _doi_url(self, doi: str | None) -> str:
        return f"https://doi.org/{doi}" if doi else ""

    def _normalize_title(self, title: Any) -> str:
        if isinstance(title, list):
            return title[0] if title else ""
        return title or ""

    def _include(self, doi_url: str, exclude_urls: List[str]) -> bool:
        return not (doi_url and doi_url in exclude_urls)

    def _build_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        doi = item.get("DOI")
        title = self._normalize_title(item.get("title", ""))
        return self._result_dict(doi, title, item)

    def _result_dict(self, doi: str | None, title: str, item: Dict[str, Any]) -> Dict[str, Any]:
        abstract = item.get("abstract", "")
        return {"url": self._doi_url(doi), "title": title, "description": abstract,
                "snippets": [abstract], "score": self.scorer.score_source(item), "doi": doi}

    def _normalize_queries(self, query_or_queries: Union[str, List[str]]) -> List[str]:
        return [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries

    def _run_search(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._search_all(queries))

    async def async_forward(
        self,
        query_or_queries: Union[str, List[str]],
        exclude_urls: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        queries = self._normalize_queries(query_or_queries)
        self.usage += len(queries)
        exclude_urls = exclude_urls or []
        results = await self._search_all(queries)
        collected = self._collect_results(results, exclude_urls)
        return self._sort_limit(collected)

    def _collect_results(self, results: List[List[Dict[str, Any]]], exclude_urls: List[str]) -> List[Dict[str, Any]]:
        return [
            self._build_result(item)
            for items in results
            for item in items
            if self._include(self._doi_url(item.get("DOI")), exclude_urls)
        ]

    def _sort_limit(self, collected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        collected.sort(key=lambda r: r.get("score", 0), reverse=True)
        return collected[: self.k] if self.k else collected

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.async_forward(query_or_queries, exclude_urls)
        )
