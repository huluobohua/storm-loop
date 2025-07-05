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
        """Convert Crossref API response to ``Paper``."""
        message = crossref_data.get("message", crossref_data)
        return cls(
            doi=message.get("DOI") or message.get("doi"),
            title=cls._parse_title(message),
            authors=cls._parse_authors(message) or None,
            journal=cls._parse_journal(message),
            year=cls._parse_year(message),
        )

    @staticmethod
    def _parse_title(msg: Dict[str, Any]) -> str:
        title = msg.get("title", "")
        if isinstance(title, list):
            return title[0] if title else ""
        return title or ""

    @staticmethod
    def _parse_authors(msg: Dict[str, Any]) -> List[str]:
        authors: List[str] = []
        for author in msg.get("author", []):
            parts = [author.get("given", ""), author.get("family", "")]
            name = " ".join(p for p in parts if p)
            if name:
                authors.append(name)
        return authors

    @staticmethod
    def _parse_journal(msg: Dict[str, Any]) -> Optional[str]:
        container = msg.get("container-title")
        if isinstance(container, list):
            return container[0] if container else None
        if isinstance(container, str):
            return container
        return None

    @staticmethod
    def _parse_year(msg: Dict[str, Any]) -> Optional[int]:
        issued = msg.get("issued")
        if isinstance(issued, dict):
            parts = issued.get("date-parts")
            if isinstance(parts, list) and parts and parts[0]:
                return parts[0][0]
        return None
