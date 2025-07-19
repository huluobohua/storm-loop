"""
Source Mapper

Maintains mapping between retrieved papers and generated citations.
Ensures provenance tracking for citation integrity.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from .models import Citation


@dataclass
class PaperSource:
    """
    Represents a source paper from academic databases.
    
    Links to original search results and retrieval metadata.
    """
    paper_id: str
    title: str
    authors: List[str]
    journal: str
    year: int
    doi: Optional[str] = None
    source_database: str = "unknown"


class SourceMapper:
    """
    Maps citations to their source papers.
    
    Maintains bidirectional mapping for provenance tracking.
    Follows single responsibility principle.
    """
    
    def __init__(self):
        """Initialize empty mapping storage."""
        self._paper_to_citations: Dict[str, Set[Citation]] = {}
        self._citation_to_paper: Dict[Citation, PaperSource] = {}
    
    def add_mapping(self, citation: Citation, source: PaperSource) -> None:
        """
        Add mapping between citation and source paper.
        
        Maintains bidirectional relationship for efficient lookup.
        """
        # Add to citation -> paper mapping
        self._citation_to_paper[citation] = source
        
        # Add to paper -> citations mapping
        if source.paper_id not in self._paper_to_citations:
            self._paper_to_citations[source.paper_id] = set()
        self._paper_to_citations[source.paper_id].add(citation)
    
    def get_source(self, citation: Citation) -> Optional[PaperSource]:
        """Get source paper for citation."""
        return self._citation_to_paper.get(citation)
    
    def get_citations(self, paper_id: str) -> Set[Citation]:
        """Get all citations for source paper."""
        return self._paper_to_citations.get(paper_id, set())
    
    def has_source(self, citation: Citation) -> bool:
        """Check if citation has mapped source."""
        return citation in self._citation_to_paper
    
    def remove_mapping(self, citation: Citation) -> bool:
        """
        Remove mapping for citation.
        
        Returns True if mapping existed and was removed.
        """
        source = self._citation_to_paper.pop(citation, None)
        if source:
            self._paper_to_citations[source.paper_id].discard(citation)
            return True
        return False
    
    def get_orphaned_citations(self, citations: List[Citation]) -> List[Citation]:
        """
        Find citations without source mappings.
        
        These are potentially fabricated citations.
        """
        return [c for c in citations if not self.has_source(c)]
    
    def get_mapping_count(self) -> int:
        """Get total number of citation mappings."""
        return len(self._citation_to_paper)
    
    def clear_mappings(self) -> None:
        """Clear all mappings."""
        self._paper_to_citations.clear()
        self._citation_to_paper.clear()