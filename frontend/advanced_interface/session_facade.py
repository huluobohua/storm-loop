"""
Session Management Facade
Handles session creation, configuration, and status operations
Following Single Responsibility Principle
"""

from typing import Dict, Any
from .research_session_manager import ResearchSessionManager
from .config_validator import ConfigValidator


class SessionFacade:
    """Facade for session management operations"""
    
    def __init__(self, session_manager: ResearchSessionManager = None, 
                 config_validator: ConfigValidator = None):
        """Initialize with dependency injection"""
        self.session_manager = session_manager or ResearchSessionManager()
        self.config_validator = config_validator or ConfigValidator()
    
    def create_research_session(self, user_id: str, session_name: str) -> str:
        """Create new research session"""
        return self.session_manager.create_session(user_id, session_name)
    
    def configure_session(self, session_id: str, config: Dict[str, Any]) -> None:
        """Configure research session with validation"""
        validated_config = self.config_validator.validate_session_config(config)
        return self.session_manager.configure_session(session_id, validated_config)
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get session configuration"""
        return self.session_manager.get_session_config(session_id)