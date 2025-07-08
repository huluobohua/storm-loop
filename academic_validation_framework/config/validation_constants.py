"""
Centralized configuration constants for Academic Validation Framework.
All hard-coded values extracted into configurable constants.
"""
from typing import Dict, List, Any


class PRISMAConstants:
    """Constants for PRISMA validation."""
    
    # Checkpoint names
    CHECKPOINTS = [
        "protocol_registration",
        "search_strategy", 
        "eligibility_criteria",
        "information_sources",
        "study_selection",
        "data_extraction",
        "risk_of_bias",
        "synthesis_methods",
        "reporting_bias",
        "certainty_assessment",
        "study_characteristics",
        "results_synthesis"
    ]
    
    # Keyword mappings for each checkpoint
    CHECKPOINT_KEYWORDS = {
        "protocol_registration": [
            "protocol", "prospero", "registration", "registered", 
            "crd", "protocol number"
        ],
        "search_strategy": [
            "search", "searched", "search strategy", "systematic search",
            "database", "electronic", "comprehensive"
        ],
        "eligibility_criteria": [
            "eligibility", "inclusion", "exclusion", "criteria",
            "included", "excluded", "selection criteria"
        ],
        "information_sources": [
            "pubmed", "medline", "embase", "cochrane", "web of science",
            "scopus", "database", "searched", "information sources"
        ],
        "study_selection": [
            "selection", "screening", "reviewers", "independently",
            "duplicate", "removal", "screened"
        ],
        "data_extraction": [
            "data extraction", "extracted", "extraction form",
            "data collection", "reviewers extracted"
        ],
        "risk_of_bias": [
            "risk of bias", "bias assessment", "rob", "cochrane",
            "quality assessment", "methodological quality"
        ],
        "synthesis_methods": [
            "meta-analysis", "synthesis", "pooled", "random effects",
            "fixed effects", "heterogeneity", "i2", "forest plot"
        ],
        "reporting_bias": [
            "publication bias", "funnel plot", "egger", "begg",
            "reporting bias", "selective reporting"
        ],
        "certainty_assessment": [
            "grade", "certainty", "quality of evidence", "confidence",
            "evidence quality", "certainty assessment"
        ],
        "study_characteristics": [
            "characteristics", "baseline", "demographics", "participants",
            "study design", "sample size"
        ],
        "results_synthesis": [
            "results", "findings", "outcomes", "effect size",
            "confidence interval", "p-value", "statistical"
        ]
    }
    
    # Scoring thresholds
    MIN_KEYWORDS_FOR_PASS = 2
    PARTIAL_SCORE_THRESHOLD = 1
    
    # Score values
    FULL_SCORE = 1.0
    PARTIAL_SCORE = 0.5
    NO_SCORE = 0.0


class BiasDetectorConstants:
    """Constants for bias detection."""
    
    # Bias types
    BIAS_TYPES = [
        "confirmation_bias",
        "publication_bias",
        "selection_bias",
        "funding_bias",
        "reporting_bias"
    ]
    
    # Bias detection keywords
    BIAS_KEYWORDS = {
        "confirmation_bias": {
            "cherry_picking": ["only", "exclusively", "particularly", "specifically supports"],
            "min_citations": 10
        },
        "publication_bias": {
            "positive_terms": ["significant", "effective", "successful", "improved"],
            "positive_threshold": 3
        },
        "selection_bias": {
            "convenience_terms": ["convenience", "available", "volunteer", "self-selected", "convenience sample"],
            "randomization_terms": ["random", "randomized", "randomisation", "random assignment"],
            "exclusion_bias_terms": ["excluded healthy", "excluded low-risk", "excluded mild cases"]
        },
        "funding_bias": {
            "industry_terms": ["sponsored by", "funded by", "pharmaceutical", "company", "corporation", "industry funding"],
            "conflict_terms": ["conflict of interest", "competing interests", "disclosures", "financial relationships"],
            "promotional_terms": ["breakthrough", "revolutionary", "unprecedented", "superior", "optimal"],
            "promotional_threshold": 2,
            "funding_terms": ["funding", "grant", "support", "sponsored"]
        },
        "reporting_bias": {
            "outcome_terms": ["primary outcome", "secondary outcome", "endpoint", "measured"],
            "vague_terms": ["some", "several", "many", "various", "numerous", "certain"],
            "vague_threshold": 3,
            "significance_terms": ["significant", "p <", "p<", "statistically significant"],
            "non_sig_terms": ["non-significant", "not significant", "no difference", "no effect"],
            "post_hoc_terms": ["post-hoc", "post hoc", "exploratory", "unplanned analysis"],
            "effect_size_terms": ["effect size", "cohen's d", "odds ratio", "confidence interval", "95% ci"]
        }
    }
    
    # Confidence calculation factors
    CONFIDENCE_FACTORS = {
        "confirmation_bias": 3.0,  # Max indicators for normalization
        "selection_bias": 3.0,
        "funding_bias": 3.0,
        "reporting_bias": 3.0
    }
    
    # Detection thresholds
    DETECTION_THRESHOLDS = {
        "confirmation_bias": 0.5,
        "publication_bias": 0.0,  # Any evidence triggers
        "selection_bias": 0.3,
        "funding_bias": 0.4,
        "reporting_bias": 0.3
    }
    
    # Partial indicator weights
    PARTIAL_WEIGHTS = {
        "funding_bias_missing_disclosure": 0.5,
        "reporting_bias_post_hoc": 0.5,
        "reporting_bias_missing_effect_size": 0.5
    }


class CitationFormatConstants:
    """Constants for citation format validation."""
    
    # Cache settings
    CACHE_SIZE = 100
    CACHE_TTL_SECONDS = 3600  # 1 hour
    
    # Auto-detection settings
    AUTO_DETECTION_MIN_CITATIONS = 3
    AUTO_DETECTION_MIN_CONFIDENCE = 0.5
    
    # Format priorities (higher = preferred)
    FORMAT_PRIORITIES = {
        "apa": 90,
        "mla": 80,
        "chicago": 70,
        "ieee": 70,
        "harvard": 60,
        "vancouver": 50,
        "ama": 50
    }
    
    # Validation thresholds
    MIN_VALID_CITATIONS_RATIO = 0.7  # 70% must be valid
    HIGH_CONFIDENCE_THRESHOLD = 0.9
    MEDIUM_CONFIDENCE_THRESHOLD = 0.7
    LOW_CONFIDENCE_THRESHOLD = 0.5


class InputValidationConstants:
    """Constants for input validation."""
    
    # String length limits
    TITLE_MIN_LENGTH = 3
    TITLE_MAX_LENGTH = 500
    ABSTRACT_MIN_LENGTH = 10
    ABSTRACT_MAX_LENGTH = 50000
    CITATION_MAX_LENGTH = 1000
    MAX_CITATIONS = 1000
    
    # Year validation
    MIN_PUBLICATION_YEAR = 1900
    MAX_PUBLICATION_YEAR = 2100
    
    # Memory limits
    MAX_STRING_LENGTH = 100000  # 100KB
    MAX_CACHE_MEMORY_MB = 100
    
    # Sanitization
    NULL_BYTE = '\x00'


class ScoringConstants:
    """Constants for scoring systems."""
    
    # Score ranges
    EXCELLENT_THRESHOLD = 0.9
    GOOD_THRESHOLD = 0.75
    FAIR_THRESHOLD = 0.6
    POOR_THRESHOLD = 0.4
    
    # Score labels
    SCORE_LABELS = {
        (0.9, 1.0): "EXCELLENT",
        (0.75, 0.9): "GOOD", 
        (0.6, 0.75): "FAIR",
        (0.4, 0.6): "POOR",
        (0.0, 0.4): "VERY POOR"
    }
    
    # Weight factors for combined scoring
    PRISMA_WEIGHT = 0.5
    BIAS_WEIGHT = 0.5
    
    # Nuanced scoring factors
    SCORE_DECAY_FACTOR = 0.1  # For partial matches
    CONFIDENCE_MULTIPLIER = 1.0  # For high-confidence detections


class PerformanceConstants:
    """Constants for performance optimization."""
    
    # Timeouts (milliseconds)
    VALIDATION_TIMEOUT_MS = 5000
    REGEX_COMPILE_TIMEOUT_MS = 100
    
    # Batch processing
    BATCH_SIZE = 100
    MAX_CONCURRENT_VALIDATIONS = 10
    
    # Memory management
    GC_THRESHOLD_MB = 500
    CACHE_CLEANUP_INTERVAL_SECONDS = 3600
    
    # Resource limits
    MAX_STATISTICS_ENTRIES = 10000  # Maximum statistics records
    MAX_ERROR_PATTERNS = 1000       # Maximum error pattern records
    STATISTICS_CLEANUP_THRESHOLD = 5000  # Cleanup when this many entries reached


# Consolidated configuration class
class ValidationConstants:
    """Main configuration constants container."""
    
    PRISMA = PRISMAConstants()
    BIAS = BiasDetectorConstants()
    CITATION = CitationFormatConstants()
    INPUT = InputValidationConstants()
    SCORING = ScoringConstants()
    PERFORMANCE = PerformanceConstants()
    
    # Global settings
    DEBUG_MODE = False
    LOG_LEVEL = "INFO"
    VERSION = "2.0.0"