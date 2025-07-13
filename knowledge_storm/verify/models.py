"""
VERIFY system data models.

Core data structures for fact verification, research patterns, and verification results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class Claim:
    """A factual claim that needs verification."""
    text: str
    context: str  # Surrounding text for context
    source_cited: Optional[str] = None
    confidence: float = 0.0
    verification_status: str = "unverified"  # unverified, verified, disputed, unsupported
    evidence: List[str] = field(default_factory=list)
    location: Optional[Tuple[int, int]] = None  # (paragraph, sentence) indices


@dataclass
class VerificationResult:
    """Result of fact verification."""
    claim: Claim
    is_supported: bool
    confidence: float
    supporting_sources: List[str]
    suggested_fix: Optional[str] = None
    severity: str = "info"  # info, warning, error


@dataclass
class ResearchPattern:
    """Learned pattern from successful research."""
    pattern_type: str  # structure, source_quality, claim_density, etc.
    domain: str
    success_metric: float
    pattern_data: Dict[str, Any]
    usage_count: int = 0
    last_used: Optional[datetime] = None