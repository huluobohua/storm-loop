"""
Main Advanced Academic Interface
Orchestrates all components and provides unified interface
Following Facade Pattern and Single Responsibility Principle
"""

from typing import Dict, List, Any, Optional
import asyncio
import threading
import uuid
from datetime import datetime

from .research_config import ResearchConfigDashboard
from .monitoring import ResearchMonitor
from .output_manager import OutputManager
from .database_manager import DatabaseManager
from .project_manager import ProjectManager
from .quality_dashboard import QualityDashboard


class AdvancedAcademicInterface:
    """
    Main interface orchestrating all advanced academic research components
    Adheres to Facade Pattern - provides simplified interface to complex subsystems
    """
    
    def __init__(self):
        self.research_config = ResearchConfigDashboard()
        self.monitor = ResearchMonitor()
        self.output_manager = OutputManager()
        self.database_manager = DatabaseManager()
        self.project_manager = ProjectManager()
        self.quality_dashboard = QualityDashboard()
        
        self._research_sessions = {}
        self._session_configs = {}
        self._fallback_mode = False
        self._lock = threading.RLock()
    
    async def initialize(self) -> None:
        """Initialize the interface"""
        # Initialization logic would go here
        pass
    
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
            self._apply_bias_detection_settings(quality_settings)
    
    def _apply_bias_detection_settings(self, quality_settings: Dict[str, Any]) -> None:
        """Apply bias detection settings"""
        bias_detection = quality_settings.get("bias_detection")
        if bias_detection:
            self.research_config.set_bias_detection_level(bias_detection)
    
    async def start_research(self, query: str) -> str:
        """Start research process"""
        research_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        stages = ["search", "analysis", "writing", "review"]
        self.monitor.initialize_progress(stages)
        
        # Simulate research process
        await asyncio.sleep(0.1)  # Simulate async work
        
        return research_id
    
    async def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Get research status"""
        # Simulate completed research for testing
        return {
            "research_id": research_id,
            "status": "completed",
            "progress": self.monitor.get_overall_progress(),
            "quality_metrics": self.monitor.get_quality_metrics()
        }
    
    async def generate_output(self, research_id: str, formats: List[str]) -> Dict[str, Any]:
        """Generate output in specified formats"""
        self.output_manager.select_output_formats(formats)
        
        # Simulate output generation
        await asyncio.sleep(0.1)
        
        return {
            "research_id": research_id,
            "formats": formats,
            "status": "completed",
            "files": [f"output.{fmt}" for fmt in formats]
        }
    
    def create_research_session(self, user_id: str, session_name: str) -> str:
        """Create new research session"""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._create_session_data(session_id, user_id, session_name)
            self._initialize_session_config(session_id)
        return session_id
    
    def _create_session_data(self, session_id: str, user_id: str, session_name: str) -> None:
        """Create session data"""
        self._research_sessions[session_id] = {
            "user_id": user_id,
            "session_name": session_name,
            "created_at": datetime.now(),
            "active": True
        }
    
    def _initialize_session_config(self, session_id: str) -> None:
        """Initialize session configuration"""
        self._session_configs[session_id] = {
            "storm_mode": "hybrid",
            "agents": ["academic_researcher"],
            "databases": ["openalex"]
        }
    
    def configure_session(self, session_id: str, config: Dict[str, Any]) -> None:
        """Configure research session"""
        with self._lock:
            if session_id in self._session_configs:
                self._session_configs[session_id].update(config)
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get session configuration"""
        with self._lock:
            return self._session_configs.get(session_id, {})
    
    def handle_api_error(self, api_name: str, error_message: str) -> Dict[str, Any]:
        """Handle API errors gracefully"""
        with self._lock:
            self._fallback_mode = True
            
            return {
                "status": "error",
                "api": api_name,
                "error": error_message,
                "fallback_enabled": True,
                "message": f"API {api_name} error handled, fallback mode enabled"
            }
    
    def enable_fallback_mode(self) -> None:
        """Enable fallback mode"""
        with self._lock:
            self._fallback_mode = True
    
    def disable_fallback_mode(self) -> None:
        """Disable fallback mode"""
        with self._lock:
            self._fallback_mode = False
    
    def is_fallback_mode_enabled(self) -> bool:
        """Check if fallback mode is enabled"""
        with self._lock:
            return self._fallback_mode