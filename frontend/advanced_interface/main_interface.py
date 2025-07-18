"""
Main Advanced Academic Interface
Simplified facade orchestrating focused components
Following Facade Pattern and Single Responsibility Principle
"""

from typing import Dict, List, Any, Optional
from .config_validator import ConfigValidator
from .session_facade import SessionFacade
from .research_config import ResearchConfigDashboard
from .monitoring import ResearchMonitor
from .output_manager import OutputManager
from .database_manager import DatabaseManager
from .project_manager import ProjectManager
from .quality_dashboard import QualityDashboard
from .research_process_orchestrator import ResearchProcessOrchestrator
from .error_handling_service import ErrorHandlingService


class AdvancedAcademicInterface:
    """
    Simplified facade interface for advanced academic research
    Delegates to focused components following Single Responsibility Principle
    """
    
    def __init__(self, 
                 research_config: Optional[ResearchConfigDashboard] = None,
                 monitor: Optional[ResearchMonitor] = None,
                 output_manager: Optional[OutputManager] = None,
                 database_manager: Optional[DatabaseManager] = None,
                 project_manager: Optional[ProjectManager] = None,
                 quality_dashboard: Optional[QualityDashboard] = None,
                 session_manager = None,  # Backwards compatibility
                 error_service: Optional[ErrorHandlingService] = None):
        """Initialize with dependency injection"""
        self.config_validator = ConfigValidator()
        self.session_facade = SessionFacade()
        self.database_manager = database_manager or DatabaseManager()
        self.project_manager = project_manager or ProjectManager()
        self.quality_dashboard = quality_dashboard or QualityDashboard()
        self.error_service = error_service or ErrorHandlingService()
        # Initialize process orchestrator with dependencies
        research_config = research_config or ResearchConfigDashboard()
        monitor = monitor or ResearchMonitor()
        output_manager = output_manager or OutputManager()
        self.process_orchestrator = ResearchProcessOrchestrator(
            monitor, research_config, output_manager
        )
    
    # Research Configuration Delegation
    async def configure_research(self, config: Dict[str, Any]) -> None:
        """Configure research settings with validation"""
        validated_config = self.config_validator.validate_research_config(config)
        return await self.process_orchestrator.configure_research(validated_config)
    
    # Research Process Delegation
    async def start_research(self, query: str) -> str:
        """Start research process"""
        return await self.process_orchestrator.start_research(query)
    
    async def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Get research status"""
        return await self.process_orchestrator.get_research_status(research_id)
    
    async def generate_output(self, research_id: str, formats: List[str]) -> Dict[str, Any]:
        """Generate output in specified formats"""
        return await self.process_orchestrator.generate_output(research_id, formats)
    
    # Session Management Delegation
    def create_research_session(self, user_id: str, session_name: str) -> str:
        """Create new research session"""
        return self.session_facade.create_research_session(user_id, session_name)
    
    def configure_session(self, session_id: str, config: Dict[str, Any]) -> None:
        """Configure research session with validation"""
        return self.session_facade.configure_session(session_id, config)
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get session configuration"""
        return self.session_facade.get_session_config(session_id)
    
    # Error Handling Delegation
    def handle_api_error(self, api_name: str, error_message: str) -> Dict[str, Any]:
        """Handle API errors gracefully"""
        return self.error_service.handle_api_error(api_name, error_message)
    
    def enable_fallback_mode(self) -> None:
        """Enable fallback mode"""
        return self.error_service.enable_fallback_mode()
    
    def disable_fallback_mode(self) -> None:
        """Disable fallback mode"""
        return self.error_service.disable_fallback_mode()
    
    def is_fallback_mode_enabled(self) -> bool:
        """Check if fallback mode is enabled"""
        return self.error_service.is_fallback_mode_enabled()