"""
Research Session Manager
Handles session creation, configuration, and management
Following Single Responsibility Principle
"""

from typing import Dict, List, Any
import threading
import uuid
from datetime import datetime


class ResearchSessionManager:
    """
    Manages research sessions
    Adheres to Single Responsibility Principle - only manages sessions
    """
    
    def __init__(self):
        self._research_sessions = {}
        self._session_configs = {}
        self._lock = threading.RLock()
    
    def create_session(self, user_id: str, session_name: str) -> str:
        """Create new research session"""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._create_session_data(session_id, user_id, session_name)
            self._initialize_session_config(session_id)
        return session_id
    
    def _create_session_data(self, session_id: str, user_id: str, session_name: str) -> None:
        """Create session data"""
        session_data = self._build_session_data(user_id, session_name)
        self._research_sessions[session_id] = session_data
    
    def _build_session_data(self, user_id: str, session_name: str) -> Dict[str, Any]:
        """Build session data dictionary"""
        return {"user_id": user_id, "session_name": session_name,
                "created_at": datetime.now(), "active": True}
    
    def _initialize_session_config(self, session_id: str) -> None:
        """Initialize session configuration"""
        config = self._build_default_config()
        self._session_configs[session_id] = config
    
    def _build_default_config(self) -> Dict[str, Any]:
        """Build default session configuration"""
        return {"storm_mode": "hybrid", "agents": ["academic_researcher"],
                "databases": ["openalex"]}
    
    def configure_session(self, session_id: str, config: Dict[str, Any]) -> None:
        """Configure research session"""
        with self._lock:
            if session_id in self._session_configs:
                self._session_configs[session_id].update(config)
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get session configuration"""
        with self._lock:
            return self._session_configs.get(session_id, {})
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        with self._lock:
            return self._research_sessions.get(session_id, {})
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        with self._lock:
            return session_id in self._research_sessions