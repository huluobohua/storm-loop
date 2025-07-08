"""
Real bias detection implementation for academic research validation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import logging

from ..interfaces import BaseValidator
from ..models import (
    ValidationResult,
    ValidationStatus,
    ResearchData,
    BiasAnalysisResult,
    BiasType
)

logger = logging.getLogger(__name__)


class RealBiasDetector(BaseValidator):
    """Real implementation of bias detection in academic research."""
    
    def __init__(self):
        super().__init__(
            name="Real Bias Detector",
            version="2.0.0"
        )
        self._config = {
            "min_bias_threshold": 0.3,
            "check_funding_bias": True,
            "check_citation_bias": True,
            "check_language_bias": True,
            "check_geographic_bias": True
        }
        
        # Bias indicators and patterns
        self._bias_indicators = {
            BiasType.CONFIRMATION: {
                "patterns": [
                    r"as expected",
                    r"confirms our hypothesis",
                    r"supports our theory",
                    r"consistent with our predictions",
                    r"validates our approach"
                ],
                "keywords": [
                    "expected", "anticipated", "predicted", "hypothesized",
                    "confirmed", "validated", "supported", "demonstrated"
                ],
                "severity_weight": 0.8
            },
            BiasType.PUBLICATION: {
                "patterns": [
                    r"significant results",
                    r"positive findings",
                    r"novel results",
                    r"groundbreaking",
                    r"first to show"
                ],
                "keywords": [
                    "significant", "positive", "novel", "groundbreaking",
                    "unprecedented", "remarkable", "exceptional"
                ],
                "severity_weight": 0.7
            },
            BiasType.SELECTION: {
                "patterns": [
                    r"selected (?:only|specifically)",
                    r"excluded (?:because|due to)",
                    r"focused on (?:only|specifically)",
                    r"limited to",
                    r"restricted to"
                ],
                "keywords": [
                    "selected", "chosen", "picked", "excluded",
                    "omitted", "ignored", "overlooked"
                ],
                "severity_weight": 0.9
            },
            BiasType.FUNDING: {
                "patterns": [
                    r"funded by",
                    r"supported by",
                    r"grant from",
                    r"sponsored by",
                    r"financial support"
                ],
                "keywords": [
                    "funded", "sponsored", "supported", "grant",
                    "financial", "commercial", "industry"
                ],
                "severity_weight": 0.6
            },
            BiasType.SAMPLING: {
                "patterns": [
                    r"convenience sample",
                    r"self-selected",
                    r"volunteer",
                    r"non-random",
                    r"purposive sampling"
                ],
                "keywords": [
                    "convenience", "volunteer", "self-selected",
                    "non-random", "purposive", "snowball"
                ],
                "severity_weight": 0.8
            },
            BiasType.REPORTING: {
                "patterns": [
                    r"selectively reported",
                    r"post[- ]hoc analysis",
                    r"exploratory analysis",
                    r"data mining",
                    r"p-hacking"
                ],
                "keywords": [
                    "selective", "post-hoc", "exploratory",
                    "retrospective", "unplanned", "data-driven"
                ],
                "severity_weight": 0.9
            },
            BiasType.CITATION: {
                "patterns": [
                    r"predominantly cites",
                    r"mainly references",
                    r"primarily draws from",
                    r"self-citation",
                    r"citation network"
                ],
                "keywords": [
                    "self-citation", "citation-network", "predominantly",
                    "mainly", "primarily", "exclusively"
                ],
                "severity_weight": 0.5
            }
        }
        
        # Language bias indicators
        self._language_bias_terms = {
            "absolute": ["always", "never", "all", "none", "every", "no one"],
            "exaggeration": ["extremely", "incredibly", "amazingly", "revolutionary"],
            "subjective": ["believe", "feel", "think", "seems", "appears"],
            "emotional": ["exciting", "disappointing", "surprising", "shocking"]
        }
        
        # Geographic bias indicators
        self._geographic_bias_patterns = {
            "western_centric": ["western", "developed countries", "first world", "global north"],
            "regional_focus": ["only in", "limited to region", "specific to country"],
            "exclusion": ["excluded countries", "not applicable to", "western-only"]
        }
        
    async def validate(self, data: ResearchData) -> ValidationResult:
        """
        Perform comprehensive bias detection on research data.
        
        Args:
            data: Research data to analyze
            
        Returns:
            Detailed bias detection results
        """
        try:
            # Extract all text for analysis
            full_text = self._extract_text_for_analysis(data)
            
            # Detect various types of bias
            bias_results = []
            overall_bias_score = 0.0
            
            # Check each bias type
            for bias_type, indicators in self._bias_indicators.items():
                result = self._detect_bias_type(bias_type, indicators, full_text, data)
                bias_results.append(result)
                overall_bias_score += result.confidence_score * indicators["severity_weight"]
            
            # Additional bias checks
            if self._config["check_language_bias"]:
                language_bias = self._detect_language_bias(full_text)
                bias_results.append(language_bias)
                overall_bias_score += language_bias.confidence_score * 0.6
            
            if self._config["check_geographic_bias"]:
                geographic_bias = self._detect_geographic_bias(full_text, data)
                bias_results.append(geographic_bias)
                overall_bias_score += geographic_bias.confidence_score * 0.7
            
            # Normalize overall score
            overall_bias_score = overall_bias_score / len(bias_results) if bias_results else 0.0
            
            # Determine status
            if overall_bias_score < 0.3:
                status = ValidationStatus.PASSED
            elif overall_bias_score < 0.6:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            # Generate comprehensive report
            bias_summary = self._generate_bias_summary(bias_results)
            recommendations = self._generate_bias_recommendations(bias_results, overall_bias_score)
            
            return ValidationResult(
                validator_name=self.name,
                test_name="Comprehensive Bias Detection",
                status=status,
                score=1.0 - overall_bias_score,  # Convert to quality score
                details={
                    "overall_bias_score": overall_bias_score,
                    "bias_types_detected": [r.bias_types for r in bias_results if r.bias_detected],
                    "bias_analysis": bias_summary,
                    "detailed_results": [self._format_bias_result(r) for r in bias_results],
                    "severity_distribution": self._calculate_severity_distribution(bias_results),
                    "mitigation_strategies": self._generate_mitigation_strategies(bias_results)
                },
                recommendations=recommendations,
                metadata={
                    "text_length": len(full_text),
                    "bias_types_checked": len(self._bias_indicators),
                    "detection_threshold": self._config["min_bias_threshold"],
                    "validator_version": self.version
                }
            )
            
        except Exception as e:
            logger.error(f"Bias detection error: {str(e)}", exc_info=True)
            return self._create_error_result(str(e))
    
    def _extract_text_for_analysis(self, data: ResearchData) -> str:
        """Extract and combine all relevant text for bias analysis."""
        text_parts = [
            data.title,
            data.abstract,
            data.methodology
        ]
        
        # Add raw content if available
        if data.raw_content:
            text_parts.append(data.raw_content)
        
        # Add paper abstracts if available
        if data.papers:
            for paper in data.papers[:10]:  # Limit to first 10 papers
                if isinstance(paper, dict):
                    if "abstract" in paper:
                        text_parts.append(paper["abstract"])
                    if "title" in paper:
                        text_parts.append(paper["title"])
        
        return "\n\n".join(filter(None, text_parts))
    
    def _detect_bias_type(
        self,
        bias_type: BiasType,
        indicators: Dict[str, Any],
        text: str,
        data: ResearchData
    ) -> BiasAnalysisResult:
        """Detect a specific type of bias."""
        text_lower = text.lower()
        evidence = []
        pattern_matches = 0
        keyword_matches = 0
        
        # Check patterns
        for pattern in indicators["patterns"]:
            matches = re.findall(pattern, text_lower)
            if matches:
                pattern_matches += len(matches)
                evidence.extend([f"Pattern '{pattern}' found: {match}" for match in matches[:3]])
        
        # Check keywords
        keyword_counts = Counter()
        words = text_lower.split()
        for keyword in indicators["keywords"]:
            count = words.count(keyword)
            if count > 0:
                keyword_matches += count
                keyword_counts[keyword] = count
        
        # Calculate confidence score
        text_length = len(words)
        pattern_density = pattern_matches / (text_length / 1000) if text_length > 0 else 0
        keyword_density = keyword_matches / (text_length / 100) if text_length > 0 else 0
        
        confidence_score = min(
            (pattern_density * 0.6 + keyword_density * 0.4) * indicators["severity_weight"],
            1.0
        )
        
        # Special checks for specific bias types
        if bias_type == BiasType.FUNDING and self._config["check_funding_bias"]:
            funding_score = self._check_funding_disclosure(text, data)
            confidence_score = (confidence_score + funding_score) / 2
            
        elif bias_type == BiasType.CITATION and self._config["check_citation_bias"]:
            citation_score = self._check_citation_patterns(data)
            confidence_score = (confidence_score + citation_score) / 2
        
        # Determine if bias is detected
        bias_detected = confidence_score >= self._config["min_bias_threshold"]
        
        # Add keyword evidence
        if keyword_counts:
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            evidence.append(f"High-frequency bias indicators: {dict(top_keywords)}")
        
        # Determine severity
        if confidence_score < 0.3:
            severity = "low"
        elif confidence_score < 0.6:
            severity = "medium"
        else:
            severity = "high"
        
        # Generate mitigation recommendations
        mitigation = self._generate_specific_mitigation(bias_type, confidence_score, evidence)
        
        return BiasAnalysisResult(
            bias_detected=bias_detected,
            bias_types=[bias_type] if bias_detected else [],
            confidence_score=confidence_score,
            severity=severity,
            evidence=evidence[:10],  # Limit evidence to top 10
            mitigation_recommendations=mitigation,
            original_confidence=confidence_score,
            revised_confidence=None  # Could be updated after mitigation
        )
    
    def _detect_language_bias(self, text: str) -> BiasAnalysisResult:
        """Detect language-based bias in the text."""
        text_lower = text.lower()
        words = text_lower.split()
        evidence = []
        bias_score = 0.0
        
        # Check for absolute language
        absolute_count = 0
        for term in self._language_bias_terms["absolute"]:
            count = words.count(term)
            if count > 0:
                absolute_count += count
                evidence.append(f"Absolute language: '{term}' used {count} times")
        
        # Check for exaggeration
        exaggeration_count = 0
        for term in self._language_bias_terms["exaggeration"]:
            count = words.count(term)
            if count > 0:
                exaggeration_count += count
                evidence.append(f"Exaggerated language: '{term}' used {count} times")
        
        # Check for subjective language
        subjective_count = 0
        for term in self._language_bias_terms["subjective"]:
            count = words.count(term)
            if count > 0:
                subjective_count += count
        
        # Calculate bias score
        total_bias_terms = absolute_count + exaggeration_count + subjective_count
        bias_density = total_bias_terms / (len(words) / 100) if words else 0
        bias_score = min(bias_density * 0.1, 1.0)  # Scale appropriately
        
        # Check for hedging language (which can indicate awareness of limitations)
        hedging_terms = ["may", "might", "could", "possibly", "potentially", "suggest"]
        hedging_count = sum(words.count(term) for term in hedging_terms)
        
        # Adjust score based on hedging (reduces bias score)
        if hedging_count > 5:
            bias_score *= 0.8
            evidence.append(f"Appropriate hedging language detected ({hedging_count} instances)")
        
        return BiasAnalysisResult(
            bias_detected=bias_score >= 0.3,
            bias_types=[BiasType.REPORTING] if bias_score >= 0.3 else [],
            confidence_score=bias_score,
            severity="low" if bias_score < 0.3 else "medium" if bias_score < 0.6 else "high",
            evidence=evidence[:10],
            mitigation_recommendations=[
                "Use more neutral, objective language",
                "Avoid absolute statements without strong evidence",
                "Replace subjective terms with measurable criteria"
            ] if bias_score >= 0.3 else []
        )
    
    def _detect_geographic_bias(self, text: str, data: ResearchData) -> BiasAnalysisResult:
        """Detect geographic or cultural bias."""
        text_lower = text.lower()
        evidence = []
        bias_indicators = 0
        
        # Check for western-centric language
        for term in self._geographic_bias_patterns["western_centric"]:
            if term in text_lower:
                bias_indicators += 1
                evidence.append(f"Western-centric term: '{term}'")
        
        # Check for regional limitations
        for pattern in self._geographic_bias_patterns["regional_focus"]:
            if pattern in text_lower:
                bias_indicators += 1
                evidence.append(f"Regional limitation: '{pattern}'")
        
        # Analyze geographic diversity in citations/data
        if data.papers:
            countries_mentioned = set()
            for paper in data.papers:
                if isinstance(paper, dict):
                    # Simple country detection (could be enhanced)
                    text_to_check = str(paper.get("abstract", "")) + str(paper.get("affiliation", ""))
                    common_countries = ["usa", "uk", "china", "germany", "japan", "india", "brazil"]
                    for country in common_countries:
                        if country in text_to_check.lower():
                            countries_mentioned.add(country)
            
            if len(countries_mentioned) < 3:
                bias_indicators += 1
                evidence.append(f"Limited geographic diversity: {len(countries_mentioned)} countries")
        
        # Calculate bias score
        bias_score = min(bias_indicators * 0.2, 1.0)
        
        return BiasAnalysisResult(
            bias_detected=bias_score >= 0.3,
            bias_types=[BiasType.SELECTION] if bias_score >= 0.3 else [],
            confidence_score=bias_score,
            severity="low" if bias_score < 0.3 else "medium" if bias_score < 0.6 else "high",
            evidence=evidence,
            mitigation_recommendations=[
                "Include research from diverse geographic regions",
                "Acknowledge geographic limitations explicitly",
                "Avoid generalizing findings beyond studied populations"
            ] if bias_score >= 0.3 else []
        )
    
    def _check_funding_disclosure(self, text: str, data: ResearchData) -> float:
        """Check for proper funding disclosure and potential conflicts."""
        text_lower = text.lower()
        
        # Check for funding disclosure
        has_funding_section = any(
            section in text_lower
            for section in ["funding", "financial disclosure", "conflict of interest", "competing interests"]
        )
        
        # Check for commercial funding
        commercial_indicators = ["company", "corporation", "inc.", "ltd.", "pharmaceutical", "industry"]
        commercial_funding = any(indicator in text_lower for indicator in commercial_indicators)
        
        # Calculate score
        if not has_funding_section:
            return 0.8  # High bias score for missing disclosure
        elif commercial_funding and "no conflict" not in text_lower:
            return 0.6  # Moderate bias score for commercial funding
        else:
            return 0.2  # Low bias score for proper disclosure
    
    def _check_citation_patterns(self, data: ResearchData) -> float:
        """Analyze citation patterns for bias."""
        if not data.citations:
            return 0.0
        
        # Check for self-citation
        authors_in_paper = set()
        if data.metadata.get("authors"):
            authors_in_paper = set(author.lower() for author in data.metadata["authors"])
        
        self_citations = 0
        same_journal_citations = 0
        recent_only_citations = 0
        
        for citation in data.citations:
            citation_lower = citation.lower()
            
            # Check self-citation
            if any(author in citation_lower for author in authors_in_paper):
                self_citations += 1
            
            # Check if citing mostly from same journal
            if data.metadata.get("journal") and data.metadata["journal"].lower() in citation_lower:
                same_journal_citations += 1
            
            # Check if only citing recent papers (last 5 years)
            import re
            year_match = re.search(r"20\d{2}", citation)
            if year_match:
                year = int(year_match.group())
                if year >= 2019:  # Assuming current year context
                    recent_only_citations += 1
        
        # Calculate bias indicators
        total_citations = len(data.citations)
        self_citation_ratio = self_citations / total_citations
        same_journal_ratio = same_journal_citations / total_citations
        recent_only_ratio = recent_only_citations / total_citations
        
        # Calculate overall citation bias score
        bias_score = 0.0
        if self_citation_ratio > 0.2:  # More than 20% self-citation
            bias_score += 0.3
        if same_journal_ratio > 0.3:  # More than 30% from same journal
            bias_score += 0.2
        if recent_only_ratio > 0.9:  # More than 90% recent papers only
            bias_score += 0.2
        
        return min(bias_score, 1.0)
    
    def _generate_bias_summary(self, bias_results: List[BiasAnalysisResult]) -> Dict[str, Any]:
        """Generate a summary of all detected biases."""
        detected_biases = []
        total_evidence = []
        
        for result in bias_results:
            if result.bias_detected:
                detected_biases.extend(result.bias_types)
                total_evidence.extend(result.evidence[:3])  # Top 3 evidence per bias
        
        # Count bias types
        bias_counts = Counter(detected_biases)
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence_score for r in bias_results) / len(bias_results) if bias_results else 0
        
        # Identify most severe biases
        severe_biases = [
            r for r in bias_results
            if r.bias_detected and r.severity in ["medium", "high"]
        ]
        
        return {
            "total_biases_detected": len(detected_biases),
            "unique_bias_types": len(set(detected_biases)),
            "bias_type_distribution": dict(bias_counts),
            "average_confidence": avg_confidence,
            "severe_bias_count": len(severe_biases),
            "top_evidence": total_evidence[:10],
            "most_common_bias": bias_counts.most_common(1)[0] if bias_counts else None
        }
    
    def _calculate_severity_distribution(self, bias_results: List[BiasAnalysisResult]) -> Dict[str, int]:
        """Calculate distribution of bias severities."""
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        
        for result in bias_results:
            if result.bias_detected:
                severity_counts[result.severity] += 1
        
        return severity_counts
    
    def _generate_mitigation_strategies(self, bias_results: List[BiasAnalysisResult]) -> List[str]:
        """Generate comprehensive mitigation strategies."""
        strategies = set()
        
        for result in bias_results:
            if result.bias_detected:
                strategies.update(result.mitigation_recommendations)
        
        # Add general strategies
        if any(r.bias_detected for r in bias_results):
            strategies.add("Consider peer review from researchers with different perspectives")
            strategies.add("Explicitly acknowledge limitations and potential biases")
            strategies.add("Use standardized reporting guidelines (e.g., CONSORT, STROBE)")
        
        return list(strategies)[:10]  # Top 10 strategies
    
    def _generate_specific_mitigation(
        self,
        bias_type: BiasType,
        confidence_score: float,
        evidence: List[str]
    ) -> List[str]:
        """Generate bias-specific mitigation recommendations."""
        mitigations = []
        
        if bias_type == BiasType.CONFIRMATION:
            mitigations.extend([
                "Pre-register hypotheses and analysis plans",
                "Report all results, including negative findings",
                "Consider alternative explanations for findings"
            ])
        
        elif bias_type == BiasType.PUBLICATION:
            mitigations.extend([
                "Publish in journals that accept negative results",
                "Use registered reports format",
                "Report effect sizes and confidence intervals"
            ])
        
        elif bias_type == BiasType.SELECTION:
            mitigations.extend([
                "Use systematic selection criteria",
                "Report all inclusion/exclusion decisions",
                "Consider selection bias in limitations"
            ])
        
        elif bias_type == BiasType.FUNDING:
            mitigations.extend([
                "Disclose all funding sources transparently",
                "Declare any conflicts of interest",
                "Consider independent replication"
            ])
        
        elif bias_type == BiasType.SAMPLING:
            mitigations.extend([
                "Use probability sampling when possible",
                "Clearly describe sampling limitations",
                "Discuss generalizability constraints"
            ])
        
        elif bias_type == BiasType.REPORTING:
            mitigations.extend([
                "Follow reporting guidelines (CONSORT, STROBE)",
                "Report all measured outcomes",
                "Avoid selective outcome reporting"
            ])
        
        elif bias_type == BiasType.CITATION:
            mitigations.extend([
                "Diversify citation sources",
                "Include contradictory evidence",
                "Limit self-citations to essential references"
            ])
        
        return mitigations[:5]  # Top 5 most relevant
    
    def _format_bias_result(self, result: BiasAnalysisResult) -> Dict[str, Any]:
        """Format a bias result for output."""
        return {
            "bias_detected": result.bias_detected,
            "bias_types": [bt.value for bt in result.bias_types],
            "confidence": round(result.confidence_score, 3),
            "severity": result.severity,
            "top_evidence": result.evidence[:3],
            "mitigation_count": len(result.mitigation_recommendations)
        }
    
    def _generate_bias_recommendations(
        self,
        bias_results: List[BiasAnalysisResult],
        overall_score: float
    ) -> List[str]:
        """Generate overall recommendations based on bias analysis."""
        recommendations = []
        
        # General recommendations based on overall score
        if overall_score >= 0.6:
            recommendations.append(
                "CRITICAL: Multiple significant biases detected. Major revision needed."
            )
        elif overall_score >= 0.3:
            recommendations.append(
                "WARNING: Moderate bias detected. Review and address identified issues."
            )
        else:
            recommendations.append(
                "Good: Low bias detected. Minor improvements may enhance objectivity."
            )
        
        # Specific recommendations for detected biases
        bias_types_detected = set()
        for result in bias_results:
            if result.bias_detected:
                bias_types_detected.update(result.bias_types)
        
        if BiasType.CONFIRMATION in bias_types_detected:
            recommendations.append(
                "Address confirmation bias by discussing alternative interpretations"
            )
        
        if BiasType.PUBLICATION in bias_types_detected:
            recommendations.append(
                "Consider publication bias impact on literature review"
            )
        
        if BiasType.SELECTION in bias_types_detected:
            recommendations.append(
                "Review selection criteria for potential systematic exclusions"
            )
        
        if BiasType.FUNDING in bias_types_detected:
            recommendations.append(
                "Ensure transparent funding disclosure and conflict of interest statement"
            )
        
        # Add top mitigation strategies
        all_mitigations = []
        for result in bias_results:
            if result.bias_detected:
                all_mitigations.extend(result.mitigation_recommendations)
        
        # Get most common mitigations
        mitigation_counts = Counter(all_mitigations)
        top_mitigations = mitigation_counts.most_common(3)
        
        for mitigation, _ in top_mitigations:
            if mitigation not in recommendations:
                recommendations.append(mitigation)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _create_error_result(self, error_message: str) -> ValidationResult:
        """Create error result for bias detection."""
        return ValidationResult(
            validator_name=self.name,
            test_name="Bias Detection",
            status=ValidationStatus.ERROR,
            score=0.0,
            error_message=f"Bias detection error: {error_message}",
            recommendations=[
                "Fix the error and retry bias detection",
                "Ensure research data is properly formatted",
                "Contact support if issue persists"
            ]
        )