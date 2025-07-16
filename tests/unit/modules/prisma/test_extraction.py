"""
Unit tests for PRISMA data extraction functionality.
"""

import pytest
from knowledge_storm.modules.prisma.extraction import DataExtractionHelper
from knowledge_storm.modules.prisma.core import Paper, ExtractionTemplate


class TestDataExtractionHelper:
    """Test suite for DataExtractionHelper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extraction_helper = DataExtractionHelper()
    
    def create_test_paper(self, study_type="randomized_controlled_trial", 
                         sample_size=100, title="Test Study"):
        """Helper method to create test papers."""
        return Paper(
            id="test_paper_1",
            title=title,
            abstract=f"This is a {study_type} with {sample_size} participants",
            authors=["Test Author"],
            year=2023,
            journal="Test Journal",
            study_type=study_type,
            sample_size=sample_size
        )
    
    def test_initialization(self):
        """Test DataExtractionHelper initialization."""
        helper = DataExtractionHelper()
        assert helper is not None
        assert hasattr(helper, 'create_extraction_template')
        assert hasattr(helper, 'extract_data_from_paper')
    
    def test_create_extraction_template_clinical_trial(self):
        """Test creating extraction template for clinical trials."""
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        
        assert isinstance(template, ExtractionTemplate)
        assert isinstance(template.fields, dict)
        assert isinstance(template.study_characteristics, list)
        assert isinstance(template.outcome_measures, list)
        assert isinstance(template.quality_indicators, list)
        
        # Check that clinical trial specific fields are present
        assert "sample_size" in template.fields
        assert "intervention" in template.fields
        assert "control_group" in template.fields
        assert "primary_outcome" in template.fields
        assert "randomization" in template.fields
        
        # Check field definitions
        for field_name, field_def in template.fields.items():
            assert "type" in field_def
            assert "description" in field_def
            assert "required" in field_def
            assert isinstance(field_def["required"], bool)
    
    def test_create_extraction_template_observational(self):
        """Test creating extraction template for observational studies."""
        template = DataExtractionHelper().create_extraction_template("observational")
        
        assert isinstance(template, ExtractionTemplate)
        
        # Check that observational study specific fields are present
        assert "study_design" in template.fields
        assert "population" in template.fields
        assert "exposure" in template.fields
        assert "outcome" in template.fields
        assert "confounders" in template.fields
        
        # Check study characteristics
        assert len(template.study_characteristics) > 0
        assert "study_design" in template.study_characteristics
        assert "setting" in template.study_characteristics
    
    def test_create_extraction_template_systematic_review(self):
        """Test creating extraction template for systematic reviews."""
        template = DataExtractionHelper().create_extraction_template("systematic_review")
        
        assert isinstance(template, ExtractionTemplate)
        
        # Check that systematic review specific fields are present
        assert "search_strategy" in template.fields
        assert "databases_searched" in template.fields
        assert "inclusion_criteria" in template.fields
        assert "exclusion_criteria" in template.fields
        assert "studies_included" in template.fields
        assert "quality_assessment" in template.fields
    
    def test_create_extraction_template_invalid_type(self):
        """Test creating extraction template with invalid study type."""
        with pytest.raises(ValueError, match="Unsupported study type"):
            DataExtractionHelper().create_extraction_template("invalid_study_type")
    
    def test_extract_data_from_paper_clinical_trial(self):
        """Test extracting data from clinical trial paper."""
        paper = self.create_test_paper(
            study_type="randomized_controlled_trial",
            sample_size=200,
            title="RCT of Drug X vs Placebo"
        )
        
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        assert isinstance(extracted_data, dict)
        
        # Check that basic information is extracted
        assert "paper_id" in extracted_data
        assert extracted_data["paper_id"] == paper.id
        assert "title" in extracted_data
        assert extracted_data["title"] == paper.title
        assert "authors" in extracted_data
        assert extracted_data["authors"] == paper.authors
        assert "year" in extracted_data
        assert extracted_data["year"] == paper.year
        assert "journal" in extracted_data
        assert extracted_data["journal"] == paper.journal
        
        # Check that study-specific data is extracted
        assert "sample_size" in extracted_data
        assert extracted_data["sample_size"] == paper.sample_size
        assert "study_type" in extracted_data
        assert extracted_data["study_type"] == paper.study_type
    
    def test_extract_data_from_paper_observational(self):
        """Test extracting data from observational study paper."""
        paper = self.create_test_paper(
            study_type="cohort_study",
            sample_size=1000,
            title="Cohort Study of Risk Factors"
        )
        
        template = DataExtractionHelper().create_extraction_template("observational")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        assert isinstance(extracted_data, dict)
        assert "paper_id" in extracted_data
        assert extracted_data["paper_id"] == paper.id
        assert "study_type" in extracted_data
        assert extracted_data["study_type"] == paper.study_type
        assert "sample_size" in extracted_data
        assert extracted_data["sample_size"] == paper.sample_size
    
    def test_extract_data_from_paper_with_missing_fields(self):
        """Test extracting data from paper with missing optional fields."""
        paper = Paper(
            id="minimal_paper",
            title="Minimal Paper",
            abstract="Minimal abstract",
            authors=["Author"],
            year=2023,
            journal="Journal"
            # Missing optional fields like study_type, sample_size, etc.
        )
        
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        assert isinstance(extracted_data, dict)
        assert "paper_id" in extracted_data
        assert extracted_data["paper_id"] == paper.id
        
        # Missing fields should be handled gracefully
        assert "sample_size" in extracted_data
        assert extracted_data["sample_size"] is None or extracted_data["sample_size"] == "Not specified"
    
    def test_extract_data_from_paper_abstract_parsing(self):
        """Test that data extraction attempts to parse abstract for missing info."""
        paper = Paper(
            id="abstract_paper",
            title="Study Title",
            abstract="This randomized controlled trial included 150 participants aged 18-65 years. The primary outcome was pain reduction measured on a 0-10 scale.",
            authors=["Author"],
            year=2023,
            journal="Journal"
        )
        
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        assert isinstance(extracted_data, dict)
        
        # Should attempt to extract information from abstract
        assert "abstract_analysis" in extracted_data
        abstract_analysis = extracted_data["abstract_analysis"]
        
        # Should identify key information from abstract
        assert "150" in str(abstract_analysis) or "sample_size" in str(abstract_analysis)
        assert "randomized" in str(abstract_analysis).lower()
        assert "pain" in str(abstract_analysis).lower()
    
    def test_template_field_validation(self):
        """Test that extraction templates have proper field validation."""
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        
        # All fields should have required validation info
        for field_name, field_def in template.fields.items():
            assert "type" in field_def
            assert field_def["type"] in ["str", "int", "float", "bool", "list", "dict"]
            assert "description" in field_def
            assert isinstance(field_def["description"], str)
            assert len(field_def["description"]) > 0
            assert "required" in field_def
            assert isinstance(field_def["required"], bool)
    
    def test_quality_indicators_included(self):
        """Test that quality indicators are included in templates."""
        clinical_template = DataExtractionHelper().create_extraction_template("clinical_trial")
        observational_template = DataExtractionHelper().create_extraction_template("observational")
        
        # Clinical trial quality indicators
        assert len(clinical_template.quality_indicators) > 0
        clinical_quality = clinical_template.quality_indicators
        assert "randomization_quality" in clinical_quality
        assert "blinding" in clinical_quality
        assert "allocation_concealment" in clinical_quality
        
        # Observational study quality indicators
        assert len(observational_template.quality_indicators) > 0
        observational_quality = observational_template.quality_indicators
        assert "selection_bias" in observational_quality
        assert "confounding_control" in observational_quality
        assert "outcome_measurement" in observational_quality
    
    def test_outcome_measures_specific_to_study_type(self):
        """Test that outcome measures are appropriate for each study type."""
        clinical_template = DataExtractionHelper().create_extraction_template("clinical_trial")
        observational_template = DataExtractionHelper().create_extraction_template("observational")
        
        # Clinical trial outcome measures
        clinical_outcomes = clinical_template.outcome_measures
        assert "primary_outcome" in clinical_outcomes
        assert "secondary_outcomes" in clinical_outcomes
        assert "adverse_events" in clinical_outcomes
        
        # Observational study outcome measures
        observational_outcomes = observational_template.outcome_measures
        assert "primary_outcome" in observational_outcomes
        assert "secondary_outcomes" in observational_outcomes
        assert "effect_size" in observational_outcomes
    
    def test_extraction_data_completeness(self):
        """Test that extraction returns complete data structure."""
        paper = self.create_test_paper()
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        # Should have all required sections
        required_sections = ["basic_info", "study_characteristics", "methodology", "results"]
        for section in required_sections:
            assert section in extracted_data
            assert isinstance(extracted_data[section], dict)
        
        # Basic info should be populated
        basic_info = extracted_data["basic_info"]
        assert "paper_id" in basic_info
        assert "title" in basic_info
        assert "authors" in basic_info
        assert "year" in basic_info
        assert "journal" in basic_info
    
    def test_extraction_handles_none_values(self):
        """Test that extraction handles None values gracefully."""
        paper = Paper(
            id="test_paper",
            title="Test",
            abstract="Test abstract",
            authors=["Author"],
            year=2023,
            journal="Journal",
            doi=None,
            url=None,
            study_type=None,
            sample_size=None
        )
        
        template = DataExtractionHelper().create_extraction_template("clinical_trial")
        extracted_data = DataExtractionHelper().extract_data_from_paper(paper, template)
        
        # Should handle None values without crashing
        assert isinstance(extracted_data, dict)
        assert "paper_id" in extracted_data
        assert extracted_data["paper_id"] == paper.id


if __name__ == "__main__":
    pytest.main([__file__])