"""
Error Handling Service
Manages error handling and fallback modes
Following Single Responsibility Principle
"""

from typing import Dict, Any
import threading


class ErrorHandlingService:
    """
    Manages error handling and fallback modes
    Adheres to Single Responsibility Principle - only handles errors and fallbacks
    """
    
    def __init__(self):
        self._fallback_mode = False
        self._lock = threading.RLock()
    
    def handle_api_error(self, api_name: str, error_message: str) -> Dict[str, Any]:
        """Handle API errors gracefully"""
        with self._lock:
            self._fallback_mode = True
            return self._build_error_response(api_name, error_message)
    
    def _build_error_response(self, api_name: str, error_message: str) -> Dict[str, Any]:
        """Build error response dictionary"""
        return {"status": "error", "api": api_name, "error": error_message,
                "fallback_enabled": True,
                "message": f"API {api_name} error handled, fallback mode enabled"}
    
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