"""
Research Configuration Schemas
Pydantic schemas for validating research and session configuration
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum


class StormMode(str, Enum):
    """Valid STORM mode options"""
    HYBRID = "hybrid"
    ACADEMIC = "academic"
    FAST = "fast"
    THOROUGH = "thorough"


class AgentType(str, Enum):
    """Valid agent types"""
    ACADEMIC_RESEARCHER = "academic_researcher"
    RESEARCHER = "researcher"
    CRITIC = "critic"
    SYNTHESIZER = "synthesizer"
    FACT_CHECKER = "fact_checker"


class DatabaseType(str, Enum):
    """Valid database types"""
    OPENALEX = "openalex"
    CROSSREF = "crossref"
    PUBMED = "pubmed"
    ARXIV = "arxiv"


class OutputFormat(str, Enum):
    """Valid output formats"""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    DOCX = "docx"
    LATEX = "latex"


class ResearchConfigSchema(BaseModel):
    """
    Schema for validating research configuration
    Provides comprehensive validation with clear error messages
    """
    
    storm_mode: Optional[StormMode] = Field(
        default=StormMode.HYBRID,
        description="STORM research mode"
    )
    
    agents: Optional[List[AgentType]] = Field(
        default=[AgentType.ACADEMIC_RESEARCHER],
        description="List of agents to use in research",
        min_length=1,
        max_length=5
    )
    
    databases: Optional[List[DatabaseType]] = Field(
        default=[DatabaseType.OPENALEX],
        description="List of databases to search",
        min_length=1,
        max_length=10
    )
    
    output_formats: Optional[List[OutputFormat]] = Field(
        default=[OutputFormat.PDF],
        description="Desired output formats",
        min_length=1,
        max_length=5
    )
    
    max_papers: Optional[int] = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of papers to retrieve"
    )
    
    quality_threshold: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Quality threshold for paper selection"
    )
    
    citation_style: Optional[str] = Field(
        default="apa",
        description="Citation style to use"
    )
    
    include_abstracts: Optional[bool] = Field(
        default=True,
        description="Whether to include paper abstracts"
    )
    
    language: Optional[str] = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="Language code for research"
    )
    
    timeout_minutes: Optional[int] = Field(
        default=30,
        ge=1,
        le=1440,  # 24 hours max
        description="Timeout for research process in minutes"
    )
    
    advanced_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Advanced configuration options"
    )
    
    @field_validator('citation_style')
    @classmethod
    def validate_citation_style(cls, v):
        """Validate citation style"""
        valid_styles = ['apa', 'mla', 'chicago', 'ieee', 'harvard']
        if v.lower() not in valid_styles:
            raise ValueError(f"Citation style must be one of: {valid_styles}")
        return v.lower()
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code"""
        # Basic validation for common language codes
        valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko']
        if v.lower() not in valid_languages:
            raise ValueError(f"Language must be one of: {valid_languages}")
        return v.lower()
    
    @model_validator(mode='after')
    def validate_config_consistency(self):
        """Validate overall configuration consistency"""
        storm_mode = self.storm_mode
        agents = self.agents
        max_papers = self.max_papers
        
        # Validate agent compatibility with storm mode
        if storm_mode == StormMode.FAST and len(agents) > 2:
            raise ValueError("Fast mode supports maximum 2 agents")
        
        if storm_mode == StormMode.THOROUGH and max_papers < 20:
            raise ValueError("Thorough mode requires at least 20 papers")
        
        return self
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        extra="forbid"  # Reject unknown fields
    )


class SessionConfigSchema(BaseModel):
    """
    Schema for validating session configuration
    Used for research session setup and management
    """
    
    session_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Name for the research session"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="User identifier"
    )
    
    research_config: Optional[ResearchConfigSchema] = Field(
        default_factory=ResearchConfigSchema,
        description="Research configuration for this session"
    )
    
    session_timeout: Optional[int] = Field(
        default=3600,  # 1 hour
        ge=300,  # 5 minutes min
        le=86400,  # 24 hours max
        description="Session timeout in seconds"
    )
    
    auto_save: Optional[bool] = Field(
        default=True,
        description="Whether to auto-save session progress"
    )
    
    tags: Optional[List[str]] = Field(
        default_factory=list,
        max_length=10,
        description="Tags for organizing sessions"
    )
    
    priority: Optional[str] = Field(
        default="normal",
        description="Session priority level"
    )
    
    @field_validator('session_name')
    @classmethod
    def validate_session_name(cls, v):
        """Validate session name"""
        if v is None:
            return v
        
        # Remove excessive whitespace and validate
        v = v.strip()
        if not v:
            raise ValueError("Session name cannot be empty")
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Session name contains invalid characters: {invalid_chars}")
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags"""
        if not v:
            return v
        
        # Validate each tag
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if tag and len(tag) <= 20:
                validated_tags.append(tag)
        
        return validated_tags
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority level"""
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v.lower()
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"  # Reject unknown fields
    )