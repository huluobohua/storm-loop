"""
Research Configuration Dashboard
Implements research type selection, STORM mode control, and agent configuration
Following Single Responsibility Principle and Sandi Metz rules
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import from knowledge_storm package directly
try:
    from knowledge_storm.storm_config import STORMConfig
    from knowledge_storm.config_validators import STORMMode
except ImportError:
    # Fallback for development environments
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge_storm.storm_config import STORMConfig
    from knowledge_storm.config_validators import STORMMode


@dataclass
class DateRange:
    """Value object for date range configuration"""
    start: str
    end: str


@dataclass
class CitationRequirements:
    """Value object for citation requirements"""
    min_citations: int
    max_age_years: int


class ResearchType(Enum):
    """Enumeration of available research types"""
    LITERATURE_REVIEW = "literature_review"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    RESEARCH_PROPOSAL = "research_proposal"


class ResearchConfigDashboard:
    """
    Main dashboard for research configuration
    Adheres to Single Responsibility Principle - only manages research configuration
    """
    
    def __init__(self):
        self.storm_config = STORMConfig()
        self.current_research_type = None
        self.selected_agents = []
        self.selected_databases = []
        self.date_range = None
        self.inclusion_criteria = []
        self.exclusion_criteria = []
        self.research_depth = "standard"
        self.citation_requirements = None
        self.bias_detection_level = "moderate"
        self._agent_configs = {}
    
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
        if research_type == "systematic_review":
            self.storm_config.prisma_screening_enabled = True
            self.storm_config.quality_gates_strict = True
    
    def get_research_config(self) -> STORMConfig:
        """Get current research configuration"""
        return self.storm_config
    
    def set_storm_mode(self, mode: str) -> None:
        """Set STORM mode"""
        self.storm_config.switch_mode(mode)
        # Store current mode for testing
        self.storm_config.current_mode = self.storm_config._current_mode
    
    def get_available_agents(self) -> List[str]:
        """Get available agent types"""
        return [
            "academic_researcher",
            "critic", 
            "citation_verifier",
            "writer",
            "research_planner"
        ]
    
    def select_agents(self, agents: List[str]) -> None:
        """Select agents for research"""
        available = self.get_available_agents()
        for agent in agents:
            if agent not in available:
                raise ValueError(f"Invalid agent: {agent}")
        
        self.selected_agents = agents
    
    def configure_agent(self, agent_name: str, config: Dict[str, Any]) -> None:
        """Configure specific agent"""
        if agent_name not in self.get_available_agents():
            raise ValueError(f"Invalid agent: {agent_name}")
        
        self._agent_configs[agent_name] = config
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get agent configuration"""
        return self._agent_configs.get(agent_name, {})
    
    def select_databases(self, databases: List[str]) -> None:
        """Select databases for research"""
        self.selected_databases = databases
    
    def set_date_range(self, start: str, end: str) -> None:
        """Set date range for research"""
        self.date_range = DateRange(start, end)
    
    def set_inclusion_criteria(self, criteria: List[str]) -> None:
        """Set inclusion criteria"""
        self.inclusion_criteria = criteria
    
    def set_exclusion_criteria(self, criteria: List[str]) -> None:
        """Set exclusion criteria"""
        self.exclusion_criteria = criteria
    
    def set_research_depth(self, depth: str) -> None:
        """Set research depth"""
        self.research_depth = depth
    
    def set_citation_requirements(self, min_citations: int, max_age_years: int) -> None:
        """Set citation requirements"""
        self.citation_requirements = CitationRequirements(min_citations, max_age_years)
    
    def set_bias_detection_level(self, level: str) -> None:
        """Set bias detection level"""
        self.bias_detection_level = level