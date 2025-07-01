import asyncio
from typing import Any, Dict, List, Optional
import json
from urllib import request, parse


class AcademicSourceService:
    """Service for retrieving academic sources from OpenAlex and Crossref."""

    OPENALEX_URL = "https://api.openalex.org/works"
    CROSSREF_URL = "https://api.crossref.org/works"

    def __init__(self) -> None:
        pass

    def search_openalex(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        params = parse.urlencode({"search": query, "per-page": limit})
        with request.urlopen(f"{self.OPENALEX_URL}?{params}") as resp:
            data = json.load(resp)
        return data.get("results", [])

    def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        with request.urlopen(f"{self.OPENALEX_URL}/{paper_id}") as resp:
            return json.load(resp)

    def search_crossref(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        params = parse.urlencode({"query": query, "rows": limit})
        with request.urlopen(f"{self.CROSSREF_URL}?{params}") as resp:
            data = json.load(resp)
        return data.get("message", {}).get("items", [])

    def resolve_doi(self, doi: str) -> Dict[str, Any]:
        with request.urlopen(f"{self.CROSSREF_URL}/{doi}") as resp:
            return json.load(resp).get("message", {})

    def get_publication_metadata(self, doi: str) -> Dict[str, Any]:
        return self.resolve_doi(doi)


class SourceQualityScorer:
    """Simple scoring based on citation count and recency."""

    def score_source(self, metadata: Dict[str, Any]) -> float:
        citations = metadata.get("cited_by_count") or metadata.get("is-referenced-by-count", 0)
        year = None
        if "publication_year" in metadata:
            year = metadata.get("publication_year")
        elif "issued" in metadata and "date-parts" in metadata["issued"]:
            year = metadata["issued"]["date-parts"][0][0]
        score = float(citations)
        if year:
            score += max(0, year - 2000) * 0.1
        return score

