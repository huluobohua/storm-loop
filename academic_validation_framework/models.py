"""
Models module for Academic Validation Framework
Contains BiasCheck model to break circular dependencies
This was moved from bias_detector.py to resolve circular import issue
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ValidationResult:
    """Value object for validation results following SOLID principles"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self._is_valid = is_valid
        self._errors = errors or []
    
    @property
    def is_valid(self) -> bool:
        return self._is_valid
    
    @property
    def errors(self) -> List[str]:
        return self._errors.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.is_valid, "errors": self.errors}


class Validator(ABC):
    """Abstract base class for all validators (Open/Closed Principle)"""
    
    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """Validate data and return result"""
        pass


class BiasCheck(Validator):
    """
    Model for bias validation checks
    Moved here from bias_detector.py to break circular dependency
    Follows Single Responsibility Principle
    """
    
    def __init__(self):
        """Initialize bias check with default state"""
        pass
    
    def validate(self, data: Any) -> ValidationResult:
        """Validate data for bias with comprehensive error handling"""
        if data is None:
            return self._handle_none_data()
        
        if not self._is_supported_type(data):
            return self._handle_unsupported_type(data)
        
        return ValidationResult(is_valid=True)
    
    def _handle_none_data(self) -> ValidationResult:
        """Handle None data input"""
        return ValidationResult(is_valid=False, errors=["Data cannot be None"])
    
    def _is_supported_type(self, data: Any) -> bool:
        """Check if data type is supported"""
        return isinstance(data, (dict, list, str, int, float))
    
    def _handle_unsupported_type(self, data: Any) -> ValidationResult:
        """Handle unsupported data types"""
        return ValidationResult(
            is_valid=False,
            errors=[f"Unsupported data type: {type(data).__name__}"]
        )
    
    @property
    def is_valid(self) -> bool:
        """Compatibility property for existing interface"""
        return True  # For backwards compatibility
    
    @property 
    def errors(self) -> List[str]:
        """Compatibility property for existing interface"""
        return []  # For backwards compatibility