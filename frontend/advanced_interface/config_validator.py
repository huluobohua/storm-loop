"""
Configuration Validation Service
Handles validation of research and session configurations
Following Single Responsibility Principle
"""

from typing import Dict, Any
from .schemas import ResearchConfigSchema, SessionConfigSchema


class ConfigValidator:
    """Validates configuration dictionaries using Pydantic schemas"""
    
    def validate_research_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize research configuration"""
        try:
            validated = ResearchConfigSchema(**config)
            return validated.model_dump()
        except Exception as e:
            raise ValueError(f"Invalid research configuration: {e}")
    
    def validate_session_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize session configuration"""
        try:
            # Validate nested research_config if present
            if 'research_config' in config:
                validated_research = ResearchConfigSchema(**config['research_config'])
                config['research_config'] = validated_research.model_dump()
            return config
        except Exception as e:
            raise ValueError(f"Invalid session configuration: {e}")