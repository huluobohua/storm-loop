#!/usr/bin/env python3
"""Demonstration of real academic validation using built-in validators."""
import asyncio
from academic_validation_framework.core import AcademicValidationFramework
from academic_validation_framework.config import FrameworkConfig
from academic_validation_framework.validators.real_prisma_validator import RealPRISMAValidator
from academic_validation_framework.validators.real_citation_validator import RealCitationValidator
from academic_validation_framework.models import ResearchData

async def main() -> None:
    print("\U0001F393 Academic Validation Framework Demo")
    print("=" * 40)

    config = FrameworkConfig(console_logging=True)
    framework = AcademicValidationFramework(config)
    framework.register_validator(RealPRISMAValidator())
    framework.register_validator(RealCitationValidator())

    high_quality = ResearchData(
        title="Machine Learning in Medical Diagnosis: A Systematic Review",
        abstract=(
            "This systematic review examines ML applications in medical diagnosis. "
            "Protocol registered in PROSPERO."
        ),
        methodology="Search strategy used Boolean operators across PubMed, Cochrane, and Embase from 2010-2023. Independent reviewers performed standardized extraction.",
        search_terms=["machine learning", "medical diagnosis", "artificial intelligence", "clinical decision"],
        databases_used=["PubMed", "Cochrane", "Embase", "IEEE Xplore"],
        inclusion_criteria=["peer-reviewed", "English", "clinical studies"],
        exclusion_criteria=["case reports", "conference abstracts"],
        citations=[
            "Smith, J. A. (2023). Machine learning in healthcare. Journal of Medical AI, 15(3), 245-267.",
            'Johnson, Mary. "AI in Diagnosis." Medical Technology, vol. 12, no. 4, 2023, pp. 100-115.',
            "Some paper by someone about AI"
        ]
    )

    poor_quality = ResearchData(
        title="Some Review",
        abstract="We looked at some stuff.",
        methodology="We searched Google Scholar.",
        search_terms=["ML"],
        databases_used=["Google Scholar"],
        inclusion_criteria=["relevant"],
        exclusion_criteria=[],
        citations=["Bad citation format"]
    )

    print("\n\U0001F4CA Testing High-Quality Research Data:")
    good_prisma = await framework.validators[0].validate(high_quality)
    print(f"   PRISMA Score: {good_prisma.score:.2f} (Pass: {good_prisma.passed})")

    print("\n\U0001F4C9 Testing Poor-Quality Research Data:")
    bad_prisma = await framework.validators[0].validate(poor_quality)
    print(f"   PRISMA Score: {bad_prisma.score:.2f} (Pass: {bad_prisma.passed})")

    print("\n\U0001F4DD Testing Citation Validation:")
    citation_result = await framework.validators[1].validate(high_quality)
    print(f"   Citation Score: {citation_result.score:.2f} (Pass: {citation_result.passed})")

    print("\n\u2705 Demo Complete")

if __name__ == "__main__":
    asyncio.run(main())
