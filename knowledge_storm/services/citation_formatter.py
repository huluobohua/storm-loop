from typing import Any, Dict


class CitationFormatter:
    """Format citation metadata in various styles."""

    def format(self, source: Dict[str, Any], style: str = "APA") -> str:
        data = self._extract_citation_data(source)
        return self._format_by_style(data, style.upper())

    def _extract_citation_data(self, source: Dict[str, Any]) -> Dict[str, str]:
        return {
            "author": source.get("author", "Anon"),
            "year": self._get_publication_year(source),
            "title": source.get("title", ""),
        }

    def _get_publication_year(self, source: Dict[str, Any]) -> str:
        return str(source.get("year") or source.get("publication_year", "n.d."))

    def _format_by_style(self, data: Dict[str, str], style: str) -> str:
        if style == "MLA":
            return self._format_mla(data)
        if style == "CHICAGO":
            return self._format_chicago(data)
        return self._format_apa(data)

    def _format_mla(self, data: Dict[str, str]) -> str:
        return f"{data['author']}. \"{data['title']}\" ({data['year']})."

    def _format_chicago(self, data: Dict[str, str]) -> str:
        return f"{data['author']}. {data['year']}. {data['title']}."

    def _format_apa(self, data: Dict[str, str]) -> str:
        return f"{data['author']} ({data['year']}). {data['title']}."

