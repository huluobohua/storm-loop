"""
PRISMA checkpoint validation strategies using Strategy pattern.
"""
from abc import ABC, abstractmethod
from academic_validation_framework.validators.enhanced_prisma_validator import PRISMACheckpoint
from academic_validation_framework.models import ResearchData


class PRISMACheckpointStrategy(ABC):
    """Abstract base class for PRISMA checkpoint validation strategies."""

    @abstractmethod
    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        """Validate specific PRISMA checkpoint."""
        pass


class ProtocolRegistrationStrategy(PRISMACheckpointStrategy):
    """Strategy for validating protocol registration."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        protocol_keywords = ["protocol", "prospero", "registration", "registered", "crd", "protocol number"]
        has_protocol = any(keyword in combined_text for keyword in protocol_keywords)
        score = 1.0 if has_protocol else 0.0

        return PRISMACheckpoint(
            name="protocol_registration",
            description="Protocol was registered before study began (PROSPERO, etc.)",
            passed=has_protocol,
            score=score,
            details=f"Protocol registration {'found' if has_protocol else 'not found'} in title/abstract"
        )


class SearchStrategyStrategy(PRISMACheckpointStrategy):
    """Strategy for validating search strategy."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        search_keywords = ["search", "database", "pubmed", "embase", "cochrane", "medline", "scopus", "web of science"]
        has_search = any(keyword in combined_text for keyword in search_keywords)
        score = 1.0 if has_search else 0.0

        return PRISMACheckpoint(
            name="search_strategy",
            description="Search strategy and databases are documented",
            passed=has_search,
            score=score,
            details=f"Search strategy {'documented' if has_search else 'not documented'} in abstract"
        )


class EligibilityCriteriaStrategy(PRISMACheckpointStrategy):
    """Strategy for validating eligibility criteria."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        criteria_keywords = ["inclusion", "exclusion", "criteria", "eligible", "eligibility", "included", "excluded"]
        has_criteria = any(keyword in combined_text for keyword in criteria_keywords)
        score = 1.0 if has_criteria else 0.0

        return PRISMACheckpoint(
            name="eligibility_criteria",
            description="Study selection criteria are clearly defined",
            passed=has_criteria,
            score=score,
            details=f"Eligibility criteria {'specified' if has_criteria else 'not specified'}"
        )


class InformationSourcesStrategy(PRISMACheckpointStrategy):
    """Strategy for validating information sources."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        source_keywords = ["database", "source", "electronic", "grey literature", "reference", "hand search"]
        has_sources = any(keyword in combined_text for keyword in source_keywords)
        score = 1.0 if has_sources else 0.0

        return PRISMACheckpoint(
            name="information_sources",
            description="Information sources are documented",
            passed=has_sources,
            score=score,
            details=f"Information sources {'documented' if has_sources else 'not documented'}"
        )


class StudySelectionStrategy(PRISMACheckpointStrategy):
    """Strategy for validating study selection process."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        selection_keywords = ["screening", "selection", "reviewer", "independent", "duplicate", "agreement"]
        has_selection = any(keyword in combined_text for keyword in selection_keywords)
        score = 1.0 if has_selection else 0.0

        return PRISMACheckpoint(
            name="study_selection",
            description="Study selection process is described",
            passed=has_selection,
            score=score,
            details=f"Study selection process {'described' if has_selection else 'not described'}"
        )


class DataExtractionStrategy(PRISMACheckpointStrategy):
    """Strategy for validating data extraction methods."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        extraction_keywords = ["data extraction", "extracted", "extraction form", "standardized", "pilot"]
        has_extraction = any(keyword in combined_text for keyword in extraction_keywords)
        score = 1.0 if has_extraction else 0.0

        return PRISMACheckpoint(
            name="data_extraction",
            description="Data extraction methods are described",
            passed=has_extraction,
            score=score,
            details=f"Data extraction {'described' if has_extraction else 'not described'}"
        )


class RiskOfBiasStrategy(PRISMACheckpointStrategy):
    """Strategy for validating risk of bias assessment."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        bias_keywords = ["risk of bias", "quality assessment", "cochrane", "rob", "methodological quality", "bias assessment"]
        has_bias_assessment = any(keyword in combined_text for keyword in bias_keywords)
        score = 1.0 if has_bias_assessment else 0.0

        return PRISMACheckpoint(
            name="risk_of_bias",
            description="Risk of bias assessment is performed",
            passed=has_bias_assessment,
            score=score,
            details=f"Risk of bias assessment {'performed' if has_bias_assessment else 'not performed'}"
        )


class SynthesisMethodsStrategy(PRISMACheckpointStrategy):
    """Strategy for validating synthesis methods."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        synthesis_keywords = ["meta-analysis", "synthesis", "pooled", "statistical", "heterogeneity", "fixed effect", "random effect"]
        has_synthesis = any(keyword in combined_text for keyword in synthesis_keywords)
        score = 1.0 if has_synthesis else 0.0

        return PRISMACheckpoint(
            name="synthesis_methods",
            description="Data synthesis methods are described",
            passed=has_synthesis,
            score=score,
            details=f"Synthesis methods {'described' if has_synthesis else 'not described'}"
        )


class ReportingBiasStrategy(PRISMACheckpointStrategy):
    """Strategy for validating reporting bias assessment."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        reporting_keywords = ["publication bias", "funnel plot", "egger", "begg", "reporting bias", "selective reporting"]
        has_reporting_check = any(keyword in combined_text for keyword in reporting_keywords)
        score = 1.0 if has_reporting_check else 0.5  # Partial score as it's often not mentioned in abstract

        return PRISMACheckpoint(
            name="reporting_bias",
            description="Reporting bias assessment is addressed",
            passed=has_reporting_check,
            score=score,
            details=f"Reporting bias {'assessed' if has_reporting_check else 'not explicitly mentioned'}"
        )


class FlowDiagramStrategy(PRISMACheckpointStrategy):
    """Strategy for validating flow diagram mention."""

    def validate(self, data: ResearchData) -> PRISMACheckpoint:
        abstract_text = (data.abstract or "").lower()
        title_text = (data.title or "").lower()
        combined_text = f"{title_text} {abstract_text}"

        flow_keywords = ["flow diagram", "flow chart", "prisma diagram", "selection flow", "study flow"]
        has_flow = any(keyword in combined_text for keyword in flow_keywords)
        score = 1.0 if has_flow else 0.2  # Low score as flow diagrams are rarely mentioned in abstracts

        return PRISMACheckpoint(
            name="flow_diagram",
            description="PRISMA flow diagram is included",
            passed=has_flow,
            score=score,
            details=f"Flow diagram {'mentioned' if has_flow else 'not mentioned in abstract'}"
        )