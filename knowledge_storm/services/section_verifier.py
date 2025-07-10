from __future__ import annotations

import logging
import re
from typing import Any, Dict, List
import asyncio

from .citation_verifier import CitationVerifier

logger = logging.getLogger(__name__)


class SectionCitationVerifier:
    """Verify citations referenced within a section."""

    def __init__(self, verifier: CitationVerifier) -> None:
        self.verifier = verifier

    def verify_section(self, section_text: str, info_list: List[Any]) -> List[Dict[str, Any]]:
        """Synchronously verify citations within ``section_text``."""
        return asyncio.run(self.verify_section_async(section_text, info_list))

    async def verify_section_async(self, section_text: str, info_list: List[Any]) -> List[Dict[str, Any]]:
        """Verify citations concurrently using async calls."""
        indices = self._extract_citation_indices(section_text)
        tasks = [self._verify_single_citation_async(i, info_list) for i in indices]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    def _extract_citation_indices(self, section_text: str) -> List[int]:
        indices: List[int] = []
        for match in re.findall(r"\[[^\]]+\]", section_text):
            try:
                indices.append(int(match[1:-1]))
            except ValueError:  # pragma: no cover - malformed citation
                logger.warning("Invalid citation format: %s", match)
        return indices

    def _verify_citations_by_indices(self, indices: List[int], info_list: List[Any]) -> List[Dict[str, Any]]:
        results = []
        for idx in indices:
            result = self._verify_single_citation(idx, info_list)
            if result:
                results.append(result)
        return results

    def _verify_single_citation(self, idx: int, info_list: List[Any]) -> Dict[str, Any] | None:
        if not (0 < idx <= len(info_list)):
            return None
        snippet = self._get_snippet_text(info_list[idx - 1])
        return self.verifier.verify_citation(snippet, {"text": snippet})

    async def _verify_single_citation_async(self, idx: int, info_list: List[Any]) -> Dict[str, Any] | None:
        if not (0 < idx <= len(info_list)):
            return None
        snippet = self._get_snippet_text(info_list[idx - 1])
        return await self.verifier.verify_citation_async(snippet, {"text": snippet})

    def _get_snippet_text(self, info_item: Any) -> str:
        return info_item.snippets[0] if info_item.snippets else ""

