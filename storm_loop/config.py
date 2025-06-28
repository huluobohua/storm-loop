"""
Configuration management for STORM-Loop
"""
import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from enum import Enum


class OperationMode(str, Enum):
    """Operation modes for STORM-Loop"""
    ACADEMIC = "academic"
    WIKIPEDIA = "wikipedia" 
    HYBRID = "hybrid"


class STORMLoopConfig(BaseSettings):
    """Main configuration class for STORM-Loop"""
    
    # Operation Mode
    mode: OperationMode = Field(default=OperationMode.HYBRID, description="Operation mode")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    perplexity_api_key: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Academic APIs
    enable_openalex: bool = Field(default=True, description="Enable OpenAlex integration")
    enable_crossref: bool = Field(default=True, description="Enable Crossref integration")
    openalex_email: Optional[str] = Field(default=None, env="OPENALEX_EMAIL")
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=10, description="Max concurrent API requests")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Quality Assurance
    min_source_quality_score: float = Field(default=0.7, description="Minimum source quality score")
    enable_citation_verification: bool = Field(default=True, description="Enable citation verification")
    enable_grammar_checking: bool = Field(default=True, description="Enable grammar checking")
    
    # Multi-Agent Settings
    max_agent_workers: int = Field(default=5, description="Maximum number of agent workers")
    agent_timeout: int = Field(default=120, description="Agent timeout in seconds")
    
    # Database
    database_url: str = Field(default="sqlite:///storm_loop.db", env="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_monitoring: bool = Field(default=False, description="Enable Prometheus monitoring")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global configuration instance
config = STORMLoopConfig()


def get_config() -> STORMLoopConfig:
    """Get the global configuration instance"""
    return config


def update_config(**kwargs) -> None:
    """Update configuration values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")