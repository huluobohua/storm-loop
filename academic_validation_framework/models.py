"""
Data models for Academic Validation Framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of a validation test."""
    
    validator_name: str
    test_name: str
    status: str  # "passed", "failed", "warning", "skipped"
    score: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: Optional[float] = None
    
    @property
    def passed(self) -> bool:
        return self.status == "passed"
    
    @property
    def failed(self) -> bool:
        return self.status == "failed"


@dataclass
class ValidationSession:
    """A complete validation session with all results."""
    
    session_id: str
    config: Optional[Any] = None  # Avoid circular import, use Any for config
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.failed)
    
    @property
    def total_count(self) -> int:
        return len(self.results)
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.passed_count / self.total_count