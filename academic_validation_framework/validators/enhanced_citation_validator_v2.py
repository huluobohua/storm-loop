"""
Enhanced Citation Validator V2 - Strategy Pattern Implementation

Comprehensive citation validation system using the Strategy pattern with
input validation, confidence calibration, and multi-format support.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.config import ValidationConfig

# Import Strategy pattern components
from academic_validation_framework.strategies import (
    CitationFormatRegistry,
    InputValidator,
    ValidationStrictness,
    ConfidenceCalibrator,
    CalibrationMethod
)
from academic_validation_framework.strategies.registry import get_global_registry


@dataclass
class EnhancedValidationResult:
    """Enhanced validation result with detailed breakdown."""
    overall_result: ValidationResult
    format_results: Dict[str, Any] = field(default_factory=dict)
    input_validation: Dict[str, Any] = field(default_factory=dict)
    confidence_calibration: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class EnhancedCitationValidatorV2:
    """
    Enhanced citation validator using Strategy pattern architecture.
    
    Provides comprehensive citation validation with:
    - Multi-format validation using Strategy pattern
    - Input sanitization and security validation
    - Confidence calibration and uncertainty quantification
    - Performance monitoring and caching
    """
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        
        # Initialize components
        self.registry = get_global_registry()
        self.input_validator = InputValidator(ValidationStrictness.STANDARD)
        self.confidence_calibrator = ConfidenceCalibrator(CalibrationMethod.TEMPERATURE_SCALING)
        
        # Performance tracking
        self.validation_count = 0
        self.total_processing_time = 0.0
        self.format_success_rates: Dict[str, float] = {}
        
        # Configuration
        self.strict_mode = getattr(config, 'strict_validation', False)
        self.enable_multi_format = True
        self.max_formats_to_test = 3
        
    async def validate(self, data: ResearchData) -> ValidationResult:
        """
        Validate citations with comprehensive strategy-based validation.
        
        Args:
            data: Research data containing citations to validate
            
        Returns:
            ValidationResult with enhanced validation details
        """
        start_time = time.time()
        
        try:
            # Phase 1: Input validation and sanitization
            input_result = self.input_validator.validate_and_sanitize(data.citations)
            
            if not input_result.is_valid:
                return self._create_input_validation_failure(input_result)
            
            sanitized_citations = input_result.sanitized_input
            
            # Phase 2: Format detection and validation
            if self.enable_multi_format:
                format_results = await self._multi_format_validation(sanitized_citations)
            else:
                format_results = await self._single_format_validation(sanitized_citations)
            
            # Phase 3: Select best result and apply confidence calibration
            best_result = self._select_best_result(format_results)
            calibrated_result = self._apply_confidence_calibration(best_result, sanitized_citations)
            
            # Phase 4: Create enhanced result
            enhanced_result = self._create_enhanced_result(
                calibrated_result,
                format_results,
                input_result,
                start_time
            )
            
            # Update performance metrics
            self._update_performance_metrics(enhanced_result.overall_result, time.time() - start_time)
            
            return enhanced_result.overall_result
            
        except Exception as e:
            # Fallback error handling
            return ValidationResult(
                validator_name="enhanced_citation_v2",
                test_name="citation_validation_test",
                status=ValidationStatus.FAILED,
                score=0.0,
                details={
                    "error": f"Validation failed: {str(e)}",
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            )
    
    async def _multi_format_validation(self, citations: List[str]) -> Dict[str, Any]:
        """Validate against multiple citation formats."""
        # Get available formats
        available_formats = self.registry.get_available_formats()
        
        # Auto-detect best formats to test
        detected_format = self.registry.auto_detect_format(citations)
        
        # Select formats to test
        formats_to_test = []
        if detected_format:
            formats_to_test.append(detected_format)
        
        # Add other high-priority formats
        remaining_formats = [f for f in available_formats if f != detected_format]
        formats_to_test.extend(remaining_formats[:self.max_formats_to_test - len(formats_to_test)])
        
        # Validate against selected formats
        results = self.registry.validate_multi_format(
            citations,
            formats=formats_to_test,
            strict_mode=self.strict_mode
        )
        
        return {
            "detected_format": detected_format,
            "formats_tested": formats_to_test,
            "format_results": results,
            "validation_method": "multi_format"
        }
    
    async def _single_format_validation(self, citations: List[str]) -> Dict[str, Any]:
        """Validate against single best-matching format."""
        # Auto-detect format
        detected_format = self.registry.auto_detect_format(citations)
        
        if not detected_format:
            # Fallback to APA if no format detected
            detected_format = "apa"
        
        # Get strategy and validate
        strategy = self.registry.get_strategy(detected_format, strict_mode=self.strict_mode)
        
        if strategy:
            result = strategy.validate(citations)
            format_results = {detected_format: result}
        else:
            # Create error result
            from academic_validation_framework.strategies.base import FormatValidationResult
            result = FormatValidationResult(
                format_name=detected_format,
                is_valid=False,
                confidence=0.0,
                errors=[f"Strategy not available for format: {detected_format}"],
                total_citations=len(citations)
            )
            format_results = {detected_format: result}
        
        return {
            "detected_format": detected_format,
            "formats_tested": [detected_format],
            "format_results": format_results,
            "validation_method": "single_format"
        }
    
    def _select_best_result(self, format_results: Dict[str, Any]) -> Any:
        """Select the best validation result from multiple formats."""
        results = format_results["format_results"]
        
        if not results:
            return None
        
        # Find format with highest confidence
        best_format = None
        best_result = None
        best_confidence = 0.0
        
        for format_name, result in results.items():
            if result.confidence > best_confidence:
                best_confidence = result.confidence
                best_format = format_name
                best_result = result
        
        return {
            "format_name": best_format,
            "result": best_result,
            "confidence": best_confidence
        }
    
    def _apply_confidence_calibration(self, best_result: Any, citations: List[str]) -> ValidationResult:
        """Apply confidence calibration to the best result."""
        if not best_result or not best_result["result"]:
            return ValidationResult(
                validator_name="enhanced_citation_v2",
                test_name="citation_validation_test",
                status=ValidationStatus.FAILED,
                score=0.0,
                details={"error": "No valid results to calibrate"}
            )
        
        format_result = best_result["result"]
        format_name = best_result["format_name"]
        
        # Extract evidence for calibration
        validation_evidence = []
        if hasattr(format_result, 'evidence') and format_result.evidence:
            validation_evidence = [
                {
                    "confidence_score": evidence.confidence_score,
                    "rule_applied": evidence.rule_applied,
                    "context": evidence.context
                }
                for evidence in format_result.evidence
            ]
        
        # Apply calibration
        calibration_result = self.confidence_calibrator.calibrate_confidence(
            raw_confidence=format_result.confidence,
            validation_evidence=validation_evidence,
            format_name=format_name,
            sample_size=len(citations)
        )
        
        # Create final validation result
        passed = calibration_result.calibrated_confidence >= self.config.citation_accuracy_threshold
        
        return ValidationResult(
            validator_name="enhanced_citation_v2",
            test_name="citation_validation_test",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            score=calibration_result.calibrated_confidence,
            details={
                "format_detected": format_name,
                "raw_confidence": calibration_result.raw_confidence,
                "calibrated_confidence": calibration_result.calibrated_confidence,
                "reliability_score": calibration_result.reliability_score,
                "uncertainty_estimate": calibration_result.uncertainty_estimate,
                "confidence_interval": {
                    "lower": calibration_result.confidence_interval.lower_bound if calibration_result.confidence_interval else None,
                    "upper": calibration_result.confidence_interval.upper_bound if calibration_result.confidence_interval else None,
                    "level": calibration_result.confidence_interval.confidence_level if calibration_result.confidence_interval else None
                },
                "calibration_method": calibration_result.calibration_method.value,
                "validation_evidence_count": len(validation_evidence),
                "format_validation_details": {
                    "total_citations": format_result.total_citations,
                    "valid_citations": format_result.valid_citations,
                    "errors": format_result.errors[:5],  # Limit errors for readability
                    "warnings": format_result.warnings[:3],
                    "suggestions": format_result.suggestions[:3]
                }
            }
        )
    
    def _create_input_validation_failure(self, input_result) -> ValidationResult:
        """Create validation result for input validation failure."""
        return ValidationResult(
            validator_name="enhanced_citation_v2",
            test_name="input_validation_test",
            status=ValidationStatus.FAILED,
            score=0.0,
            details={
                "input_validation_failed": True,
                "errors": input_result.errors,
                "security_issues": input_result.security_issues,
                "encoding_issues": input_result.encoding_issues,
                "content_issues": input_result.content_issues,
                "original_count": input_result.original_count,
                "processed_count": input_result.processed_count,
                "filtered_count": input_result.filtered_count
            }
        )
    
    def _create_enhanced_result(
        self,
        validation_result: ValidationResult,
        format_results: Dict[str, Any],
        input_result: Any,
        start_time: float
    ) -> EnhancedValidationResult:
        """Create comprehensive enhanced validation result."""
        processing_time = (time.time() - start_time) * 1000
        
        # Performance metrics
        performance_metrics = {
            "processing_time_ms": processing_time,
            "citations_processed": input_result.processed_count,
            "formats_tested": len(format_results.get("formats_tested", [])),
            "validation_method": format_results.get("validation_method", "unknown")
        }
        
        # Input validation summary
        input_validation = {
            "passed": input_result.is_valid,
            "original_count": input_result.original_count,
            "processed_count": input_result.processed_count,
            "filtered_count": input_result.filtered_count,
            "security_issues": len(input_result.security_issues),
            "content_issues": len(input_result.content_issues)
        }
        
        # Confidence calibration summary
        confidence_calibration = {}
        if validation_result.details:
            confidence_calibration = {
                "raw_confidence": validation_result.details.get("raw_confidence", 0.0),
                "calibrated_confidence": validation_result.details.get("calibrated_confidence", 0.0),
                "reliability_score": validation_result.details.get("reliability_score", 0.0),
                "calibration_method": validation_result.details.get("calibration_method", "unknown")
            }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_result, input_result, format_results)
        
        return EnhancedValidationResult(
            overall_result=validation_result,
            format_results=format_results,
            input_validation=input_validation,
            confidence_calibration=confidence_calibration,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        validation_result: ValidationResult,
        input_result: Any,
        format_results: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Input validation recommendations
        if input_result.security_issues:
            recommendations.append("Review citations for potential security vulnerabilities")
        
        if input_result.filtered_count > 0:
            recommendations.append(f"{input_result.filtered_count} citations were filtered due to validation issues")
        
        # Format validation recommendations
        if validation_result.score < 0.5:
            recommendations.append("Citation format appears non-standard - consider reviewing formatting guidelines")
        
        if validation_result.details and validation_result.details.get("uncertainty_estimate", 0) > 0.3:
            recommendations.append("High uncertainty in validation - consider manual review")
        
        # Multi-format recommendations
        if format_results.get("validation_method") == "multi_format":
            detected_format = format_results.get("detected_format")
            if detected_format:
                recommendations.append(f"Primary format detected as {detected_format.upper()}")
            
            results = format_results.get("format_results", {})
            if len(results) > 1:
                confidences = [(name, result.confidence) for name, result in results.items()]
                confidences.sort(key=lambda x: x[1], reverse=True)
                
                if len(confidences) > 1 and confidences[0][1] - confidences[1][1] < 0.2:
                    recommendations.append("Multiple citation formats detected - ensure consistency")
        
        # Performance recommendations
        if self.validation_count > 0:
            avg_time = self.total_processing_time / self.validation_count
            if avg_time > 500:  # > 500ms
                recommendations.append("Consider reducing citation batch size for better performance")
        
        return recommendations
    
    def _update_performance_metrics(self, result: ValidationResult, processing_time: float) -> None:
        """Update internal performance tracking."""
        self.validation_count += 1
        self.total_processing_time += processing_time
        
        # Update format success rates
        if result.details and "format_detected" in result.details:
            format_name = result.details["format_detected"]
            
            if format_name not in self.format_success_rates:
                self.format_success_rates[format_name] = 0.0
            
            # Update success rate (exponential moving average)
            success = 1.0 if result.status == ValidationStatus.PASSED else 0.0
            alpha = 0.1  # Learning rate
            self.format_success_rates[format_name] = (
                (1 - alpha) * self.format_success_rates[format_name] + alpha * success
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance and usage summary."""
        avg_processing_time = (
            self.total_processing_time / self.validation_count
            if self.validation_count > 0 else 0.0
        )
        
        return {
            "validation_count": self.validation_count,
            "average_processing_time_ms": avg_processing_time,
            "format_success_rates": dict(self.format_success_rates),
            "registry_statistics": self.registry.get_statistics(),
            "calibrator_summary": self.confidence_calibrator.get_calibration_summary()
        }
    
    def configure_input_validation(self, strictness: ValidationStrictness) -> None:
        """Configure input validation strictness."""
        self.input_validator = InputValidator(strictness)
    
    def configure_confidence_calibration(self, method: CalibrationMethod) -> None:
        """Configure confidence calibration method."""
        self.confidence_calibrator = ConfidenceCalibrator(method)
    
    def enable_strict_mode(self, enabled: bool = True) -> None:
        """Enable or disable strict validation mode."""
        self.strict_mode = enabled
    
    def set_multi_format_validation(self, enabled: bool = True, max_formats: int = 3) -> None:
        """Configure multi-format validation."""
        self.enable_multi_format = enabled
        self.max_formats_to_test = max_formats
    
    def add_calibration_feedback(
        self,
        raw_confidence: float,
        actual_accuracy: float,
        format_name: str = ""
    ) -> None:
        """Add feedback for confidence calibration learning."""
        self.confidence_calibrator.add_calibration_data(
            raw_confidence=raw_confidence,
            actual_accuracy=actual_accuracy,
            format_name=format_name
        )