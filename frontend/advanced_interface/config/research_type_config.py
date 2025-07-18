"""
Research Type Configuration
Single responsibility for managing research types
"""

from typing import List
from enum import Enum


class ResearchType(Enum):
    """Enumeration of available research types"""
    LITERATURE_REVIEW = "literature_review"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    RESEARCH_PROPOSAL = "research_proposal"


class ResearchTypeConfig:
    """
    Manages research type configuration
    Adheres to Single Responsibility Principle
    """
    
    def __init__(self):
        self.current_research_type = None
    
    def get_research_types(self) -> List[str]:
        """Get available research types"""
        return [rt.value for rt in ResearchType]
    
    def select_research_type(self, research_type: str) -> None:
        """Select research type and configure accordingly"""
        if research_type not in self.get_research_types():
            raise ValueError(f"Invalid research type: {research_type}")
        
        self.current_research_type = research_type
        self._configure_for_research_type(research_type)
    
    def _configure_for_research_type(self, research_type: str) -> None:
        """Configure settings based on research type"""
        # Configuration logic specific to research type
        pass