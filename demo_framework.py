#!/usr/bin/env python3
"""
Simple demonstration of the Academic Validation Framework.
"""

import asyncio
import sys
from pathlib import Path

# Add framework to path
framework_path = Path(__file__).parent / "academic_validation_framework"
sys.path.insert(0, str(framework_path))

# Sample research data
SAMPLE_RESEARCH = {
    "title": "Machine Learning Applications in Healthcare: A Systematic Review",
    "content": """
    ## Abstract
    **Objective**: To systematically review machine learning applications in healthcare.
    **Methods**: Systematic search across PubMed, EMBASE, Cochrane databases.
    **Results**: 150 studies identified, showing significant potential.
    **Conclusion**: ML shows promise but requires further validation.
    
    ## Methods
    ### Search Strategy
    Comprehensive search using PubMed/MEDLINE, EMBASE, Cochrane Library.
    Search terms: "machine learning", "healthcare", "medical diagnosis".
    
    ### Inclusion Criteria
    - Applied ML in healthcare settings
    - Published 2018-2023
    - Peer-reviewed publications
    
    ### Data Extraction
    Performed by two independent reviewers using standardized forms.
    
    ### Quality Assessment
    Used QUADAS-2 and Cochrane Risk of Bias tools.
    """,
    "citations": [
        {"text": "Smith, J. (2023). Deep learning in medical imaging. Journal of Medical AI, 15(3), 245-267."},
        {"text": "Brown, M. (2022). ML in clinical decision support. Healthcare Technology Review, 12(4), 112-128."},
    ],
    "metadata": {"type": "systematic_review", "discipline": "Medicine"}
}


async def run_demo():
    """Run the framework demo."""
    print("🔬 Academic Validation Framework Demo")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    from config import FrameworkConfig
    
    # Configure framework
    config = FrameworkConfig(
        output_dir="demo_results",
        console_logging=False,  # Reduce noise
        auto_generate_reports=False
    )
    
    runner = ComprehensiveTestRunner(config=config)
    
    try:
        print(f"📊 Framework Components:")
        print(f"   Validators: {len(runner.framework.validators)}")
        print(f"   Benchmarks: {len(runner.framework.benchmarks)}")
        
        print(f"\n🧪 Running validation...")
        
        session = await runner.run_comprehensive_validation(
            research_output=SAMPLE_RESEARCH,
            session_id="demo",
            discipline="Medicine",
            citation_style="APA",
            methodology="Systematic Review"
        )
        
        print(f"\n📈 Results:")
        print(f"   Total Tests: {session.total_count}")
        print(f"   Passed: {session.passed_count}")
        print(f"   Failed: {session.failed_count}")
        print(f"   Success Rate: {session.success_rate:.1%}")
        
        print(f"\n📋 Test Results:")
        for result in session.results[:5]:  # Show first 5 results
            status = "✅" if result.passed else "❌"
            score = f"({result.score:.2f})" if result.score else ""
            print(f"   {status} {result.test_name} {score}")
        
        if len(session.results) > 5:
            print(f"   ... and {len(session.results) - 5} more tests")
        
        print(f"\n✅ Demo completed successfully!")
        
    finally:
        await runner.cleanup()


def main():
    print("🚀 Academic Validation Framework - Quick Demo")
    print("Comprehensive testing for academic research validation\n")
    
    try:
        asyncio.run(run_demo())
        print(f"\n🎯 This framework provides:")
        print(f"   • PRISMA systematic review validation")
        print(f"   • Citation accuracy checking")
        print(f"   • Performance benchmarking")
        print(f"   • Extensible modular architecture")
        return 0
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())