"""Task result data structures for agent communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class TaskResult:
    """
    Immutable result structure for agent task execution.
    
    Provides type safety and structured data exchange between agents
    while maintaining backward compatibility with string results.
    
    Attributes:
        success: Whether the task completed successfully
        data: The main result data (can be any type)
        error_message: Error description if task failed
        metadata: Additional context information
    """
    success: bool
    data: Union[str, Dict[str, Any], List[Any]]
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        """String representation for backward compatibility."""
        if isinstance(self.data, str):
            return self.data
        elif isinstance(self.data, dict) and 'topic' in self.data:
            return f"Research plan for: {self.data['topic']}"
        return str(self.data)
    
    @classmethod
    def success_result(
        cls, 
        data: Union[str, Dict[str, Any], List[Any]], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Create a successful task result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod 
    def error_result(
        cls, 
        error_message: str, 
        fallback_data: Optional[Union[str, Dict[str, Any], List[Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Create an error task result with optional fallback data."""
        return cls(
            success=False, 
            data=fallback_data or error_message,
            error_message=error_message,
            metadata=metadata
        )


@dataclass(frozen=True)
class ResearchPlan:
    """
    Structured research plan data with type safety.
    
    Replaces ad-hoc dictionary structures with proper typing
    and validation for research planning results.
    
    Attributes:
        topic: The research topic
        complexity: Complexity score (1-10)
        steps: List of research steps
        estimated_time: Time estimate in hours
        perspectives: Optional research perspectives
        error_context: Error information if planning had issues
    """
    topic: str
    complexity: int
    steps: List[str]
    estimated_time: int
    perspectives: Optional[List[str]] = None
    error_context: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate data constraints."""
        if self.complexity < 1 or self.complexity > 10:
            raise ValueError(f"Complexity must be 1-10, got {self.complexity}")
        if self.estimated_time < 0:
            raise ValueError(f"Estimated time must be non-negative, got {self.estimated_time}")
        if not self.steps:
            raise ValueError("Steps list cannot be empty")
    
    def to_dict(self) -> Dict[str, Union[str, int, List[str]]]:
        """Convert to dictionary for backward compatibility."""
        result = {
            "topic": self.topic,
            "complexity": self.complexity, 
            "steps": self.steps,
            "estimated_time": self.estimated_time
        }
        if self.perspectives:
            result["perspectives"] = self.perspectives
        if self.error_context:
            result["error"] = self.error_context
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResearchPlan:
        """Create from dictionary data."""
        return cls(
            topic=data["topic"],
            complexity=data["complexity"],
            steps=data["steps"],
            estimated_time=data["estimated_time"],
            perspectives=data.get("perspectives"),
            error_context=data.get("error")
        )