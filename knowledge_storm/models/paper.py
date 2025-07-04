from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Paper:
    """Simple representation of an academic paper."""

    doi: Optional[str] = None
    title: str = ""
    authors: List[str] | None = None
    journal: Optional[str] = None
    year: Optional[int] = None

    @classmethod
    def from_crossref_response(cls, crossref_data: Dict[str, Any]) -> "Paper":
        """Convert Crossref API response to Paper object."""
        message = crossref_data.get("message", crossref_data)
        doi = message.get("DOI") or message.get("doi")

        title_field = message.get("title", "")
        if isinstance(title_field, list):
            title = title_field[0] if title_field else ""
        else:
            title = title_field or ""

        authors: List[str] = []
        for author in message.get("author", []):
            parts = [author.get("given", ""), author.get("family", "")]
            name = " ".join(p for p in parts if p)
            if name:
                authors.append(name)

        journal = None
        container = message.get("container-title")
        if isinstance(container, list):
            journal = container[0] if container else None
        elif isinstance(container, str):
            journal = container

        year = None
        issued = message.get("issued")
        if issued and isinstance(issued, dict):
            date_parts = issued.get("date-parts")
            if isinstance(date_parts, list) and date_parts and date_parts[0]:
                year = date_parts[0][0]

        return cls(doi=doi, title=title, authors=authors or None, journal=journal, year=year)
