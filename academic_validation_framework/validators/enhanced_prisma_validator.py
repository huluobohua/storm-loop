from typing import Dict, List, Any
from dataclasses import dataclass
from academic_validation_framework.interfaces_v2 import ValidatorProtocol
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.config import ValidationConfig

@dataclass
class PRISMACheckpoint:
    """Individual PRISMA compliance checkpoint."""
    name: str
    description: str
    passed: bool
    score: float
    details: str

class EnhancedPRISMAValidator:
    """PRISMA systematic review compliance validator."""

    def __init__(self, config: 'ValidationConfig'):
        self.config = config
        self.checkpoints = [
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

    async def validate(self, data: ResearchData) -> ValidationResult:
        """Validate PRISMA compliance."""
        checkpoints = []
        total_score = 0.0

        for checkpoint_name in self.checkpoints:
            checkpoint = await self._validate_checkpoint(checkpoint_name, data)
            checkpoints.append(checkpoint)
            total_score += checkpoint.score

        overall_score = total_score / len(self.checkpoints)
        passed = overall_score >= self.config.prisma_compliance_threshold

        return ValidationResult(
            validator_name="enhanced_prisma",
            test_name="prisma_compliance_test",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            score=overall_score,
            details={
                "checkpoints": [
                    {
                        "name": cp.name,
                        "passed": cp.passed,
                        "score": cp.score,
                        "details": cp.details
                    }
                    for cp in checkpoints
                ],
                "total_checkpoints": len(checkpoints),
                "passed_checkpoints": sum(1 for cp in checkpoints if cp.passed)
            }
        )

    async def _validate_checkpoint(self, checkpoint_name: str, data: ResearchData) -> PRISMACheckpoint:
        """Validate individual PRISMA checkpoint."""
        # Protocol registration check
        if checkpoint_name == "protocol_registration":
            has_protocol = any(
                keyword in data.abstract.lower() if data.abstract else False
                for keyword in ["protocol", "prospero", "registration"]
            )
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Protocol was registered before study began",
                passed=has_protocol,
                score=1.0 if has_protocol else 0.0,
                details=f"Protocol registration {'found' if has_protocol else 'not found'} in abstract"
            )

        # Search strategy check
        elif checkpoint_name == "search_strategy":
            has_search_strategy = any(
                keyword in data.abstract.lower() if data.abstract else False
                for keyword in ["search", "database", "pubmed", "embase", "cochrane"]
            )
            return PRISMACheckpoint(
                name=checkpoint_name,
                description="Search strategy is documented",
                passed=has_search_strategy,
                score=1.0 if has_search_strategy else 0.0,
                details=f"Search strategy {'documented' if has_search_strategy else 'not documented'}"
            )

        # Default implementation for other checkpoints
        else:
            return PRISMACheckpoint(
                name=checkpoint_name,
                description=f"Check for {checkpoint_name.replace('_', ' ')}",
                passed=True,  # Placeholder - implement real logic
                score=0.8,    # Placeholder score
                details=f"Placeholder validation for {checkpoint_name}"
            )
