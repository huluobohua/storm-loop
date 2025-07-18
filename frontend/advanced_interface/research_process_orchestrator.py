"""
Research Process Orchestrator
Orchestrates research process execution and monitoring
Following Single Responsibility Principle
"""

from typing import Dict, List, Any
import asyncio
import uuid


class ResearchProcessOrchestrator:
    """
    Orchestrates research process execution
    Adheres to Single Responsibility Principle - only manages research processes
    """
    
    def __init__(self, monitor, research_config, output_manager):
        self.monitor = monitor
        self.research_config = research_config
        self.output_manager = output_manager
    
    async def start_research(self, query: str) -> str:
        """Start research process"""
        research_id = str(uuid.uuid4())
        self._initialize_tracking()
        await self._simulate_work()
        return research_id
    
    def _initialize_tracking(self) -> None:
        """Initialize progress tracking for research"""
        stages = ["search", "analysis", "writing", "review"]
        self.monitor.initialize_progress(stages)
    
    async def _simulate_work(self) -> None:
        """Simulate research work with async delay"""
        await asyncio.sleep(0.1)
    
    async def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Get research status"""
        return self._build_status(research_id)
    
    def _build_status(self, research_id: str) -> Dict[str, Any]:
        """Build research status dictionary"""
        return {"research_id": research_id, "status": "completed", 
                "progress": self.monitor.get_overall_progress(),
                "quality_metrics": self.monitor.get_quality_metrics()}
    
    async def configure_research(self, config: Dict[str, Any]) -> None:
        """Configure research settings"""
        self._configure_research_type(config)
        self._configure_storm_mode(config)
        self._configure_agents_and_databases(config)
        self._configure_quality_settings(config)
    
    def _configure_research_type(self, config: Dict[str, Any]) -> None:
        """Configure research type"""
        research_type = config.get("research_type")
        if research_type:
            self.research_config.select_research_type(research_type)
    
    def _configure_storm_mode(self, config: Dict[str, Any]) -> None:
        """Configure STORM mode"""
        storm_mode = config.get("storm_mode")
        if storm_mode:
            self.research_config.set_storm_mode(storm_mode)
    
    def _configure_agents_and_databases(self, config: Dict[str, Any]) -> None:
        """Configure agents and databases"""
        self._configure_agents(config)
        self._configure_databases(config)
    
    def _configure_agents(self, config: Dict[str, Any]) -> None:
        """Configure agents"""
        agents = config.get("agents")
        if agents:
            self.research_config.select_agents(agents)
    
    def _configure_databases(self, config: Dict[str, Any]) -> None:
        """Configure databases"""
        databases = config.get("databases")
        if databases:
            self.research_config.select_databases(databases)
    
    def _configure_quality_settings(self, config: Dict[str, Any]) -> None:
        """Configure quality settings"""
        quality_settings = config.get("quality_settings")
        if quality_settings:
            self._apply_bias_detection(quality_settings)
    
    def _apply_bias_detection(self, quality_settings: Dict[str, Any]) -> None:
        """Apply bias detection settings"""
        bias_detection = quality_settings.get("bias_detection")
        if bias_detection:
            self.research_config.set_bias_detection_level(bias_detection)
    
    async def generate_output(self, research_id: str, formats: List[str]) -> Dict[str, Any]:
        """Generate output in specified formats"""
        self.output_manager.select_output_formats(formats)
        await self._simulate_output_generation()
        return self._build_output_result(research_id, formats)
    
    async def _simulate_output_generation(self) -> None:
        """Simulate output generation with async delay"""
        await asyncio.sleep(0.1)
    
    def _build_output_result(self, research_id: str, formats: List[str]) -> Dict[str, Any]:
        """Build output generation result"""
        return {"research_id": research_id, "formats": formats,
                "status": "completed", "files": [f"output.{fmt}" for fmt in formats]}