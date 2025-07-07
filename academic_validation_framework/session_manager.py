"""
Session management for validation sessions.
"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid
import logging
from threading import Lock

from .models import ValidationSession, ValidationRequest, ValidationResult, PerformanceMetrics
from .config import FrameworkConfig

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages validation sessions lifecycle."""
    
    def __init__(self, config: Optional[FrameworkConfig] = None):
        """
        Initialize session manager.
        
        Args:
            config: Framework configuration
        """
        self.config = config or FrameworkConfig()
        self._sessions: Dict[str, ValidationSession] = {}
        self._lock = Lock()
        self._session_limit = self.config.max_sessions
        
    def create_session(self, request: ValidationRequest) -> str:
        """
        Create a new validation session.
        
        Args:
            request: Validation request
            
        Returns:
            Session ID
            
        Raises:
            RuntimeError: If session limit exceeded
        """
        with self._lock:
            # Check session limit
            active_sessions = sum(
                1 for s in self._sessions.values() 
                if s.status == "in_progress"
            )
            
            if active_sessions >= self._session_limit:
                raise RuntimeError(
                    f"Session limit exceeded: {active_sessions}/{self._session_limit} active sessions"
                )
            
            # Create new session
            session_id = str(uuid.uuid4())
            session = ValidationSession(
                session_id=session_id,
                request=request,
                metadata={
                    "created_by": "SessionManager",
                    "framework_version": self.config.version
                }
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created session: {session_id}")
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[ValidationSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, any]) -> None:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply
            
        Raises:
            KeyError: If session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
                else:
                    session.metadata[key] = value
            
            logger.debug(f"Updated session {session_id}: {list(updates.keys())}")
    
    def add_result(self, session_id: str, result: ValidationResult) -> None:
        """
        Add a validation result to a session.
        
        Args:
            session_id: Session identifier
            result: Validation result to add
            
        Raises:
            KeyError: If session not found
            RuntimeError: If session already completed
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            
            if session.status == "completed":
                raise RuntimeError(f"Cannot add results to completed session: {session_id}")
            
            session.results.append(result)
            logger.debug(f"Added result to session {session_id}: {result.validator_name}")
    
    def set_performance_metrics(self, session_id: str, metrics: PerformanceMetrics) -> None:
        """
        Set performance metrics for a session.
        
        Args:
            session_id: Session identifier
            metrics: Performance metrics
            
        Raises:
            KeyError: If session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            self._sessions[session_id].performance_metrics = metrics
            logger.debug(f"Set performance metrics for session {session_id}")
    
    def close_session(self, session_id: str) -> None:
        """
        Close and finalize a session.
        
        Args:
            session_id: Session identifier
            
        Raises:
            KeyError: If session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            session.end_time = datetime.now()
            session.status = "completed"
            
            # Calculate final statistics
            session.metadata["final_stats"] = {
                "total_results": len(session.results),
                "passed": session.passed_count,
                "failed": session.failed_count,
                "success_rate": session.success_rate,
                "duration": session.duration
            }
            
            logger.info(f"Closed session {session_id}: {session.metadata['final_stats']}")
    
    def fail_session(self, session_id: str, error: str) -> None:
        """
        Mark a session as failed.
        
        Args:
            session_id: Session identifier
            error: Error message
            
        Raises:
            KeyError: If session not found
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            session.end_time = datetime.now()
            session.status = "failed"
            session.metadata["error"] = error
            
            logger.error(f"Failed session {session_id}: {error}")
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return [
            sid for sid, session in self._sessions.items()
            if session.status == "in_progress"
        ]
    
    def get_session_history(self, limit: Optional[int] = None) -> List[ValidationSession]:
        """
        Get session history.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions, newest first
        """
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        
        if limit:
            return sessions[:limit]
        return sessions
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Remove sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions removed
        """
        with self._lock:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            sessions_to_remove = []
            
            for sid, session in self._sessions.items():
                if session.status == "completed" and session.end_time:
                    if session.end_time.timestamp() < cutoff_date:
                        sessions_to_remove.append(sid)
            
            for sid in sessions_to_remove:
                del self._sessions[sid]
            
            if sessions_to_remove:
                logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
            
            return len(sessions_to_remove)
    
    def get_statistics(self) -> Dict[str, any]:
        """Get session manager statistics."""
        total_sessions = len(self._sessions)
        active_sessions = len(self.get_active_sessions())
        completed_sessions = sum(
            1 for s in self._sessions.values() 
            if s.status == "completed"
        )
        failed_sessions = sum(
            1 for s in self._sessions.values() 
            if s.status == "failed"
        )
        
        # Calculate average success rate
        success_rates = [
            s.success_rate for s in self._sessions.values()
            if s.status == "completed" and s.total_count > 0
        ]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "average_success_rate": avg_success_rate,
            "session_limit": self._session_limit
        }