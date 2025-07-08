"""
Input validation utilities for Academic Validation Framework.
"""
from typing import Any, Optional, List, Dict, Type, Union
from dataclasses import fields, is_dataclass
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Comprehensive input validation utility."""
    
    @staticmethod
    def validate_required_fields(data: Any, required_fields: List[str]) -> None:
        """Validate that required fields are present and non-empty."""
        if data is None:
            raise ValidationError("Input data cannot be None")
        
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if not hasattr(data, field):
                missing_fields.append(field)
            else:
                value = getattr(data, field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    empty_fields.append(field)
        
        errors = []
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            errors.append(f"Empty required fields: {', '.join(empty_fields)}")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_dataclass(instance: Any, expected_type: Type) -> None:
        """Validate that an instance is of the expected dataclass type."""
        if not isinstance(instance, expected_type):
            raise ValidationError(
                f"Expected instance of {expected_type.__name__}, "
                f"got {type(instance).__name__}"
            )
        
        if is_dataclass(instance):
            # Validate each field
            for field in fields(instance):
                field_value = getattr(instance, field.name)
                
                # Check type annotations
                if hasattr(field.type, '__origin__'):
                    # Handle generic types like List, Dict, Optional
                    origin = field.type.__origin__
                    
                    if origin is list and field_value is not None:
                        if not isinstance(field_value, list):
                            raise ValidationError(
                                f"Field '{field.name}' must be a list, "
                                f"got {type(field_value).__name__}"
                            )
                    
                    elif origin is dict and field_value is not None:
                        if not isinstance(field_value, dict):
                            raise ValidationError(
                                f"Field '{field.name}' must be a dict, "
                                f"got {type(field_value).__name__}"
                            )
                    
                    elif origin is Union:
                        # Handle Optional types
                        args = field.type.__args__
                        if type(None) in args and field_value is None:
                            continue  # None is allowed for Optional
                        
                        # Check if value matches any of the union types
                        valid_types = [t for t in args if t is not type(None)]
                        if field_value is not None and not any(isinstance(field_value, t) for t in valid_types):
                            type_names = ', '.join(t.__name__ for t in valid_types)
                            raise ValidationError(
                                f"Field '{field.name}' must be one of [{type_names}], "
                                f"got {type(field_value).__name__}"
                            )
                
                elif field_value is not None and not isinstance(field_value, field.type):
                    # Simple type check
                    raise ValidationError(
                        f"Field '{field.name}' must be {field.type.__name__}, "
                        f"got {type(field_value).__name__}"
                    )
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, 
                             min_length: Optional[int] = None,
                             max_length: Optional[int] = None) -> None:
        """Validate string length constraints."""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        if min_length is not None and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long"
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters long"
            )
    
    @staticmethod
    def validate_list_size(value: List[Any], field_name: str,
                          min_size: Optional[int] = None,
                          max_size: Optional[int] = None) -> None:
        """Validate list size constraints."""
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list")
        
        if min_size is not None and len(value) < min_size:
            raise ValidationError(
                f"{field_name} must contain at least {min_size} items"
            )
        
        if max_size is not None and len(value) > max_size:
            raise ValidationError(
                f"{field_name} must contain at most {max_size} items"
            )
    
    @staticmethod
    def validate_number_range(value: Union[int, float], field_name: str,
                            min_value: Optional[Union[int, float]] = None,
                            max_value: Optional[Union[int, float]] = None) -> None:
        """Validate numeric range constraints."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}"
            )
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input by removing potentially harmful content."""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        sanitized = value.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        # Limit length to prevent DoS
        MAX_STRING_LENGTH = 100000  # 100KB
        if len(sanitized) > MAX_STRING_LENGTH:
            logger.warning(f"String truncated from {len(sanitized)} to {MAX_STRING_LENGTH} characters")
            sanitized = sanitized[:MAX_STRING_LENGTH]
        
        return sanitized
    
    @staticmethod
    def validate_research_data(data: Any) -> None:
        """Validate ResearchData object comprehensively."""
        from academic_validation_framework.models import ResearchData
        
        # Type validation
        InputValidator.validate_dataclass(data, ResearchData)
        
        # Required fields
        InputValidator.validate_required_fields(data, ['title', 'abstract'])
        
        # String length validation
        InputValidator.validate_string_length(data.title, 'title', min_length=3, max_length=500)
        InputValidator.validate_string_length(data.abstract, 'abstract', min_length=10, max_length=50000)
        
        # List validation
        if data.citations:
            InputValidator.validate_list_size(data.citations, 'citations', max_size=1000)
            
            # Validate each citation
            for i, citation in enumerate(data.citations):
                if not isinstance(citation, str):
                    raise ValidationError(f"Citation at index {i} must be a string")
                if len(citation) > 1000:
                    raise ValidationError(f"Citation at index {i} exceeds maximum length of 1000 characters")
        
        # Year validation
        if data.publication_year is not None:
            InputValidator.validate_number_range(
                data.publication_year, 'publication_year', 
                min_value=1900, max_value=2100
            )
        
        # Sanitize string fields
        data.title = InputValidator.sanitize_string(data.title)
        data.abstract = InputValidator.sanitize_string(data.abstract)
        if data.methodology:
            data.methodology = InputValidator.sanitize_string(data.methodology)
        if data.journal:
            data.journal = InputValidator.sanitize_string(data.journal)


def validate_input(func):
    """Decorator for automatic input validation."""
    def wrapper(*args, **kwargs):
        # Log validation attempt
        logger.debug(f"Validating input for {func.__name__}")
        
        try:
            # If first argument is self/cls, second argument is typically the data
            if len(args) >= 2:
                data = args[1]
                
                # Check if it's ResearchData
                from academic_validation_framework.models import ResearchData
                if isinstance(data, ResearchData):
                    InputValidator.validate_research_data(data)
            
            return func(*args, **kwargs)
            
        except ValidationError as e:
            logger.error(f"Validation error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation in {func.__name__}: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    return wrapper