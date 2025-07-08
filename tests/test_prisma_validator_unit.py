"""
Unit tests for EnhancedPRISMAValidator that test actual implementation.
"""
import pytest
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.models import ResearchData, ValidationStatus
from academic_validation_framework.config import ValidationConfig


class TestPRISMAValidatorUnit:
    """Unit tests for EnhancedPRISMAValidator that test real implementation."""

    @pytest.fixture
    def config(self):
        return ValidationConfig(prisma_threshold=0.7)

    @pytest.fixture
    def validator(self, config):
        return EnhancedPRISMAValidator(config)

    @pytest.mark.asyncio
    async def test_protocol_registration_detected(self, validator):
        """Test detection of protocol registration."""
        data = ResearchData(
            title="Systematic Review of Treatment Options",
            abstract="This systematic review was registered in PROSPERO (CRD42023123456) before data extraction began.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        # Check protocol registration checkpoint
        checkpoints = result.details["prisma_checkpoints"]
        protocol_check = next(c for c in checkpoints if c["name"] == "protocol_registration")
        assert protocol_check["passed"] is True
        assert protocol_check["score"] == 1.0
        assert "found" in protocol_check["details"]

    @pytest.mark.asyncio
    async def test_search_strategy_detected(self, validator):
        """Test detection of search strategy documentation."""
        data = ResearchData(
            title="Meta-analysis of Clinical Trials",
            abstract="We searched PubMed, Embase, and Cochrane databases from inception to December 2023.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        search_check = next(c for c in checkpoints if c["name"] == "search_strategy")
        assert search_check["passed"] is True
        assert search_check["score"] == 1.0

    @pytest.mark.asyncio
    async def test_eligibility_criteria_detected(self, validator):
        """Test detection of eligibility criteria."""
        data = ResearchData(
            title="Systematic Review",
            abstract="Inclusion criteria were randomized controlled trials in adults. Exclusion criteria included observational studies.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        criteria_check = next(c for c in checkpoints if c["name"] == "eligibility_criteria")
        assert criteria_check["passed"] is True
        assert criteria_check["score"] == 1.0

    @pytest.mark.asyncio
    async def test_risk_of_bias_assessment(self, validator):
        """Test detection of risk of bias assessment."""
        data = ResearchData(
            title="Systematic Review with Quality Assessment",
            abstract="Risk of bias was assessed using the Cochrane risk of bias tool by two independent reviewers.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        rob_check = next(c for c in checkpoints if c["name"] == "risk_of_bias")
        assert rob_check["passed"] is True
        assert rob_check["score"] == 1.0

    @pytest.mark.asyncio
    async def test_synthesis_methods_detected(self, validator):
        """Test detection of synthesis methods."""
        data = ResearchData(
            title="Meta-analysis",
            abstract="Random effects meta-analysis was performed. Heterogeneity was assessed using I-squared statistics.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        synthesis_check = next(c for c in checkpoints if c["name"] == "synthesis_methods")
        assert synthesis_check["passed"] is True
        assert synthesis_check["score"] == 1.0

    @pytest.mark.asyncio
    async def test_complete_prisma_compliance(self, validator):
        """Test a study with full PRISMA compliance."""
        data = ResearchData(
            title="Comprehensive Systematic Review and Meta-analysis",
            abstract="""This systematic review was registered in PROSPERO. We searched PubMed, Embase, and Cochrane databases. 
            Inclusion criteria were RCTs in adults. Two reviewers independently screened studies and extracted data. 
            Risk of bias was assessed using Cochrane tool. Random effects meta-analysis was performed with assessment 
            of heterogeneity. Publication bias was evaluated using funnel plots.""",
            citations=["cite1"] * 20
        )

        result = await validator.validate(data)

        assert result.status == ValidationStatus.PASSED
        assert result.score >= 0.7
        
        # Most checkpoints should pass
        checkpoints = result.details["prisma_checkpoints"]
        passed_checkpoints = [c for c in checkpoints if c["passed"]]
        assert len(passed_checkpoints) >= 6

    @pytest.mark.asyncio
    async def test_minimal_prisma_compliance(self, validator):
        """Test a study with minimal PRISMA compliance."""
        data = ResearchData(
            title="Literature Review",
            abstract="We reviewed the literature on this topic and summarized the findings.",
            citations=["cite1"] * 5
        )

        result = await validator.validate(data)

        assert result.status == ValidationStatus.FAILED
        assert result.score < 0.7
        
        # Most checkpoints should fail
        checkpoints = result.details["prisma_checkpoints"]
        failed_checkpoints = [c for c in checkpoints if not c["passed"]]
        assert len(failed_checkpoints) >= 7

    @pytest.mark.asyncio
    async def test_flow_diagram_check(self, validator):
        """Test detection of flow diagram mention."""
        data = ResearchData(
            title="Systematic Review",
            abstract="The PRISMA flow diagram shows the study selection process from 1000 records to 25 included studies.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        flow_check = next(c for c in checkpoints if c["name"] == "flow_diagram")
        assert flow_check["passed"] is True

    @pytest.mark.asyncio
    async def test_error_handling_empty_data(self, validator):
        """Test error handling with empty data."""
        data = ResearchData(title="", abstract="", citations=[])

        result = await validator.validate(data)

        assert result.status == ValidationStatus.ERROR
        assert result.score == 0.0
        assert "error" in result.details

    @pytest.mark.asyncio
    async def test_none_abstract_handling(self, validator):
        """Test handling of None abstract."""
        data = ResearchData(
            title="Systematic Review",
            abstract=None,
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        # Should handle gracefully
        assert result.status in [ValidationStatus.FAILED, ValidationStatus.ERROR]
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_checkpoint_scoring_accuracy(self, validator):
        """Test that checkpoint scoring is accurate."""
        data = ResearchData(
            title="Partial PRISMA Compliance",
            abstract="We searched PubMed database. Inclusion criteria were defined.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        
        # Search strategy should pass
        search_check = next(c for c in checkpoints if c["name"] == "search_strategy")
        assert search_check["passed"] is True
        
        # Protocol registration should fail
        protocol_check = next(c for c in checkpoints if c["name"] == "protocol_registration")
        assert protocol_check["passed"] is False
        
        # Overall score should reflect partial compliance
        assert 0.0 < result.score < 1.0

    @pytest.mark.asyncio
    async def test_special_characters_in_abstract(self, validator):
        """Test handling of special characters."""
        data = ResearchData(
            title="Systematic Review",
            abstract="PROSPERO registration: CRD№123456. Search: PubMed® & Embase™",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        # Should detect protocol registration despite special characters
        checkpoints = result.details["prisma_checkpoints"]
        protocol_check = next(c for c in checkpoints if c["name"] == "protocol_registration")
        assert protocol_check["passed"] is True

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, validator):
        """Test that keyword detection is case insensitive."""
        data = ResearchData(
            title="SYSTEMATIC REVIEW",
            abstract="PROTOCOL WAS REGISTERED IN PROSPERO. SEARCHED PUBMED AND EMBASE.",
            citations=["cite1"] * 10
        )

        result = await validator.validate(data)

        checkpoints = result.details["prisma_checkpoints"]
        
        # Should detect keywords regardless of case
        protocol_check = next(c for c in checkpoints if c["name"] == "protocol_registration")
        assert protocol_check["passed"] is True
        
        search_check = next(c for c in checkpoints if c["name"] == "search_strategy")
        assert search_check["passed"] is True

    @pytest.mark.asyncio
    async def test_comprehensive_error_details(self, validator):
        """Test that error details are comprehensive."""
        data = ResearchData(
            title="Review",
            abstract="Brief review of topic.",
            citations=["cite1"]
        )

        result = await validator.validate(data)

        assert result.status == ValidationStatus.FAILED
        
        # Should have detailed information about what's missing
        assert "prisma_checkpoints" in result.details
        assert "total_checkpoints" in result.details
        assert "passed_checkpoints" in result.details
        assert "compliance_percentage" in result.details