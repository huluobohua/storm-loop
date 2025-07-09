"""
Configuration validation utilities for ensuring validator configurations are valid.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from academic_validation_framework.config import ValidationConfig


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ConfigValidator:
    """Validates ValidationConfig instances for correctness and completeness."""
    
    @staticmethod
    def validate_config(config: ValidationConfig) -> ConfigValidationResult:
        """
        Validate a ValidationConfig instance.
        
        Args:
            config: The ValidationConfig to validate
            
        Returns:
            ConfigValidationResult with validation details
        """
        errors = []
        warnings = []
        
        # Validate thresholds
        ConfigValidator._validate_thresholds(config, errors, warnings)
        
        # Validate performance settings
        ConfigValidator._validate_performance_settings(config, errors, warnings)
        
        # Validate API settings
        ConfigValidator._validate_api_settings(config, errors, warnings)
        
        # Validate citation settings
        ConfigValidator._validate_citation_settings(config, errors, warnings)
        
        # Validate PRISMA settings
        ConfigValidator._validate_prisma_settings(config, errors, warnings)
        
        # Validate bias detection settings
        ConfigValidator._validate_bias_settings(config, errors, warnings)
        
        # Validate logging settings
        ConfigValidator._validate_logging_settings(config, errors, warnings)
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _validate_thresholds(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate threshold values."""
        thresholds = {
            "citation_accuracy_threshold": config.citation_accuracy_threshold,
            "prisma_compliance_threshold": config.prisma_compliance_threshold,
            "bias_detection_threshold": config.bias_detection_threshold,
            "confidence_threshold": config.confidence_threshold,
        }
        
        for name, value in thresholds.items():
            if not isinstance(value, (int, float)):
                errors.append(f"{name} must be a number")
            elif not (0.0 <= value <= 1.0):
                errors.append(f"{name} must be between 0.0 and 1.0")
            elif value < 0.5:
                warnings.append(f"{name} is set to {value}, which is quite low")
    
    @staticmethod
    def _validate_performance_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate performance-related settings."""
        if config.max_concurrent_validations <= 0:
            errors.append("max_concurrent_validations must be positive")
        elif config.max_concurrent_validations > 100:
            warnings.append("max_concurrent_validations is very high, may cause resource issues")
        
        if config.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")
        elif config.timeout_seconds > 300:
            warnings.append("timeout_seconds is very high, may cause long waits")
        
        if config.memory_limit_mb <= 0:
            errors.append("memory_limit_mb must be positive")
        elif config.memory_limit_mb < 512:
            warnings.append("memory_limit_mb is quite low, may cause memory issues")
        
        if config.cache_ttl_seconds <= 0:
            errors.append("cache_ttl_seconds must be positive")
    
    @staticmethod
    def _validate_api_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate API-related settings."""
        if config.retry_attempts < 0:
            errors.append("retry_attempts must be non-negative")
        elif config.retry_attempts > 10:
            warnings.append("retry_attempts is very high, may cause long delays")
        
        if config.backoff_factor <= 0:
            errors.append("backoff_factor must be positive")
        elif config.backoff_factor > 5:
            warnings.append("backoff_factor is very high, may cause exponential delays")
        
        if config.api_rate_limits:
            for service, limit in config.api_rate_limits.items():
                if not isinstance(limit, int) or limit <= 0:
                    errors.append(f"Rate limit for {service} must be a positive integer")
    
    @staticmethod
    def _validate_citation_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate citation-related settings."""
        valid_formats = {"APA", "MLA", "Chicago", "Harvard", "IEEE", "Vancouver"}
        
        if config.citation_formats:
            for fmt in config.citation_formats:
                if fmt not in valid_formats:
                    warnings.append(f"Citation format '{fmt}' is not a standard format")
        
        if not config.citation_formats:
            warnings.append("No citation formats specified")
    
    @staticmethod
    def _validate_prisma_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate PRISMA-related settings."""
        valid_versions = {"2020", "2009"}
        
        if config.prisma_version not in valid_versions:
            errors.append(f"PRISMA version must be one of {valid_versions}")
        
        if config.minimum_search_databases <= 0:
            errors.append("minimum_search_databases must be positive")
        elif config.minimum_search_databases < 2:
            warnings.append("minimum_search_databases is quite low for systematic reviews")
        
        if config.required_prisma_sections:
            standard_sections = {
                "title", "abstract", "introduction", "methods", 
                "results", "discussion", "conclusion", "references"
            }
            for section in config.required_prisma_sections:
                if section not in standard_sections:
                    warnings.append(f"Non-standard PRISMA section: {section}")
    
    @staticmethod
    def _validate_bias_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate bias detection settings."""
        valid_sensitivity = {"low", "medium", "high"}
        
        if config.bias_sensitivity_level not in valid_sensitivity:
            errors.append(f"bias_sensitivity_level must be one of {valid_sensitivity}")
        
        if config.bias_types_to_check:
            standard_bias_types = {
                "confirmation_bias", "selection_bias", "publication_bias",
                "funding_bias", "author_bias", "reporting_bias"
            }
            for bias_type in config.bias_types_to_check:
                if bias_type not in standard_bias_types:
                    warnings.append(f"Non-standard bias type: {bias_type}")
    
    @staticmethod
    def _validate_logging_settings(config: ValidationConfig, errors: List[str], warnings: List[str]):
        """Validate logging settings."""
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        
        if config.log_level not in valid_log_levels:
            errors.append(f"log_level must be one of {valid_log_levels}")
        
        if config.max_error_count <= 0:
            errors.append("max_error_count must be positive")
    
    @staticmethod
    def validate_and_fix_config(config: ValidationConfig) -> ValidationConfig:
        """
        Validate config and attempt to fix common issues.
        
        Args:
            config: The ValidationConfig to validate and fix
            
        Returns:
            A corrected ValidationConfig instance
        """
        # Create a copy to avoid modifying the original
        import copy
        fixed_config = copy.deepcopy(config)
        
        # Fix threshold values
        for attr in ["citation_accuracy_threshold", "prisma_compliance_threshold", 
                    "bias_detection_threshold", "confidence_threshold"]:
            value = getattr(fixed_config, attr)
            if value < 0.0:
                setattr(fixed_config, attr, 0.0)
            elif value > 1.0:
                setattr(fixed_config, attr, 1.0)
        
        # Fix performance settings
        if fixed_config.max_concurrent_validations <= 0:
            fixed_config.max_concurrent_validations = 50
        
        if fixed_config.timeout_seconds <= 0:
            fixed_config.timeout_seconds = 30
        
        if fixed_config.memory_limit_mb <= 0:
            fixed_config.memory_limit_mb = 2048
        
        # Fix API settings
        if fixed_config.retry_attempts < 0:
            fixed_config.retry_attempts = 3
        
        if fixed_config.backoff_factor <= 0:
            fixed_config.backoff_factor = 2.0
        
        # Fix PRISMA settings
        if fixed_config.minimum_search_databases <= 0:
            fixed_config.minimum_search_databases = 3
        
        if fixed_config.prisma_version not in ["2020", "2009"]:
            fixed_config.prisma_version = "2020"
        
        # Fix bias settings
        if fixed_config.bias_sensitivity_level not in ["low", "medium", "high"]:
            fixed_config.bias_sensitivity_level = "medium"
        
        # Fix logging settings
        if fixed_config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            fixed_config.log_level = "INFO"
        
        if fixed_config.max_error_count <= 0:
            fixed_config.max_error_count = 10
        
        return fixed_config