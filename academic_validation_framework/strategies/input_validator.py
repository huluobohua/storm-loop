"""
Input Validation Layer for Academic Citation Validation

Provides comprehensive input validation, sanitization, and security checks
for citation data before processing by format-specific validators.
"""

import re
import html
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import unicodedata


class ValidationStrictness(Enum):
    """Levels of validation strictness."""
    PERMISSIVE = "permissive"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class InputValidationResult:
    """Result of input validation checks."""
    is_valid: bool
    sanitized_input: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    encoding_issues: List[str] = field(default_factory=list)
    content_issues: List[str] = field(default_factory=list)
    
    # Statistics
    original_count: int = 0
    processed_count: int = 0
    filtered_count: int = 0
    
    # Metadata
    strictness_level: ValidationStrictness = ValidationStrictness.STANDARD
    processing_notes: List[str] = field(default_factory=list)


class InputValidator:
    """
    Comprehensive input validation and sanitization for citation data.
    
    Provides security-focused validation to prevent XSS, injection attacks,
    and other security vulnerabilities while ensuring data quality.
    """
    
    def __init__(self, strictness: ValidationStrictness = ValidationStrictness.STANDARD):
        self.strictness = strictness
        self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules based on strictness level."""
        # Security patterns (always enforced)
        self.security_patterns = {
            "script_tags": re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            "javascript": re.compile(r'javascript:', re.IGNORECASE),
            "data_urls": re.compile(r'data:', re.IGNORECASE),
            "sql_injection": re.compile(r'(union\s+select|drop\s+table|insert\s+into|delete\s+from)', re.IGNORECASE),
            "html_entities": re.compile(r'&[a-zA-Z][a-zA-Z0-9]+;'),
            "html_tags": re.compile(r'<[^>]+>'),
            "suspicious_chars": re.compile(r'[<>"\'\x00-\x1f\x7f-\x9f]'),
        }
        
        # Content validation patterns (strictness-dependent)
        if self.strictness == ValidationStrictness.PERMISSIVE:
            self.max_citation_length = 2000
            self.min_citation_length = 5
            self.max_citations_count = 1000
        elif self.strictness == ValidationStrictness.STANDARD:
            self.max_citation_length = 1000
            self.min_citation_length = 10
            self.max_citations_count = 500
        elif self.strictness == ValidationStrictness.STRICT:
            self.max_citation_length = 800
            self.min_citation_length = 20
            self.max_citations_count = 200
        else:  # PARANOID
            self.max_citation_length = 600
            self.min_citation_length = 30
            self.max_citations_count = 100
        
        # Allowed patterns for different strictness levels
        self.content_patterns = {
            "basic_citation": re.compile(r'^[A-Za-z0-9\s\.,;:()\[\]&"\'-]+$'),
            "extended_citation": re.compile(r'^[A-Za-z0-9\s\.,;:()\[\]&"\'-_/\\*#@+=?!]+$'),
            "unicode_citation": re.compile(r'^[\w\s\.,;:()\[\]&"\'-_/\\*#@+=?!]+$', re.UNICODE),
        }
    
    def validate_and_sanitize(self, citations: List[str]) -> InputValidationResult:
        """
        Validate and sanitize a list of citations.
        
        Args:
            citations: List of citation strings to validate
            
        Returns:
            InputValidationResult with validation results and sanitized data
        """
        if not isinstance(citations, list):
            return InputValidationResult(
                is_valid=False,
                errors=["Input must be a list of strings"],
                original_count=0,
                processed_count=0
            )
        
        result = InputValidationResult(
            is_valid=True,
            original_count=len(citations),
            strictness_level=self.strictness
        )
        
        # Basic count validation
        if len(citations) == 0:
            result.warnings.append("No citations provided")
            result.processed_count = 0
            return result
        
        if len(citations) > self.max_citations_count:
            result.errors.append(f"Too many citations: {len(citations)} (max: {self.max_citations_count})")
            result.is_valid = False
        
        sanitized_citations = []
        
        for i, citation in enumerate(citations):
            # Validate individual citation
            citation_result = self._validate_single_citation(citation, i + 1)
            
            if citation_result["is_valid"]:
                sanitized_citations.append(citation_result["sanitized"])
                result.processing_notes.extend(citation_result["notes"])
            else:
                result.filtered_count += 1
                result.errors.extend(citation_result["errors"])
                result.warnings.extend(citation_result["warnings"])
                result.security_issues.extend(citation_result["security_issues"])
                result.encoding_issues.extend(citation_result["encoding_issues"])
                result.content_issues.extend(citation_result["content_issues"])
                
                # In strict modes, fail completely on invalid citations
                if self.strictness in [ValidationStrictness.STRICT, ValidationStrictness.PARANOID]:
                    result.is_valid = False
        
        result.sanitized_input = sanitized_citations
        result.processed_count = len(sanitized_citations)
        
        # Final validation
        if result.processed_count == 0 and result.original_count > 0:
            result.errors.append("All citations were filtered out due to validation issues")
            result.is_valid = False
        
        # Security assessment
        if result.security_issues:
            result.errors.append(f"Security issues detected: {len(result.security_issues)} items")
            result.is_valid = False
        
        return result
    
    def _validate_single_citation(self, citation: Any, index: int) -> Dict[str, Any]:
        """
        Validate and sanitize a single citation.
        
        Args:
            citation: Citation to validate (should be string)
            index: Index of citation for error reporting
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "is_valid": True,
            "sanitized": "",
            "errors": [],
            "warnings": [],
            "security_issues": [],
            "encoding_issues": [],
            "content_issues": [],
            "notes": []
        }
        
        # Type validation
        if not isinstance(citation, str):
            result["is_valid"] = False
            result["errors"].append(f"Citation {index}: Must be a string, got {type(citation).__name__}")
            return result
        
        # Basic sanitization
        try:
            # Normalize Unicode
            citation = unicodedata.normalize('NFKC', citation)
            
            # Strip whitespace
            citation = citation.strip()
            
            # Basic length check
            if len(citation) == 0:
                result["warnings"].append(f"Citation {index}: Empty after sanitization")
                result["is_valid"] = False
                return result
            
            if len(citation) < self.min_citation_length:
                result["content_issues"].append(
                    f"Citation {index}: Too short ({len(citation)} chars, min: {self.min_citation_length})"
                )
                if self.strictness != ValidationStrictness.PERMISSIVE:
                    result["is_valid"] = False
                    return result
            
            if len(citation) > self.max_citation_length:
                result["content_issues"].append(
                    f"Citation {index}: Too long ({len(citation)} chars, max: {self.max_citation_length})"
                )
                # Truncate if in permissive mode, otherwise fail
                if self.strictness == ValidationStrictness.PERMISSIVE:
                    citation = citation[:self.max_citation_length]
                    result["notes"].append(f"Citation {index}: Truncated to {self.max_citation_length} characters")
                else:
                    result["is_valid"] = False
                    return result
            
        except Exception as e:
            result["encoding_issues"].append(f"Citation {index}: Unicode normalization failed: {str(e)}")
            result["is_valid"] = False
            return result
        
        # Security validation
        security_valid, security_issues = self._check_security(citation, index)
        if not security_valid:
            result["security_issues"].extend(security_issues)
            result["is_valid"] = False
            return result
        
        # Content validation
        content_valid, content_issues = self._check_content(citation, index)
        result["content_issues"].extend(content_issues)
        
        if not content_valid and self.strictness != ValidationStrictness.PERMISSIVE:
            result["is_valid"] = False
            return result
        
        # HTML sanitization
        citation = self._sanitize_html(citation)
        
        # Final sanitization
        citation = self._final_sanitization(citation)
        
        result["sanitized"] = citation
        return result
    
    def _check_security(self, citation: str, index: int) -> Tuple[bool, List[str]]:
        """
        Check for security vulnerabilities in citation.
        
        Args:
            citation: Citation string to check
            index: Citation index for error reporting
            
        Returns:
            Tuple of (is_secure, security_issues)
        """
        issues = []
        
        # Check for script tags
        if self.security_patterns["script_tags"].search(citation):
            issues.append(f"Citation {index}: Contains script tags")
        
        # Check for JavaScript URLs
        if self.security_patterns["javascript"].search(citation):
            issues.append(f"Citation {index}: Contains javascript: URLs")
        
        # Check for data URLs (can be used for XSS)
        if self.security_patterns["data_urls"].search(citation):
            issues.append(f"Citation {index}: Contains data: URLs")
        
        # Check for SQL injection patterns
        if self.security_patterns["sql_injection"].search(citation):
            issues.append(f"Citation {index}: Contains SQL injection patterns")
        
        # Check for suspicious characters
        if self.strictness == ValidationStrictness.PARANOID:
            if self.security_patterns["suspicious_chars"].search(citation):
                issues.append(f"Citation {index}: Contains potentially dangerous characters")
        
        # Check for excessive HTML entities (potential encoding attack)
        html_entities = self.security_patterns["html_entities"].findall(citation)
        if len(html_entities) > 10:  # Arbitrary threshold
            issues.append(f"Citation {index}: Excessive HTML entities detected ({len(html_entities)})")
        
        return len(issues) == 0, issues
    
    def _check_content(self, citation: str, index: int) -> Tuple[bool, List[str]]:
        """
        Check content validity based on strictness level.
        
        Args:
            citation: Citation string to check
            index: Citation index for error reporting
            
        Returns:
            Tuple of (is_valid, content_issues)
        """
        issues = []
        
        # Character set validation based on strictness
        if self.strictness == ValidationStrictness.STRICT:
            if not self.content_patterns["basic_citation"].match(citation):
                issues.append(f"Citation {index}: Contains non-standard characters")
        elif self.strictness == ValidationStrictness.PARANOID:
            if not self.content_patterns["basic_citation"].match(citation):
                issues.append(f"Citation {index}: Contains non-basic characters")
        else:
            # Standard or permissive - allow extended character set
            if not self.content_patterns["unicode_citation"].match(citation):
                issues.append(f"Citation {index}: Contains invalid characters")
        
        # Check for suspicious patterns
        if citation.count('"') % 2 != 0:
            issues.append(f"Citation {index}: Unmatched quotation marks")
        
        if citation.count('(') != citation.count(')'):
            issues.append(f"Citation {index}: Unmatched parentheses")
        
        # Check for excessive repetition (potential spam/injection)
        if re.search(r'(.)\1{10,}', citation):  # Same character repeated 11+ times
            issues.append(f"Citation {index}: Excessive character repetition")
        
        # Check for binary data indicators
        if '\x00' in citation or any(ord(c) > 127 and ord(c) < 160 for c in citation):
            issues.append(f"Citation {index}: Contains binary or control characters")
        
        return len(issues) == 0, issues
    
    def _sanitize_html(self, citation: str) -> str:
        """
        Sanitize HTML content from citation.
        
        Args:
            citation: Citation string to sanitize
            
        Returns:
            Sanitized citation string
        """
        # HTML escape dangerous characters
        citation = html.escape(citation)
        
        # Remove HTML tags completely
        citation = self.security_patterns["html_tags"].sub('', citation)
        
        # Decode safe HTML entities
        citation = html.unescape(citation)
        
        return citation
    
    def _final_sanitization(self, citation: str) -> str:
        """
        Final sanitization pass.
        
        Args:
            citation: Citation string to sanitize
            
        Returns:
            Final sanitized citation string
        """
        # Remove null bytes
        citation = citation.replace('\x00', '')
        
        # Normalize whitespace
        citation = re.sub(r'\s+', ' ', citation)
        
        # Remove leading/trailing whitespace
        citation = citation.strip()
        
        # Remove control characters except tab and newline
        citation = ''.join(char for char in citation if ord(char) >= 32 or char in '\t\n')
        
        return citation
    
    def get_validation_summary(self, result: InputValidationResult) -> Dict[str, Any]:
        """
        Get a summary of validation results.
        
        Args:
            result: InputValidationResult to summarize
            
        Returns:
            Dictionary with validation summary
        """
        return {
            "validation_passed": result.is_valid,
            "strictness_level": result.strictness_level.value,
            "statistics": {
                "original_count": result.original_count,
                "processed_count": result.processed_count,
                "filtered_count": result.filtered_count,
                "success_rate": (result.processed_count / result.original_count) if result.original_count > 0 else 0.0
            },
            "issue_summary": {
                "total_errors": len(result.errors),
                "security_issues": len(result.security_issues),
                "encoding_issues": len(result.encoding_issues),
                "content_issues": len(result.content_issues),
                "warnings": len(result.warnings)
            },
            "recommendations": self._generate_recommendations(result)
        }
    
    def _generate_recommendations(self, result: InputValidationResult) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if result.security_issues:
            recommendations.append("Review citations for potential security vulnerabilities")
        
        if result.encoding_issues:
            recommendations.append("Check source encoding and character set compatibility")
        
        if result.filtered_count > result.processed_count * 0.5:
            recommendations.append("Consider using a more permissive validation level")
        
        if result.content_issues:
            recommendations.append("Verify citation formatting follows academic standards")
        
        if not result.is_valid and self.strictness == ValidationStrictness.PARANOID:
            recommendations.append("Try using a less strict validation level for better compatibility")
        
        return recommendations