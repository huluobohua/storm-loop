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
import logging
import threading
from contextlib import contextmanager

from .base import CitationFormatStrategy, FormatValidationResult
from ..utils.lru_cache import LRUCache
from ..config.validation_constants import ValidationConstants

logger = logging.getLogger(__name__)


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
    
    def __init__(self, cache_size: int = 100, cache_ttl: int = 3600):
        """
        Initialize the registry with LRU cache and thread safety.
        
        Args:
            cache_size: Maximum number of items in cache
            cache_ttl: Time-to-live for cache entries in seconds
        """
        self._strategies: Dict[str, StrategyMetadata] = {}
        self._statistics = ValidationStatistics()
        self._auto_detection_cache = LRUCache(max_size=cache_size, ttl_seconds=cache_ttl)
        self._initialized = False
        
        # Thread safety
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._stats_lock = threading.Lock()  # Separate lock for statistics
    
    @contextmanager
    def _strategy_lock(self):
        """Context manager for strategy operations."""
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
    
    @contextmanager
    def _statistics_lock(self):
        """Context manager for statistics operations."""
        self._stats_lock.acquire()
        try:
            yield
        finally:
            self._stats_lock.release()
    
    def register_strategy(
        self,
        strategy_class: Type[CitationFormatStrategy],
        priority: int = 50,
        is_enabled: bool = True
    ) -> bool:
        """
        Register a citation format strategy with thread safety.
        
        Args:
            strategy_class: Strategy class to register
            priority: Priority for auto-detection (higher = preferred)
            is_enabled: Whether strategy is enabled
            
        Returns:
            True if registration successful, False otherwise
        """
        with self._strategy_lock():
            try:
                # Security validation - prevent code injection
                if not inspect.isclass(strategy_class):
                    raise ValueError("strategy_class must be a class")
                
                # Validate that it's a proper class and not malicious code
                if not hasattr(strategy_class, '__name__'):
                    raise ValueError("Invalid strategy class - missing __name__")
                
                # Check for suspicious class names that might indicate injection
                class_name = strategy_class.__name__
                if not class_name.isidentifier() or class_name.startswith('_'):
                    raise ValueError(f"Invalid class name: {class_name}")
                
                # Validate inheritance properly
                if not issubclass(strategy_class, CitationFormatStrategy):
                    raise ValueError(f"Strategy class must inherit from CitationFormatStrategy")
                
                # Validate module origin - only allow trusted modules
                module_name = getattr(strategy_class, '__module__', None)
                if module_name and not self._is_trusted_module(module_name):
                    raise ValueError(f"Strategy from untrusted module: {module_name}")
                
                # Validate priority range to prevent resource abuse
                if not isinstance(priority, int) or priority < 0 or priority > 100:
                    raise ValueError("Priority must be an integer between 0 and 100")
                
                # Create instance safely - this could execute arbitrary code
                try:
                    instance = strategy_class()
                except Exception as e:
                    raise ValueError(f"Failed to instantiate strategy safely: {e}")
                
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
            logger.error(f"Failed to register strategy {strategy_class.__name__}: {e}")
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
        
        with self._strategy_lock():
            if format_name in self._strategies:
                del self._strategies[format_name]
                # Clear this format from cache
                # Since we can't iterate over LRU cache directly, we'll clear it
                # This is acceptable as cache will rebuild naturally
                self._auto_detection_cache.clear()
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
        
        with self._strategy_lock():
            metadata = self._strategies.get(format_name)
            
            if metadata and metadata.is_enabled:
                try:
                    instance = metadata.strategy_class(strict_mode=strict_mode)
                    
                    # Update usage statistics safely within lock
                    metadata.usage_count += 1
                    metadata.last_used = datetime.now()
                    
                    return instance
                except Exception as e:
                    logger.error(f"Failed to create strategy instance for {format_name}: {e}")
        
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
        
        # Check cache first with thread safety
        cache_key = hash(tuple(citations[:3]))  # Use first 3 citations for cache key
        cached_format = self._auto_detection_cache.get(cache_key)
        if cached_format is not None:
            with self._strategy_lock():
                if cached_format in self._strategies and self._strategies[cached_format].is_enabled:
                    return cached_format
        
        # Score each available format
        format_scores: Dict[str, float] = {}
        
        # Get a snapshot of strategies to avoid holding lock during validation
        with self._strategy_lock():
            strategies_snapshot = [(name, metadata) for name, metadata in self._strategies.items()]
        
        for format_name, metadata in strategies_snapshot:
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
                logger.warning(f"Auto-detection failed for {format_name}: {e}")
                format_scores[format_name] = 0.0
        
        # Find best match
        if format_scores:
            best_format = max(format_scores, key=format_scores.get)
            best_score = format_scores[best_format]
            
            # Only return if confidence is reasonable
            if best_score > 0.5:
                # Cache result
                self._auto_detection_cache.put(cache_key, best_format)
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
                    logger.warning(f"Validation failed for format {format_name}: {e}")
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
        """Update validation statistics with thread safety."""
        with self._statistics_lock():
            self._statistics.total_validations += 1
            
            if result.is_valid:
                self._statistics.successful_validations += 1
            else:
                self._statistics.failed_validations += 1
            
            # Update format distribution with bounds checking
            if format_name not in self._statistics.format_distribution:
                self._statistics.format_distribution[format_name] = 0
            self._statistics.format_distribution[format_name] += 1
            
            # Cleanup statistics if they grow too large
            perf_constants = ValidationConstants.PERFORMANCE
            if (len(self._statistics.format_distribution) > perf_constants.STATISTICS_CLEANUP_THRESHOLD or
                len(self._statistics.error_patterns) > perf_constants.STATISTICS_CLEANUP_THRESHOLD):
                self._cleanup_statistics()
            
            # Update average processing time
            total_time = (self._statistics.average_processing_time * 
                         (self._statistics.total_validations - 1) + processing_time)
            self._statistics.average_processing_time = total_time / self._statistics.total_validations
            
            # Update average confidence
            total_confidence = (self._statistics.average_confidence * 
                              (self._statistics.total_validations - 1) + result.confidence)
            self._statistics.average_confidence = total_confidence / self._statistics.total_validations
        
        # Update strategy success rate (needs strategy lock)
        with self._strategy_lock():
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
            
            # Import and register MLA strategy
            from .mla_strategy import MLAFormatStrategy
            self.register_strategy(MLAFormatStrategy, priority=75)
            
            # Import and register IEEE strategy
            from .ieee_strategy import IEEEFormatStrategy
            self.register_strategy(IEEEFormatStrategy, priority=70)
            
            # Import and register Harvard strategy
            from .harvard_strategy import HarvardFormatStrategy
            self.register_strategy(HarvardFormatStrategy, priority=65)
            
            # Import and register Chicago strategy
            from .chicago_strategy import ChicagoFormatStrategy
            self.register_strategy(ChicagoFormatStrategy, priority=60)
            
            self._initialized = True
            
        except ImportError as e:
            logger.error(f"Failed to initialize some default strategies: {e}")
    
    def clear_cache(self) -> None:
        """Clear auto-detection cache."""
        self._auto_detection_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._auto_detection_cache.stats()
    
    def enable_strategy(self, format_name: str) -> bool:
        """Enable a strategy."""
        format_name = format_name.lower()
        
        with self._strategy_lock():
            if format_name in self._strategies:
                self._strategies[format_name].is_enabled = True
                return True
            return False
    
    def disable_strategy(self, format_name: str) -> bool:
        """Disable a strategy."""
        format_name = format_name.lower()
        
        with self._strategy_lock():
            if format_name in self._strategies:
                self._strategies[format_name].is_enabled = False
                # Clear this format from cache
                # Since we can't iterate over LRU cache directly, we'll clear it
                # This is acceptable as cache will rebuild naturally
                self._auto_detection_cache.clear()
                return True
            return False
    
    def reset_statistics(self) -> None:
        """Reset all validation statistics."""
        with self._statistics_lock():
            self._statistics = ValidationStatistics()
        
        with self._strategy_lock():
            for metadata in self._strategies.values():
                metadata.usage_count = 0
                metadata.success_rate = 0.0
                metadata.last_used = None
    
    def _cleanup_statistics(self) -> None:
        """Clean up statistics to prevent unbounded growth."""
        perf_constants = ValidationConstants.PERFORMANCE
        
        # Keep only the most frequent format distributions
        if len(self._statistics.format_distribution) > perf_constants.MAX_STATISTICS_ENTRIES:
            # Sort by count, keep top entries
            sorted_formats = sorted(
                self._statistics.format_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self._statistics.format_distribution = dict(
                sorted_formats[:perf_constants.MAX_STATISTICS_ENTRIES]
            )
            logger.info(f"Cleaned format distribution statistics, kept {perf_constants.MAX_STATISTICS_ENTRIES} entries")
        
        # Keep only the most frequent error patterns
        if len(self._statistics.error_patterns) > perf_constants.MAX_ERROR_PATTERNS:
            # Sort by count, keep top entries
            sorted_errors = sorted(
                self._statistics.error_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self._statistics.error_patterns = dict(
                sorted_errors[:perf_constants.MAX_ERROR_PATTERNS]
            )
            logger.info(f"Cleaned error pattern statistics, kept {perf_constants.MAX_ERROR_PATTERNS} entries")
    
    def _is_trusted_module(self, module_name: str) -> bool:
        """Check if a module is trusted for strategy registration."""
        # Use exact matching for dangerous modules to prevent bypass
        dangerous_modules = {
            'os', 'sys', 'subprocess', 'eval', 'exec', 'importlib',
            'socket', 'urllib', 'requests', 'http', 'urllib2', 'urllib3',
            'httplib', 'httplib2', 'ftplib', 'telnetlib', 'smtplib',
            'poplib', 'imaplib', 'nntplib', 'xmlrpclib', 'SimpleXMLRPCServer',
            'DocXMLRPCServer', 'CGIHTTPServer', 'BaseHTTPServer', 'SimpleHTTPServer',
            'CGIXMLRPCRequestHandler', 'pickle', 'cPickle', 'marshal', 'shelve'
        }
        
        # First check if it's a dangerous module
        if module_name in dangerous_modules:
            return False
        
        # Check if any component of the module path is dangerous
        module_parts = module_name.split('.')
        for part in module_parts:
            if part in dangerous_modules:
                return False
        
        # Trusted modules - use exact prefixes and be more restrictive
        trusted_prefixes = [
            'academic_validation_framework.',  # Note the dot to ensure exact prefix
            'academic_validation_framework',   # Allow the package itself
            '__main__',                       # Allow for testing
            'test_',                         # Allow test modules
            'tests.',                        # Allow test packages
        ]
        
        # Check if it starts with a trusted prefix
        for prefix in trusted_prefixes:
            if module_name == prefix or module_name.startswith(prefix):
                return True
        
        # Default to untrusted
        return False


# Global registry instance
_global_registry = None


def get_global_registry() -> CitationFormatRegistry:
    """Get the global citation format registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CitationFormatRegistry()
        _global_registry.initialize_default_strategies()
    return _global_registry