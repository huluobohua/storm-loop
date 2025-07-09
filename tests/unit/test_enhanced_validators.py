"""
Unit tests for enhanced validators.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from academic_validation_framework.config import ValidationConfig
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.enhanced_citation_validator import EnhancedCitationValidator
from academic_validation_framework.validators.bias_detector import BiasDetector
from academic_validation_framework.validators.validation_manager import ValidationManager
from academic_validation_framework.validators.config_validator import ConfigValidator
from academic_validation_framework.models import ResearchData, ValidationResult, ValidationStatus
from academic_validation_framework.exceptions import DataValidationError, ConfigurationError


class TestConfigValidator:
    """Test the configuration validator."""
    
    def test_valid_config(self):
        """Test validation of a valid configuration."""
        config = ValidationConfig()
        result = ConfigValidator.validate_config(config)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_thresholds(self):
        """Test validation with invalid threshold values."""
        config = ValidationConfig(
            citation_accuracy_threshold=1.5,  # Invalid: > 1.0
            prisma_compliance_threshold=-0.1,  # Invalid: < 0.0
            bias_detection_threshold=0.3  # Warning: low value
        )
        
        result = ConfigValidator.validate_config(config)
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert any("citation_accuracy_threshold" in error for error in result.errors)
        assert any("prisma_compliance_threshold" in error for error in result.errors)
        assert any("bias_detection_threshold" in warning for warning in result.warnings)
    
    def test_fix_config(self):
        """Test automatic config fixing."""
        config = ValidationConfig(
            citation_accuracy_threshold=1.5,
            timeout_seconds=-10,
            retry_attempts=-1
        )
        
        fixed_config = ConfigValidator.validate_and_fix_config(config)
        
        assert fixed_config.citation_accuracy_threshold == 1.0
        assert fixed_config.timeout_seconds == 30
        assert fixed_config.retry_attempts == 3


class TestEnhancedPRISMAValidator:
    """Test the enhanced PRISMA validator."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return ValidationConfig(
            prisma_compliance_threshold=0.8,
            timeout_seconds=30
        )
    
    @pytest.fixture
    def validator(self, config):
        """Provide PRISMA validator instance."""
        return EnhancedPRISMAValidator(config)
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample research data."""
        return ResearchData(
            title="Systematic Review of Machine Learning in Healthcare",
            abstract="This systematic review examines machine learning applications in healthcare. Protocol was registered in PROSPERO (CRD12345). We searched PubMed, EMBASE, and Cochrane databases. Study selection followed PRISMA guidelines with independent screening.",
            citations=[
                "Smith, J. A. (2023). ML in diagnosis. Journal of Medical AI, 15(3), 45-67."
            ],
            authors=["Dr. Jane Smith", "Dr. John Doe"],
            publication_year=2024,
            journal="Healthcare Reviews"
        )
    
    def test_validator_properties(self, validator):
        """Test validator properties."""
        assert validator.name == "enhanced_prisma"
        assert ResearchData in validator.supported_data_types
    
    @pytest.mark.asyncio
    async def test_valid_prisma_compliance(self, validator, sample_data):
        """Test validation of PRISMA-compliant data."""
        with patch.object(validator, 'constants') as mock_constants:
            mock_constants.CHECKPOINTS = ["protocol_registration", "search_strategy"]
            
            result = await validator.validate(sample_data)
            
            assert isinstance(result, ValidationResult)
            assert result.validator_name == "enhanced_prisma"
            assert result.score > 0.0
            assert "checkpoints" in result.details
    
    @pytest.mark.asyncio
    async def test_protocol_registration_detection(self, validator, sample_data):
        """Test protocol registration detection."""
        with patch.object(validator, 'constants') as mock_constants:
            mock_constants.CHECKPOINTS = ["protocol_registration"]
            
            result = await validator.validate(sample_data)
            
            # Should detect PROSPERO registration
            protocol_checkpoint = next(
                (cp for cp in result.details["checkpoints"] 
                 if cp["name"] == "protocol_registration"),
                None
            )
            assert protocol_checkpoint is not None
            assert protocol_checkpoint["passed"] is True
    
    @pytest.mark.asyncio
    async def test_search_strategy_detection(self, validator, sample_data):
        """Test search strategy detection."""
        with patch.object(validator, 'constants') as mock_constants:
            mock_constants.CHECKPOINTS = ["search_strategy"]
            
            result = await validator.validate(sample_data)
            
            # Should detect database mentions
            search_checkpoint = next(
                (cp for cp in result.details["checkpoints"] 
                 if cp["name"] == "search_strategy"),
                None
            )
            assert search_checkpoint is not None
            assert search_checkpoint["passed"] is True
    
    @pytest.mark.asyncio
    async def test_missing_protocol_registration(self, validator):
        """Test detection of missing protocol registration."""
        data = ResearchData(
            title="Review without protocol",
            abstract="This review examines topics without mentioning protocol registration.",
            citations=["Smith, J. (2023). Article. Journal, 1, 1-10."],
            authors=["Author"],
            publication_year=2024
        )
        
        with patch.object(validator, 'constants') as mock_constants:
            mock_constants.CHECKPOINTS = ["protocol_registration"]
            
            result = await validator.validate(data)
            
            protocol_checkpoint = next(
                (cp for cp in result.details["checkpoints"] 
                 if cp["name"] == "protocol_registration"),
                None
            )
            assert protocol_checkpoint is not None
            assert protocol_checkpoint["passed"] is False
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, validator):
        """Test error handling in validation."""
        invalid_data = "not_research_data"
        
        with patch('academic_validation_framework.utils.input_validation.InputValidator.validate_research_data') as mock_validate:
            mock_validate.side_effect = Exception("Validation failed")
            
            result = await validator.validate(invalid_data)
            
            assert result.status == ValidationStatus.ERROR
            assert result.score == 0.0
            assert "error" in result.details


class TestEnhancedCitationValidator:
    """Test the enhanced citation validator."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return ValidationConfig(
            citation_accuracy_threshold=0.9,
            citation_formats=["APA", "MLA"]
        )
    
    @pytest.fixture
    def validator(self, config):
        """Provide citation validator instance."""
        return EnhancedCitationValidator(config)
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample research data with citations."""
        return ResearchData(
            title="Citation Analysis Study",
            abstract="This study analyzes citation patterns.",
            citations=[
                "Smith, J. A. (2023). Citation patterns. Journal of Research, 15(3), 45-67.",
                "Doe, J. (2022). Research methods. Academic Press."
            ],
            authors=["Author"],
            publication_year=2024
        )
    
    def test_validator_properties(self, validator):
        """Test validator properties."""
        assert validator.name == "enhanced_citation"
        assert ResearchData in validator.supported_data_types
    
    @pytest.mark.asyncio
    async def test_citation_validation(self, validator, sample_data):
        """Test citation format validation."""
        with patch.object(validator, '_validate_format') as mock_validate:
            mock_validate.return_value = Mock(
                format_name="APA",
                is_valid=True,
                confidence=0.95,
                errors=[]
            )
            
            result = await validator.validate(sample_data)
            
            assert isinstance(result, ValidationResult)
            assert result.validator_name == "enhanced_citation"
            assert result.score > 0.0
            assert "format_results" in result.details
    
    @pytest.mark.asyncio
    async def test_no_citations_error(self, validator):
        """Test handling of data with no citations."""
        data = ResearchData(
            title="No Citations Study",
            abstract="This study has no citations.",
            citations=[],
            authors=["Author"],
            publication_year=2024
        )
        
        result = await validator.validate(data)
        
        assert result.validator_name == "enhanced_citation"
        assert not result.passed
        assert result.score == 0.0
        assert "error" in result.details
    
    @pytest.mark.asyncio
    async def test_format_validation_logic(self, validator, sample_data):
        """Test specific format validation logic."""
        # Test APA format validation
        citations = ["Smith, J. A. (2023). Title. Journal, 15(3), 45-67."]
        
        result = await validator._validate_format("APA", citations)
        
        assert result.format_name == "APA"
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0


class TestBiasDetector:
    """Test the bias detector."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return ValidationConfig(
            bias_detection_threshold=0.8,
            bias_types_to_check=["confirmation_bias", "publication_bias"]
        )
    
    @pytest.fixture
    def validator(self, config):
        """Provide bias detector instance."""
        return BiasDetector(config)
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample research data."""
        return ResearchData(
            title="Bias Detection Study",
            abstract="This study examines potential bias in research with funding from pharmaceutical companies.",
            citations=[
                "Positive, A. (2023). Positive results. Journal, 1, 1-10.",
                "Negative, B. (2023). Negative results. Journal, 2, 11-20."
            ],
            authors=["Researcher A", "Researcher B"],
            publication_year=2024
        )
    
    def test_validator_properties(self, validator):
        """Test validator properties."""
        assert validator.name == "bias_detector"
        assert ResearchData in validator.supported_data_types
    
    def test_strategy_initialization(self, validator):
        """Test that strategies are properly initialized."""
        assert "confirmation_bias" in validator.strategies
        assert "publication_bias" in validator.strategies
        # Should not include strategies not in config
        assert "selection_bias" not in validator.strategies
    
    @pytest.mark.asyncio
    async def test_bias_detection(self, validator, sample_data):
        """Test bias detection logic."""
        with patch.object(validator, '_run_bias_detection') as mock_detection:
            mock_detection.return_value = [
                Mock(bias_type="confirmation_bias", detected=False, confidence=0.3),
                Mock(bias_type="publication_bias", detected=True, confidence=0.9)
            ]
            
            result = await validator.validate(sample_data)
            
            assert isinstance(result, ValidationResult)
            assert result.validator_name == "bias_detector"
            assert "bias_checks" in result.details
            assert result.details["total_bias_types_checked"] == 2
    
    @pytest.mark.asyncio
    async def test_funding_bias_detection(self, validator, sample_data):
        """Test funding bias detection."""
        # Add funding bias to config
        validator.config.bias_types_to_check = ["funding_bias"]
        validator.strategies = {"funding_bias": Mock()}
        
        with patch.object(validator, '_run_bias_detection') as mock_detection:
            mock_detection.return_value = [
                Mock(bias_type="funding_bias", detected=True, confidence=0.85)
            ]
            
            result = await validator.validate(sample_data)
            
            funding_check = next(
                (bc for bc in result.details["bias_checks"] 
                 if bc["type"] == "funding_bias"),
                None
            )
            assert funding_check is not None
            assert funding_check["detected"] is True


class TestValidationManager:
    """Test the validation manager."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return ValidationConfig(
            timeout_seconds=5,
            retry_attempts=2,
            track_performance_metrics=True
        )
    
    @pytest.fixture
    def manager(self, config):
        """Provide validation manager instance."""
        return ValidationManager(config)
    
    @pytest.fixture
    def mock_validator(self):
        """Provide mock validator."""
        validator = Mock()
        validator.name = "test_validator"
        validator.supported_data_types = [ResearchData]
        validator.validate.return_value = ValidationResult(
            validator_name="test_validator",
            test_name="test",
            status=ValidationStatus.PASSED,
            score=0.95,
            details={"test": "data"}
        )
        return validator
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample data."""
        return ResearchData(
            title="Test Study",
            abstract="Test abstract",
            citations=["Test citation"],
            authors=["Test Author"],
            publication_year=2024
        )
    
    @pytest.mark.asyncio
    async def test_successful_validation(self, manager, mock_validator, sample_data):
        """Test successful validation execution."""
        result = await manager.execute_validation(mock_validator, sample_data)
        
        assert isinstance(result, ValidationResult)
        assert result.validator_name == "test_validator"
        assert result.score == 0.95
        assert hasattr(result, 'execution_time_seconds')
        
        # Check metrics were recorded
        assert len(manager.metrics) == 1
        metric = list(manager.metrics.values())[0]
        assert metric.validator_name == "test_validator"
        assert metric.success is True
    
    @pytest.mark.asyncio
    async def test_unsupported_data_type(self, manager, mock_validator):
        """Test handling of unsupported data type."""
        mock_validator.supported_data_types = [str]
        
        result = await manager.execute_validation(mock_validator, {"invalid": "data"})
        
        assert result.status == ValidationStatus.ERROR
        assert result.score == 0.0
        assert "error_info" in result.details
        assert "unsupported_data_type" in str(result.details)
    
    @pytest.mark.asyncio
    async def test_validation_timeout(self, manager, mock_validator, sample_data):
        """Test validation timeout handling."""
        async def timeout_validation(data):
            await asyncio.sleep(10)  # Longer than timeout
            return ValidationResult(
                validator_name="test_validator",
                test_name="test",
                status=ValidationStatus.PASSED,
                score=0.95,
                details={}
            )
        
        mock_validator.validate = timeout_validation
        
        result = await manager.execute_validation(mock_validator, sample_data)
        
        assert result.status == ValidationStatus.ERROR
        assert "timeout" in str(result.details).lower()
    
    @pytest.mark.asyncio
    async def test_validation_retry(self, manager, mock_validator, sample_data):
        """Test validation retry logic."""
        call_count = 0
        
        async def failing_validation(data):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise Exception("Temporary failure")
            return ValidationResult(
                validator_name="test_validator",
                test_name="test",
                status=ValidationStatus.PASSED,
                score=0.95,
                details={}
            )
        
        mock_validator.validate = failing_validation
        
        result = await manager.execute_validation(mock_validator, sample_data)
        
        # Should succeed on third attempt
        assert result.status == ValidationStatus.PASSED
        assert call_count == 3
    
    def test_performance_summary(self, manager):
        """Test performance summary generation."""
        # Add some test metrics
        manager.metrics["test1"] = Mock(
            validator_name="validator1",
            success=True,
            execution_time=1.0
        )
        manager.metrics["test2"] = Mock(
            validator_name="validator2",
            success=False,
            execution_time=2.0
        )
        
        summary = manager.get_performance_summary()
        
        assert summary["total_validations"] == 2
        assert summary["successful_validations"] == 1
        assert summary["failed_validations"] == 1
        assert summary["success_rate"] == 0.5
        assert summary["average_execution_time"] == 1.5
        assert "validator1" in summary["validator_usage"]
        assert "validator2" in summary["validator_usage"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])