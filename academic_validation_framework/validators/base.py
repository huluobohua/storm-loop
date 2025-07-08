"""
Base validator interface and common validation utilities.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..models import ValidationResult


@dataclass
class ValidationContext:
    """Context information for validation."""
    
    research_output: Any
    discipline: Optional[str] = None
    methodology: Optional[str] = None
    citation_style: Optional[str] = None
    target_audience: Optional[str] = None
    validation_level: str = "standard"  # "basic", "standard", "comprehensive"
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


class BaseValidator(ABC):
    """
    Base class for all academic validators.
    
    Provides common functionality and interface for validation components.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the validator."""
        if not self._initialized:
            await self._initialize_validator()
            self._initialized = True
    
    @abstractmethod
    async def _initialize_validator(self) -> None:
        """Validator-specific initialization logic."""
        pass
    
    @abstractmethod
    async def validate(
        self, 
        research_output: Any,
        context: Optional[ValidationContext] = None,
        **kwargs: Any
    ) -> Union[ValidationResult, List[ValidationResult]]:
        """
        Validate research output.
        
        Args:
            research_output: The research output to validate
            context: Additional context for validation
            **kwargs: Additional validation parameters
            
        Returns:
            ValidationResult or list of ValidationResults
        """
        pass
    
    async def run_validation_with_timing(
        self,
        research_output: Any,
        context: Optional[ValidationContext] = None,
        **kwargs: Any
    ) -> Union[ValidationResult, List[ValidationResult]]:
        """Run validation with execution timing."""
        await self.initialize()
        
        start_time = time.time()
        try:
            result = await self.validate(research_output, context, **kwargs)
            execution_time = time.time() - start_time
            
            # Add timing information to results
            if isinstance(result, list):
                for r in result:
                    r.execution_time = execution_time / len(result)
            else:
                result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ValidationResult(
                validator_name=self.name,
                test_name="validation_execution",
                status="failed",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                execution_time=execution_time,
            )
            return error_result
    
    def _create_result(
        self,
        test_name: str,
        status: str,
        score: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Create a validation result."""
        return ValidationResult(
            validator_name=self.name,
            test_name=test_name,
            status=status,
            score=score,
            details=details or {},
            metadata=metadata or {},
        )
    
    def _calculate_composite_score(
        self, 
        scores: Dict[str, float], 
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate a weighted composite score."""
        if not scores:
            return 0.0
        
        if weights is None:
            # Equal weights if not specified
            weights = {key: 1.0 for key in scores.keys()}
        
        total_weight = sum(weights.get(key, 1.0) for key in scores.keys())
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            score * weights.get(key, 1.0) 
            for key, score in scores.items()
        )
        
        return weighted_sum / total_weight
    
    def _normalize_score(self, score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Normalize a score to be between min_val and max_val."""
        if max_val <= min_val:
            return min_val
        return max(min_val, min(max_val, score))
    
    def _extract_text_content(self, research_output: Any) -> str:
        """Extract text content from various research output formats."""
        if isinstance(research_output, str):
            return research_output
        elif isinstance(research_output, dict):
            if "content" in research_output:
                return research_output["content"]
            elif "text" in research_output:
                return research_output["text"]
            elif "article" in research_output:
                return research_output["article"]
            else:
                # Try to concatenate all string values
                text_parts = []
                for value in research_output.values():
                    if isinstance(value, str):
                        text_parts.append(value)
                return " ".join(text_parts)
        elif hasattr(research_output, "content"):
            return research_output.content
        elif hasattr(research_output, "text"):
            return research_output.text
        else:
            return str(research_output)
    
    def _extract_citations(self, research_output: Any) -> List[Dict[str, Any]]:
        """Extract citations from research output."""
        citations = []
        
        if isinstance(research_output, dict):
            if "citations" in research_output:
                citations = research_output["citations"]
            elif "references" in research_output:
                citations = research_output["references"]
        elif hasattr(research_output, "citations"):
            citations = research_output.citations
        elif hasattr(research_output, "references"):
            citations = research_output.references
        
        # Ensure citations are in dict format
        if isinstance(citations, list):
            formatted_citations = []
            for citation in citations:
                if isinstance(citation, str):
                    formatted_citations.append({"text": citation})
                elif isinstance(citation, dict):
                    formatted_citations.append(citation)
                else:
                    formatted_citations.append({"text": str(citation)})
            return formatted_citations
        
        return []
    
    def _extract_metadata(self, research_output: Any) -> Dict[str, Any]:
        """Extract metadata from research output."""
        if isinstance(research_output, dict):
            return research_output.get("metadata", {})
        elif hasattr(research_output, "metadata"):
            return research_output.metadata or {}
        else:
            return {}
    
    async def cleanup(self) -> None:
        """Cleanup validator resources."""
        pass
    
    def get_validator_info(self) -> Dict[str, Any]:
        """Get information about this validator."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "config": self.config,
            "initialized": self._initialized,
        }


class CompositeValidator(BaseValidator):
    """
    A validator that combines multiple sub-validators.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        validators: List[BaseValidator],
        combination_strategy: str = "weighted_average",
        weights: Optional[Dict[str, float]] = None,
        **kwargs
    ):
        super().__init__(name, description, **kwargs)
        self.validators = validators
        self.combination_strategy = combination_strategy
        self.weights = weights or {}
    
    async def _initialize_validator(self) -> None:
        """Initialize all sub-validators."""
        await asyncio.gather(
            *[validator.initialize() for validator in self.validators]
        )
    
    async def validate(
        self,
        research_output: Any,
        context: Optional[ValidationContext] = None,
        **kwargs: Any
    ) -> ValidationResult:
        """Run all sub-validators and combine results."""
        sub_results = await asyncio.gather(
            *[
                validator.run_validation_with_timing(research_output, context, **kwargs)
                for validator in self.validators
            ],
            return_exceptions=True
        )
        
        # Filter out exceptions and flatten results
        valid_results = []
        for result in sub_results:
            if not isinstance(result, Exception):
                if isinstance(result, list):
                    valid_results.extend(result)
                else:
                    valid_results.append(result)
        
        # Combine results based on strategy
        if self.combination_strategy == "weighted_average":
            combined_score = self._calculate_weighted_average(valid_results)
        elif self.combination_strategy == "minimum":
            combined_score = min(r.score for r in valid_results if r.score is not None)
        elif self.combination_strategy == "maximum":
            combined_score = max(r.score for r in valid_results if r.score is not None)
        else:
            combined_score = self._calculate_weighted_average(valid_results)
        
        # Determine overall status
        failed_results = [r for r in valid_results if r.failed]
        if failed_results:
            status = "failed"
        elif all(r.passed for r in valid_results):
            status = "passed"
        else:
            status = "warning"
        
        return self._create_result(
            test_name="composite_validation",
            status=status,
            score=combined_score,
            details={
                "sub_results": [
                    {
                        "validator": r.validator_name,
                        "test": r.test_name,
                        "status": r.status,
                        "score": r.score,
                    }
                    for r in valid_results
                ],
                "combination_strategy": self.combination_strategy,
            },
            metadata={
                "sub_validator_count": len(self.validators),
                "valid_results_count": len(valid_results),
                "failed_results_count": len(failed_results),
            }
        )
    
    def _calculate_weighted_average(self, results: List[ValidationResult]) -> float:
        """Calculate weighted average of sub-validator scores."""
        if not results:
            return 0.0
        
        scored_results = [r for r in results if r.score is not None]
        if not scored_results:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for result in scored_results:
            weight = self.weights.get(result.validator_name, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def cleanup(self) -> None:
        """Cleanup all sub-validators."""
        await asyncio.gather(
            *[validator.cleanup() for validator in self.validators],
            return_exceptions=True
        )