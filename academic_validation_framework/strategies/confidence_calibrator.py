"""
Confidence Calibration System for Citation Validation

Provides sophisticated confidence calibration and uncertainty quantification
for academic citation validation results.
"""

import math
# numpy not required for this implementation
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import statistics


class CalibrationMethod(Enum):
    """Available confidence calibration methods."""
    TEMPERATURE_SCALING = "temperature_scaling"
    PLATT_SCALING = "platt_scaling"
    ISOTONIC_REGRESSION = "isotonic_regression"
    BAYESIAN_CALIBRATION = "bayesian_calibration"
    HISTOGRAM_BINNING = "histogram_binning"
    ENSEMBLE_AVERAGE = "ensemble_average"


@dataclass
class CalibrationData:
    """Data point for calibration learning."""
    raw_confidence: float
    actual_accuracy: float
    validation_evidence: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    format_name: str = ""
    sample_size: int = 1


@dataclass
class ConfidenceInterval:
    """Confidence interval for uncertainty quantification."""
    lower_bound: float
    upper_bound: float
    confidence_level: float
    method: str


@dataclass
class CalibrationResult:
    """Result of confidence calibration."""
    calibrated_confidence: float
    raw_confidence: float
    calibration_method: CalibrationMethod
    confidence_interval: Optional[ConfidenceInterval] = None
    reliability_score: float = 0.0
    uncertainty_estimate: float = 0.0
    
    # Calibration metadata
    calibration_strength: float = 0.0  # How much calibration was applied
    evidence_quality: float = 0.0      # Quality of supporting evidence
    historical_accuracy: float = 0.0   # Historical accuracy at this confidence level
    
    # Debug information
    calibration_factors: Dict[str, float] = field(default_factory=dict)
    raw_scores: Dict[str, float] = field(default_factory=dict)


class ConfidenceCalibrator:
    """
    Advanced confidence calibration system for citation validation.
    
    Provides multiple calibration algorithms, uncertainty quantification,
    and reliability assessment to improve confidence score accuracy.
    """
    
    def __init__(self, default_method: CalibrationMethod = CalibrationMethod.TEMPERATURE_SCALING):
        self.default_method = default_method
        self.calibration_history: List[CalibrationData] = []
        self.calibration_parameters: Dict[CalibrationMethod, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, float] = {}
        
        # Initialize default parameters
        self._initialize_parameters()
    
    def _initialize_parameters(self) -> None:
        """Initialize default calibration parameters."""
        self.calibration_parameters = {
            CalibrationMethod.TEMPERATURE_SCALING: {
                "temperature": 1.0,
                "learning_rate": 0.01,
                "min_temperature": 0.1,
                "max_temperature": 10.0
            },
            CalibrationMethod.PLATT_SCALING: {
                "A": 0.0,
                "B": 0.0,
                "learning_rate": 0.01,
                "regularization": 0.001
            },
            CalibrationMethod.BAYESIAN_CALIBRATION: {
                "prior_alpha": 1.0,
                "prior_beta": 1.0,
                "confidence_level": 0.95
            },
            CalibrationMethod.HISTOGRAM_BINNING: {
                "num_bins": 10,
                "min_samples_per_bin": 5,
                "smoothing_factor": 0.1
            }
        }
    
    def calibrate_confidence(
        self,
        raw_confidence: float,
        validation_evidence: List[Dict[str, Any]],
        format_name: str = "",
        method: Optional[CalibrationMethod] = None,
        sample_size: int = 1
    ) -> CalibrationResult:
        """
        Calibrate a raw confidence score using specified method.
        
        Args:
            raw_confidence: Raw confidence score (0.0 to 1.0)
            validation_evidence: List of evidence supporting the confidence
            format_name: Name of citation format being validated
            method: Calibration method to use (None = default)
            sample_size: Number of citations in validation sample
            
        Returns:
            CalibrationResult with calibrated confidence and metadata
        """
        if method is None:
            method = self.default_method
        
        # Validate input
        raw_confidence = max(0.0, min(1.0, raw_confidence))
        
        # Calculate evidence quality
        evidence_quality = self._assess_evidence_quality(validation_evidence)
        
        # Get historical accuracy
        historical_accuracy = self._get_historical_accuracy(raw_confidence, format_name)
        
        # Apply calibration method
        calibrated_confidence = self._apply_calibration_method(
            raw_confidence, method, format_name, evidence_quality, sample_size
        )
        
        # Calculate uncertainty estimate
        uncertainty = self._estimate_uncertainty(
            raw_confidence, calibrated_confidence, evidence_quality, sample_size
        )
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            calibrated_confidence, uncertainty, method
        )
        
        # Calculate reliability score
        reliability = self._calculate_reliability_score(
            calibrated_confidence, evidence_quality, historical_accuracy, sample_size
        )
        
        # Calculate calibration strength
        calibration_strength = abs(calibrated_confidence - raw_confidence)
        
        return CalibrationResult(
            calibrated_confidence=calibrated_confidence,
            raw_confidence=raw_confidence,
            calibration_method=method,
            confidence_interval=confidence_interval,
            reliability_score=reliability,
            uncertainty_estimate=uncertainty,
            calibration_strength=calibration_strength,
            evidence_quality=evidence_quality,
            historical_accuracy=historical_accuracy,
            calibration_factors=self._get_calibration_factors(method),
            raw_scores={
                "evidence_quality": evidence_quality,
                "historical_accuracy": historical_accuracy,
                "sample_size_factor": self._sample_size_factor(sample_size)
            }
        )
    
    def _apply_calibration_method(
        self,
        raw_confidence: float,
        method: CalibrationMethod,
        format_name: str,
        evidence_quality: float,
        sample_size: int
    ) -> float:
        """Apply specific calibration method."""
        
        if method == CalibrationMethod.TEMPERATURE_SCALING:
            return self._temperature_scaling(raw_confidence, format_name)
        
        elif method == CalibrationMethod.PLATT_SCALING:
            return self._platt_scaling(raw_confidence, format_name)
        
        elif method == CalibrationMethod.BAYESIAN_CALIBRATION:
            return self._bayesian_calibration(raw_confidence, evidence_quality, sample_size)
        
        elif method == CalibrationMethod.HISTOGRAM_BINNING:
            return self._histogram_binning(raw_confidence, format_name)
        
        elif method == CalibrationMethod.ENSEMBLE_AVERAGE:
            return self._ensemble_calibration(raw_confidence, format_name, evidence_quality, sample_size)
        
        else:
            # Fallback to simple adjustment
            return self._simple_calibration(raw_confidence, evidence_quality, sample_size)
    
    def _temperature_scaling(self, raw_confidence: float, format_name: str) -> float:
        """Apply temperature scaling calibration."""
        params = self.calibration_parameters[CalibrationMethod.TEMPERATURE_SCALING]
        temperature = params["temperature"]
        
        # Convert confidence to logits, apply temperature, convert back
        if raw_confidence <= 0.0:
            return 0.0
        elif raw_confidence >= 1.0:
            return 1.0
        
        # Convert to logits
        logit = math.log(raw_confidence / (1 - raw_confidence))
        
        # Apply temperature scaling
        scaled_logit = logit / temperature
        
        # Convert back to probability
        calibrated = 1 / (1 + math.exp(-scaled_logit))
        
        return max(0.0, min(1.0, calibrated))
    
    def _platt_scaling(self, raw_confidence: float, format_name: str) -> float:
        """Apply Platt scaling calibration."""
        params = self.calibration_parameters[CalibrationMethod.PLATT_SCALING]
        A = params["A"]
        B = params["B"]
        
        # Convert to logits
        if raw_confidence <= 0.0:
            logit = -10.0  # Very negative logit
        elif raw_confidence >= 1.0:
            logit = 10.0   # Very positive logit
        else:
            logit = math.log(raw_confidence / (1 - raw_confidence))
        
        # Apply Platt scaling: P(y=1|f) = 1 / (1 + exp(A*f + B))
        scaled_logit = A * logit + B
        calibrated = 1 / (1 + math.exp(-scaled_logit))
        
        return max(0.0, min(1.0, calibrated))
    
    def _bayesian_calibration(self, raw_confidence: float, evidence_quality: float, sample_size: int) -> float:
        """Apply Bayesian calibration with Beta distribution."""
        params = self.calibration_parameters[CalibrationMethod.BAYESIAN_CALIBRATION]
        prior_alpha = params["prior_alpha"]
        prior_beta = params["prior_beta"]
        
        # Estimate pseudo-counts from confidence and evidence
        evidence_weight = evidence_quality * sample_size
        
        # Calculate posterior parameters
        success_count = raw_confidence * evidence_weight
        failure_count = (1 - raw_confidence) * evidence_weight
        
        posterior_alpha = prior_alpha + success_count
        posterior_beta = prior_beta + failure_count
        
        # Posterior mean (Bayesian estimate)
        calibrated = posterior_alpha / (posterior_alpha + posterior_beta)
        
        return max(0.0, min(1.0, calibrated))
    
    def _histogram_binning(self, raw_confidence: float, format_name: str) -> float:
        """Apply histogram binning calibration."""
        params = self.calibration_parameters[CalibrationMethod.HISTOGRAM_BINNING]
        num_bins = params["num_bins"]
        
        # Find which bin this confidence falls into
        bin_index = min(int(raw_confidence * num_bins), num_bins - 1)
        
        # Get historical accuracy for this bin
        bin_accuracy = self._get_bin_accuracy(bin_index, format_name, num_bins)
        
        # Apply smoothing
        smoothing = params["smoothing_factor"]
        calibrated = (1 - smoothing) * bin_accuracy + smoothing * raw_confidence
        
        return max(0.0, min(1.0, calibrated))
    
    def _ensemble_calibration(
        self,
        raw_confidence: float,
        format_name: str,
        evidence_quality: float,
        sample_size: int
    ) -> float:
        """Apply ensemble of multiple calibration methods."""
        methods = [
            CalibrationMethod.TEMPERATURE_SCALING,
            CalibrationMethod.PLATT_SCALING,
            CalibrationMethod.BAYESIAN_CALIBRATION
        ]
        
        calibrated_scores = []
        weights = []
        
        for method in methods:
            try:
                score = self._apply_calibration_method(
                    raw_confidence, method, format_name, evidence_quality, sample_size
                )
                calibrated_scores.append(score)
                
                # Weight based on method reliability
                method_weight = self._get_method_weight(method, format_name)
                weights.append(method_weight)
                
            except Exception:
                continue
        
        if not calibrated_scores:
            return raw_confidence
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_sum = sum(score * weight for score, weight in zip(calibrated_scores, weights))
            return weighted_sum / total_weight
        else:
            return statistics.mean(calibrated_scores)
    
    def _simple_calibration(self, raw_confidence: float, evidence_quality: float, sample_size: int) -> float:
        """Simple heuristic calibration as fallback."""
        # Adjust confidence based on evidence quality
        evidence_factor = 0.5 + 0.5 * evidence_quality
        
        # Adjust based on sample size (larger samples = more reliable)
        sample_factor = min(1.0, math.log(sample_size + 1) / math.log(10))
        
        # Apply conservative adjustment
        calibrated = raw_confidence * evidence_factor * sample_factor
        
        # Add small uncertainty margin
        uncertainty_margin = 0.05 * (1 - evidence_quality)
        calibrated = max(uncertainty_margin, calibrated - uncertainty_margin)
        
        return max(0.0, min(1.0, calibrated))
    
    def _assess_evidence_quality(self, validation_evidence: List[Dict[str, Any]]) -> float:
        """Assess the quality of validation evidence."""
        if not validation_evidence:
            return 0.0
        
        total_quality = 0.0
        
        for evidence in validation_evidence:
            evidence_score = evidence.get("confidence_score", 0.0)
            rule_type = evidence.get("rule_applied", "")
            context = evidence.get("context", {})
            
            # Base quality from confidence score
            quality = evidence_score
            
            # Adjust based on rule type reliability
            if "pattern_match" in rule_type.lower():
                quality *= 0.8  # Pattern matching is moderately reliable
            elif "expert_rule" in rule_type.lower():
                quality *= 1.0  # Expert rules are highly reliable
            elif "heuristic" in rule_type.lower():
                quality *= 0.6  # Heuristics are less reliable
            
            # Adjust based on context richness
            context_richness = len(context) / 5.0  # Normalize to 0-1
            quality *= (0.7 + 0.3 * min(1.0, context_richness))
            
            total_quality += quality
        
        return min(1.0, total_quality / len(validation_evidence))
    
    def _get_historical_accuracy(self, confidence_level: float, format_name: str) -> float:
        """Get historical accuracy at this confidence level."""
        if not self.calibration_history:
            return 0.5  # Default neutral accuracy
        
        # Find historical data points near this confidence level
        tolerance = 0.1
        relevant_data = [
            data for data in self.calibration_history
            if (abs(data.raw_confidence - confidence_level) <= tolerance and
                (not format_name or data.format_name == format_name))
        ]
        
        if not relevant_data:
            return 0.5
        
        # Calculate average accuracy
        accuracies = [data.actual_accuracy for data in relevant_data]
        return statistics.mean(accuracies)
    
    def _estimate_uncertainty(
        self,
        raw_confidence: float,
        calibrated_confidence: float,
        evidence_quality: float,
        sample_size: int
    ) -> float:
        """Estimate uncertainty in the calibrated confidence."""
        # Base uncertainty from calibration adjustment
        calibration_uncertainty = abs(calibrated_confidence - raw_confidence)
        
        # Evidence uncertainty
        evidence_uncertainty = 1.0 - evidence_quality
        
        # Sample size uncertainty (smaller samples = higher uncertainty)
        sample_uncertainty = 1.0 / math.sqrt(sample_size + 1)
        
        # Model uncertainty (how well our calibration works)
        model_uncertainty = self._get_model_uncertainty()
        
        # Combine uncertainties (assuming independence)
        total_uncertainty = math.sqrt(
            calibration_uncertainty**2 +
            evidence_uncertainty**2 * 0.5 +
            sample_uncertainty**2 * 0.3 +
            model_uncertainty**2 * 0.2
        )
        
        return min(0.5, total_uncertainty)  # Cap at 0.5
    
    def _calculate_confidence_interval(
        self,
        calibrated_confidence: float,
        uncertainty: float,
        method: CalibrationMethod,
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """Calculate confidence interval for the calibrated confidence."""
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)
        
        # Calculate interval
        margin = z_score * uncertainty
        lower_bound = max(0.0, calibrated_confidence - margin)
        upper_bound = min(1.0, calibrated_confidence + margin)
        
        return ConfidenceInterval(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_level=confidence_level,
            method=method.value
        )
    
    def _calculate_reliability_score(
        self,
        calibrated_confidence: float,
        evidence_quality: float,
        historical_accuracy: float,
        sample_size: int
    ) -> float:
        """Calculate overall reliability score for the calibrated confidence."""
        # Base reliability from evidence quality
        reliability = evidence_quality * 0.4
        
        # Add historical performance component
        reliability += historical_accuracy * 0.3
        
        # Add sample size component
        sample_reliability = min(1.0, sample_size / 10.0)  # Normalize to 10 samples
        reliability += sample_reliability * 0.2
        
        # Add calibration confidence component
        confidence_reliability = 1.0 - abs(0.5 - calibrated_confidence) * 2  # Closer to 0.5 = less reliable
        reliability += confidence_reliability * 0.1
        
        return max(0.0, min(1.0, reliability))
    
    def _sample_size_factor(self, sample_size: int) -> float:
        """Calculate factor based on sample size."""
        return min(1.0, math.log(sample_size + 1) / math.log(20))  # Normalize to 20 samples
    
    def _get_calibration_factors(self, method: CalibrationMethod) -> Dict[str, float]:
        """Get current calibration factors for debugging."""
        return dict(self.calibration_parameters.get(method, {}))
    
    def _get_bin_accuracy(self, bin_index: int, format_name: str, num_bins: int) -> float:
        """Get historical accuracy for a confidence bin."""
        # Find historical data in this bin
        bin_start = bin_index / num_bins
        bin_end = (bin_index + 1) / num_bins
        
        relevant_data = [
            data for data in self.calibration_history
            if (bin_start <= data.raw_confidence < bin_end and
                (not format_name or data.format_name == format_name))
        ]
        
        if not relevant_data:
            return 0.5  # Default to neutral
        
        return statistics.mean([data.actual_accuracy for data in relevant_data])
    
    def _get_method_weight(self, method: CalibrationMethod, format_name: str) -> float:
        """Get weight for ensemble method based on historical performance."""
        # This would be based on historical performance tracking
        # For now, return default weights
        weights = {
            CalibrationMethod.TEMPERATURE_SCALING: 0.35,
            CalibrationMethod.PLATT_SCALING: 0.30,
            CalibrationMethod.BAYESIAN_CALIBRATION: 0.35
        }
        return weights.get(method, 0.33)
    
    def _get_model_uncertainty(self) -> float:
        """Get uncertainty in the calibration model itself."""
        # This would be based on calibration model validation
        # For now, return a reasonable default
        return 0.1
    
    def add_calibration_data(
        self,
        raw_confidence: float,
        actual_accuracy: float,
        format_name: str = "",
        sample_size: int = 1
    ) -> None:
        """Add a data point for calibration learning."""
        data_point = CalibrationData(
            raw_confidence=raw_confidence,
            actual_accuracy=actual_accuracy,
            format_name=format_name,
            sample_size=sample_size
        )
        
        self.calibration_history.append(data_point)
        
        # Optionally update calibration parameters based on new data
        self._update_calibration_parameters()
    
    def _update_calibration_parameters(self) -> None:
        """Update calibration parameters based on historical data."""
        if len(self.calibration_history) < 10:
            return  # Need minimum data for parameter updates
        
        # Update temperature scaling parameter
        self._update_temperature_parameter()
        
        # Update Platt scaling parameters
        self._update_platt_parameters()
    
    def _update_temperature_parameter(self) -> None:
        """Update temperature scaling parameter."""
        # Simple approach: minimize calibration error
        # In practice, this would use more sophisticated optimization
        
        best_temperature = 1.0
        best_error = float('inf')
        
        for temp in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]:
            error = self._calculate_calibration_error_for_temperature(temp)
            if error < best_error:
                best_error = error
                best_temperature = temp
        
        self.calibration_parameters[CalibrationMethod.TEMPERATURE_SCALING]["temperature"] = best_temperature
    
    def _calculate_calibration_error_for_temperature(self, temperature: float) -> float:
        """Calculate calibration error for a given temperature."""
        total_error = 0.0
        
        for data in self.calibration_history[-50:]:  # Use recent data
            # Apply temperature scaling
            if data.raw_confidence <= 0.0 or data.raw_confidence >= 1.0:
                calibrated = data.raw_confidence
            else:
                logit = math.log(data.raw_confidence / (1 - data.raw_confidence))
                scaled_logit = logit / temperature
                calibrated = 1 / (1 + math.exp(-scaled_logit))
            
            # Calculate error
            error = abs(calibrated - data.actual_accuracy)
            total_error += error
        
        return total_error / len(self.calibration_history[-50:])
    
    def _update_platt_parameters(self) -> None:
        """Update Platt scaling parameters using simple gradient descent."""
        # This is a simplified version - real implementation would use proper optimization
        params = self.calibration_parameters[CalibrationMethod.PLATT_SCALING]
        learning_rate = params["learning_rate"]
        
        # Calculate gradients (simplified)
        grad_A, grad_B = self._calculate_platt_gradients()
        
        # Update parameters
        params["A"] -= learning_rate * grad_A
        params["B"] -= learning_rate * grad_B
    
    def _calculate_platt_gradients(self) -> Tuple[float, float]:
        """Calculate gradients for Platt scaling parameters."""
        # Simplified gradient calculation
        grad_A = 0.0
        grad_B = 0.0
        
        for data in self.calibration_history[-50:]:
            if data.raw_confidence <= 0.0 or data.raw_confidence >= 1.0:
                continue
            
            logit = math.log(data.raw_confidence / (1 - data.raw_confidence))
            
            # Current prediction
            params = self.calibration_parameters[CalibrationMethod.PLATT_SCALING]
            scaled_logit = params["A"] * logit + params["B"]
            prediction = 1 / (1 + math.exp(-scaled_logit))
            
            # Error
            error = prediction - data.actual_accuracy
            
            # Gradients
            grad_A += error * logit
            grad_B += error
        
        count = len(self.calibration_history[-50:])
        return grad_A / count if count > 0 else 0.0, grad_B / count if count > 0 else 0.0
    
    def get_calibration_summary(self) -> Dict[str, Any]:
        """Get summary of calibration system state."""
        return {
            "default_method": self.default_method.value,
            "calibration_data_points": len(self.calibration_history),
            "calibration_parameters": {
                method.value: params
                for method, params in self.calibration_parameters.items()
            },
            "recent_performance": self._get_recent_performance(),
            "available_methods": [method.value for method in CalibrationMethod]
        }
    
    def _get_recent_performance(self) -> Dict[str, float]:
        """Get recent calibration performance metrics."""
        if len(self.calibration_history) < 5:
            return {"insufficient_data": True}
        
        recent_data = self.calibration_history[-20:]
        
        # Calculate metrics
        raw_errors = [abs(d.raw_confidence - d.actual_accuracy) for d in recent_data]
        avg_raw_error = statistics.mean(raw_errors)
        
        return {
            "average_raw_error": avg_raw_error,
            "data_points": len(recent_data),
            "average_sample_size": statistics.mean([d.sample_size for d in recent_data])
        }