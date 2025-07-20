"""
Configuration Validation Service
Handles validation of research and session configurations
Following Single Responsibility Principle
"""

from typing import Dict, Any
from pydantic import ValidationError
from .schemas import ResearchConfigSchema, SessionConfigSchema


class ConfigValidator:
    """Validates configuration dictionaries using Pydantic schemas"""
    
    def validate_research_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize research configuration"""
        validated = ResearchConfigSchema(**config)
        return validated.model_dump()
    
    def validate_session_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize session configuration"""
        validated = SessionConfigSchema(**config)
        return validated.model_dump()