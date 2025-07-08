"""
Citation Format Strategy Registry

Manages registration, discovery, and orchestration of citation format
validation strategies following the Registry pattern.
"""

from typing import Dict, List, Optional, Type, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import importlib
import inspect

from .base import CitationFormatStrategy, FormatValidationResult


@dataclass
class StrategyMetadata:
    """Metadata for a registered strategy."""
    strategy_class: Type[CitationFormatStrategy]
    name: str
    version: str
    supported_types: List[str]
    priority: int = 50  # Higher priority = preferred for auto-detection
    is_enabled: bool = True
    registration_time: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


@dataclass 
class ValidationStatistics:
    """Validation statistics for performance monitoring."""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    average_processing_time: float = 0.0
    average_confidence: float = 0.0
    format_distribution: Dict[str, int] = field(default_factory=dict)
    error_patterns: Dict[str, int] = field(default_factory=dict)


class CitationFormatRegistry:
    """
    Registry for citation format validation strategies.
    
    Provides a centralized system for registering, discovering, and
    managing citation format validators with performance monitoring
    and auto-detection capabilities.
    """
    
    def __init__(self):
        self._strategies: Dict[str, StrategyMetadata] = {}
        self._statistics = ValidationStatistics()
        self._auto_detection_cache: Dict[str, str] = {}
        self._initialized = False
    
    def register_strategy(
        self,
        strategy_class: Type[CitationFormatStrategy],
        priority: int = 50,
        is_enabled: bool = True
    ) -> bool:
        """
        Register a citation format strategy.
        
        Args:
            strategy_class: Strategy class to register
            priority: Priority for auto-detection (higher = preferred)
            is_enabled: Whether strategy is enabled
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate strategy class
            if not issubclass(strategy_class, CitationFormatStrategy):
                raise ValueError(f"Strategy class must inherit from CitationFormatStrategy")
            
            # Create instance to get metadata
            instance = strategy_class()
            
            # Check for required properties
            required_properties = ['format_name', 'format_version', 'supported_types']
            for prop in required_properties:
                if not hasattr(instance, prop):
                    raise ValueError(f"Strategy missing required property: {prop}")
            
            format_name = instance.format_name.lower()
            
            # Check for duplicates
            if format_name in self._strategies:
                existing = self._strategies[format_name]
                if existing.strategy_class == strategy_class:
                    # Update existing registration
                    existing.priority = priority
                    existing.is_enabled = is_enabled
                    existing.registration_time = datetime.now()
                    return True
                else:
                    raise ValueError(f"Strategy '{format_name}' already registered with different class")
            
            # Register strategy
            metadata = StrategyMetadata(
                strategy_class=strategy_class,
                name=format_name,
                version=instance.format_version,
                supported_types=instance.supported_types,
                priority=priority,
                is_enabled=is_enabled
            )
            
            self._strategies[format_name] = metadata
            
            # Initialize format distribution tracking
            self._statistics.format_distribution[format_name] = 0
            
            return True
            
        except Exception as e:
            print(f"Failed to register strategy {strategy_class.__name__}: {e}")
            return False
    
    def unregister_strategy(self, format_name: str) -> bool:
        """
        Unregister a citation format strategy.
        
        Args:
            format_name: Name of format to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        format_name = format_name.lower()
        if format_name in self._strategies:
            del self._strategies[format_name]
            # Clear from cache
            self._auto_detection_cache = {
                k: v for k, v in self._auto_detection_cache.items() 
                if v != format_name
            }
            return True
        return False
    
    def get_strategy(self, format_name: str, strict_mode: bool = False) -> Optional[CitationFormatStrategy]:
        """
        Get a strategy instance by format name.
        
        Args:
            format_name: Name of format
            strict_mode: Whether to use strict validation mode
            
        Returns:
            Strategy instance or None if not found
        """
        format_name = format_name.lower()
        metadata = self._strategies.get(format_name)
        
        if metadata and metadata.is_enabled:
            try:
                instance = metadata.strategy_class(strict_mode=strict_mode)
                
                # Update usage statistics
                metadata.usage_count += 1
                metadata.last_used = datetime.now()
                
                return instance
            except Exception as e:
                print(f"Failed to create strategy instance for {format_name}: {e}")
        
        return None
    
    def get_available_formats(self, include_disabled: bool = False) -> List[str]:
        """
        Get list of available format names.
        
        Args:
            include_disabled: Whether to include disabled strategies
            
        Returns:
            List of format names
        """
        if include_disabled:
            return list(self._strategies.keys())
        else:
            return [
                name for name, metadata in self._strategies.items()
                if metadata.is_enabled
            ]
    
    def auto_detect_format(self, citations: List[str]) -> Optional[str]:
        """
        Auto-detect the most likely citation format.
        
        Args:
            citations: List of citations to analyze
            
        Returns:
            Format name or None if detection fails
        """
        if not citations:
            return None
        
        # Check cache first
        cache_key = hash(tuple(citations[:3]))  # Use first 3 citations for cache key
        if cache_key in self._auto_detection_cache:
            cached_format = self._auto_detection_cache[cache_key]
            if cached_format in self._strategies and self._strategies[cached_format].is_enabled:
                return cached_format
        
        # Score each available format
        format_scores: Dict[str, float] = {}
        
        for format_name, metadata in self._strategies.items():
            if not metadata.is_enabled:
                continue
            
            try:
                strategy = self.get_strategy(format_name)
                if not strategy:
                    continue
                
                # Quick validation sample (use subset for performance)
                sample_citations = citations[:min(5, len(citations))]
                result = strategy.validate(sample_citations)
                
                # Calculate detection score
                base_score = result.confidence
                
                # Adjust score based on strategy priority
                priority_weight = metadata.priority / 100.0
                
                # Adjust score based on historical success rate
                success_weight = metadata.success_rate if metadata.usage_count > 0 else 0.5
                
                # Combined score
                final_score = (base_score * 0.6) + (priority_weight * 0.2) + (success_weight * 0.2)
                
                format_scores[format_name] = final_score
                
            except Exception as e:
                print(f"Auto-detection failed for {format_name}: {e}")
                format_scores[format_name] = 0.0
        
        # Find best match
        if format_scores:
            best_format = max(format_scores, key=format_scores.get)
            best_score = format_scores[best_format]
            
            # Only return if confidence is reasonable
            if best_score > 0.5:
                # Cache result
                self._auto_detection_cache[cache_key] = best_format
                return best_format
        
        return None
    
    def validate_multi_format(
        self,
        citations: List[str],
        formats: Optional[List[str]] = None,
        strict_mode: bool = False
    ) -> Dict[str, FormatValidationResult]:
        """
        Validate citations against multiple formats.
        
        Args:
            citations: Citations to validate
            formats: Specific formats to test (None = all available)
            strict_mode: Whether to use strict validation
            
        Returns:
            Dictionary mapping format names to validation results
        """
        if formats is None:
            formats = self.get_available_formats()
        
        results = {}
        
        for format_name in formats:
            strategy = self.get_strategy(format_name, strict_mode=strict_mode)
            if strategy:
                try:
                    start_time = datetime.now()
                    result = strategy.validate(citations)
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Update processing time in result
                    result.processing_time_ms = processing_time
                    
                    results[format_name] = result
                    
                    # Update statistics
                    self._update_statistics(format_name, result, processing_time)
                    
                except Exception as e:
                    print(f"Validation failed for format {format_name}: {e}")
                    # Create error result
                    results[format_name] = FormatValidationResult(
                        format_name=format_name,
                        is_valid=False,
                        confidence=0.0,
                        errors=[f"Validation failed: {str(e)}"],
                        total_citations=len(citations),
                        processed_citations=0
                    )
        
        return results
    
    def get_best_format_match(
        self,
        citations: List[str],
        confidence_threshold: float = 0.7
    ) -> Tuple[Optional[str], Optional[FormatValidationResult]]:
        """
        Find the best format match for citations.
        
        Args:
            citations: Citations to validate
            confidence_threshold: Minimum confidence required
            
        Returns:
            Tuple of (format_name, validation_result) or (None, None)
        """
        results = self.validate_multi_format(citations)
        
        if not results:
            return None, None
        
        # Find format with highest confidence
        best_format = None
        best_result = None
        best_confidence = 0.0
        
        for format_name, result in results.items():
            if result.confidence > best_confidence and result.confidence >= confidence_threshold:
                best_confidence = result.confidence
                best_format = format_name
                best_result = result
        
        return best_format, best_result
    
    def _update_statistics(
        self,
        format_name: str,
        result: FormatValidationResult,
        processing_time: float
    ) -> None:
        """Update validation statistics."""
        self._statistics.total_validations += 1
        
        if result.is_valid:
            self._statistics.successful_validations += 1
        else:
            self._statistics.failed_validations += 1
        
        # Update format distribution
        self._statistics.format_distribution[format_name] += 1
        
        # Update average processing time
        total_time = (self._statistics.average_processing_time * 
                     (self._statistics.total_validations - 1) + processing_time)
        self._statistics.average_processing_time = total_time / self._statistics.total_validations
        
        # Update average confidence
        total_confidence = (self._statistics.average_confidence * 
                          (self._statistics.total_validations - 1) + result.confidence)
        self._statistics.average_confidence = total_confidence / self._statistics.total_validations
        
        # Update strategy success rate
        metadata = self._strategies.get(format_name)
        if metadata:
            if result.is_valid:
                metadata.success_rate = ((metadata.success_rate * metadata.usage_count + 1.0) / 
                                       (metadata.usage_count + 1))
            else:
                metadata.success_rate = ((metadata.success_rate * metadata.usage_count) / 
                                       (metadata.usage_count + 1))
        
        # Track error patterns
        for error in result.errors:
            # Extract error type (first word)
            error_type = error.split(':')[0] if ':' in error else error.split()[0]
            self._statistics.error_patterns[error_type] = (
                self._statistics.error_patterns.get(error_type, 0) + 1
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": self._statistics.total_validations,
            "success_rate": (
                self._statistics.successful_validations / self._statistics.total_validations
                if self._statistics.total_validations > 0 else 0.0
            ),
            "average_processing_time_ms": self._statistics.average_processing_time,
            "average_confidence": self._statistics.average_confidence,
            "format_distribution": dict(self._statistics.format_distribution),
            "common_errors": dict(sorted(
                self._statistics.error_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 error patterns
            "registered_strategies": {
                name: {
                    "version": metadata.version,
                    "priority": metadata.priority,
                    "enabled": metadata.is_enabled,
                    "usage_count": metadata.usage_count,
                    "success_rate": metadata.success_rate,
                    "last_used": metadata.last_used.isoformat() if metadata.last_used else None
                }
                for name, metadata in self._strategies.items()
            }
        }
    
    def initialize_default_strategies(self) -> None:
        """Initialize with default citation format strategies."""
        if self._initialized:
            return
        
        try:
            # Import and register APA strategy
            from .apa_strategy import APAFormatStrategy
            self.register_strategy(APAFormatStrategy, priority=80)
            
            # Register other strategies as they become available
            # from .mla_strategy import MLAFormatStrategy
            # self.register_strategy(MLAFormatStrategy, priority=70)
            
            self._initialized = True
            
        except ImportError as e:
            print(f"Failed to initialize some default strategies: {e}")
    
    def clear_cache(self) -> None:
        """Clear auto-detection cache."""
        self._auto_detection_cache.clear()
    
    def enable_strategy(self, format_name: str) -> bool:
        """Enable a strategy."""
        format_name = format_name.lower()
        if format_name in self._strategies:
            self._strategies[format_name].is_enabled = True
            return True
        return False
    
    def disable_strategy(self, format_name: str) -> bool:
        """Disable a strategy."""
        format_name = format_name.lower()
        if format_name in self._strategies:
            self._strategies[format_name].is_enabled = False
            # Clear from cache
            self._auto_detection_cache = {
                k: v for k, v in self._auto_detection_cache.items() 
                if v != format_name
            }
            return True
        return False
    
    def reset_statistics(self) -> None:
        """Reset all validation statistics."""
        self._statistics = ValidationStatistics()
        for metadata in self._strategies.values():
            metadata.usage_count = 0
            metadata.success_rate = 0.0
            metadata.last_used = None


# Global registry instance
_global_registry = None


def get_global_registry() -> CitationFormatRegistry:
    """Get the global citation format registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CitationFormatRegistry()
        _global_registry.initialize_default_strategies()
    return _global_registry