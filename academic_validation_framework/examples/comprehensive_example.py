"""
Comprehensive Example: Academic Validation Framework

This example demonstrates how to use the Academic Validation Framework
to validate research outputs across multiple dimensions including PRISMA
compliance, citation accuracy, performance benchmarks, and credibility assessment.
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sample research output for testing
SAMPLE_RESEARCH_OUTPUT = {
    "title": "Machine Learning Applications in Healthcare: A Systematic Review",
    "content": """
    # Machine Learning Applications in Healthcare: A Systematic Review
    
    ## Abstract
    
    **Objective**: To systematically review the current applications of machine learning 
    in healthcare and assess their effectiveness.
    
    **Methods**: A systematic search was conducted across PubMed, EMBASE, and Cochrane 
    databases from January 2018 to December 2023. Studies were selected based on predefined 
    inclusion criteria. Data extraction was performed using standardized forms.
    
    **Results**: A total of 150 studies were identified and analyzed. The findings indicate 
    significant potential for machine learning applications in diagnostic imaging, 
    predictive analytics, and personalized treatment.
    
    **Conclusion**: Machine learning shows promise in healthcare applications but requires 
    further validation and standardization.
    
    ## Introduction
    
    The integration of machine learning (ML) technologies in healthcare has gained 
    significant momentum in recent years. This systematic review aims to provide a 
    comprehensive overview of current ML applications in healthcare settings.
    
    ## Methods
    
    ### Search Strategy
    
    A comprehensive search was conducted using the following databases:
    - PubMed/MEDLINE
    - EMBASE  
    - Cochrane Library
    - IEEE Xplore
    
    Search terms included: "machine learning", "artificial intelligence", "healthcare", 
    "medical diagnosis", "predictive modeling".
    
    ### Inclusion Criteria
    
    Studies were included if they:
    - Applied machine learning techniques in healthcare settings
    - Published between 2018-2023
    - Reported quantitative outcomes
    - Were peer-reviewed publications
    
    ### Data Extraction
    
    Data extraction was performed by two independent reviewers using a standardized form.
    Disagreements were resolved through consensus.
    
    ### Quality Assessment
    
    The quality of included studies was assessed using the QUADAS-2 tool for diagnostic 
    accuracy studies and the Cochrane Risk of Bias tool for interventional studies.
    
    ## Results
    
    The search yielded 2,456 potentially relevant articles. After screening and full-text 
    review, 150 studies met the inclusion criteria.
    
    ### Study Characteristics
    
    The included studies covered various healthcare domains including:
    - Diagnostic imaging (n=65, 43.3%)
    - Clinical decision support (n=45, 30.0%)
    - Drug discovery (n=25, 16.7%)
    - Personalized medicine (n=15, 10.0%)
    
    ### Machine Learning Applications
    
    Deep learning was the most commonly used approach (n=85, 56.7%), followed by 
    ensemble methods (n=35, 23.3%) and support vector machines (n=30, 20.0%).
    
    ## Discussion
    
    Our findings demonstrate the growing adoption of machine learning in healthcare.
    However, several challenges remain including data privacy, regulatory approval,
    and clinical integration.
    
    ## Conclusion
    
    Machine learning applications in healthcare show significant promise but require
    continued research and validation efforts.
    """,
    "citations": [
        {
            "text": "Smith, J., Johnson, A., & Williams, K. (2023). Deep learning in medical imaging: A comprehensive review. Journal of Medical AI, 15(3), 245-267.",
            "doi": "10.1000/jmai.2023.15.3.245"
        },
        {
            "text": "Brown, M., Davis, L., & Wilson, R. (2022). Machine learning applications in clinical decision support systems. Healthcare Technology Review, 12(4), 112-128.",
            "doi": "10.1000/htr.2022.12.4.112"
        },
        {
            "text": "Lee, S., Kim, H., & Chen, W. (2023). Artificial intelligence in drug discovery: Current trends and future directions. Nature Machine Intelligence, 8(2), 89-104.",
            "doi": "10.1038/nmi.2023.89"
        },
        {
            "text": "Taylor, P., Anderson, C., & Thompson, D. (2022). Personalized medicine using machine learning: A systematic approach. Precision Medicine Journal, 7(1), 23-41.",
            "doi": "10.1000/pmj.2022.7.1.23"
        },
        {
            "text": "Garcia, M., Martinez, L., & Rodriguez, A. (2023). Ethical considerations in AI-driven healthcare. Medical Ethics Quarterly, 45(2), 156-172.",
            "doi": "10.1000/meq.2023.45.2.156"
        }
    ],
    "metadata": {
        "type": "systematic_review",
        "discipline": "Medicine",
        "methodology": "Systematic Review",
        "citation_style": "APA",
        "authors": ["Dr. Academic Researcher", "Prof. Review Expert"],
        "institution": "Academic Medical Center",
        "submission_date": "2024-01-15"
    }
}


async def run_basic_validation_example():
    """Example of basic research validation."""
    print("🔬 Running Basic Validation Example")
    print("=" * 50)
    
    # Import after defining sample data to avoid circular imports
    import sys
    from pathlib import Path
    framework_path = Path(__file__).parent.parent
    sys.path.insert(0, str(framework_path))
    
    from test_runner import ComprehensiveTestRunner
    from config import FrameworkConfig
    
    # Configure framework
    config = FrameworkConfig(
        output_dir="validation_results/basic_example",
        log_level="INFO",
        console_logging=True,
        min_prisma_compliance=0.75,
        min_citation_accuracy=0.90
    )
    
    # Create test runner
    runner = ComprehensiveTestRunner(config=config)
    
    try:
        # Run comprehensive validation
        session = await runner.run_comprehensive_validation(
            research_output=SAMPLE_RESEARCH_OUTPUT,
            session_id="basic_validation_example",
            discipline="Medicine",
            citation_style="APA",
            methodology="Systematic Review"
        )
        
        # Print results summary
        print(f"\n📊 Validation Results Summary:")
        print(f"Session ID: {session.session_id}")
        print(f"Total Tests: {session.total_count}")
        print(f"Passed: {session.passed_count}")
        print(f"Failed: {session.failed_count}")
        print(f"Success Rate: {session.success_rate:.1%}")
        print(f"Duration: {session.duration:.2f}s")
        
        # Show detailed results
        print(f"\n📋 Detailed Test Results:")
        for result in session.results:
            status_emoji = "✅" if result.passed else "❌" if result.failed else "⚠️"
            score_display = f"({result.score:.2f})" if result.score is not None else ""
            print(f"{status_emoji} {result.validator_name}: {result.test_name} {score_display}")
        
        # Generate reports
        print(f"\n📄 Generating Reports...")
        report_files = await runner.generate_comprehensive_reports(session)
        
        print(f"Generated Reports:")
        for report_type, files in report_files.items():
            print(f"  {report_type}: {len(files)} files")
            for file_path in files:
                print(f"    - {file_path}")
        
        return session
        
    finally:
        await runner.cleanup()


async def run_prisma_specific_example():
    """Example of PRISMA-specific validation."""
    print("\n📚 Running PRISMA-Specific Validation Example")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
    
    try:
        # Run only PRISMA validation
        session = await runner.run_prisma_validation_only(
            research_output=SAMPLE_RESEARCH_OUTPUT
        )
        
        print(f"\n📊 PRISMA Validation Results:")
        print(f"Total PRISMA Tests: {session.total_count}")
        print(f"Passed: {session.passed_count}")
        print(f"Failed: {session.failed_count}")
        
        # Show PRISMA-specific results
        for result in session.results:
            if "prisma" in result.test_name.lower():
                status_emoji = "✅" if result.passed else "❌"
                score_display = f"({result.score:.2f})" if result.score is not None else ""
                print(f"{status_emoji} {result.test_name} {score_display}")
                
                # Show recommendations if available
                if "recommendations" in result.details:
                    print(f"    Recommendations:")
                    for rec in result.details["recommendations"]:
                        print(f"      • {rec}")
        
        return session
        
    finally:
        await runner.cleanup()


async def run_citation_validation_example():
    """Example of citation accuracy validation."""
    print("\n📖 Running Citation Validation Example")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
    
    try:
        # Run only citation validation
        session = await runner.run_citation_validation_only(
            research_output=SAMPLE_RESEARCH_OUTPUT,
            citation_style="APA"
        )
        
        print(f"\n📊 Citation Validation Results:")
        print(f"Total Citation Tests: {session.total_count}")
        print(f"Passed: {session.passed_count}")
        print(f"Failed: {session.failed_count}")
        
        # Show citation-specific results
        for result in session.results:
            if "citation" in result.test_name.lower():
                status_emoji = "✅" if result.passed else "❌"
                score_display = f"({result.score:.2f})" if result.score is not None else ""
                print(f"{status_emoji} {result.test_name} {score_display}")
                
                # Show citation statistics if available
                if "citation_style" in result.details:
                    print(f"    Citation Style: {result.details['citation_style']}")
                if "total_citations" in result.details:
                    print(f"    Total Citations: {result.details['total_citations']}")
        
        return session
        
    finally:
        await runner.cleanup()


async def run_performance_benchmark_example():
    """Example of performance benchmarking."""
    print("\n⚡ Running Performance Benchmark Example")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
    
    try:
        # Run only performance benchmarks
        session = await runner.run_performance_benchmarks_only(
            research_output=SAMPLE_RESEARCH_OUTPUT
        )
        
        print(f"\n📊 Performance Benchmark Results:")
        print(f"Total Performance Tests: {session.total_count}")
        print(f"Passed: {session.passed_count}")
        print(f"Failed: {session.failed_count}")
        
        # Show performance-specific results
        for result in session.results:
            if "benchmark" in result.test_name.lower():
                status_emoji = "✅" if result.passed else "❌"
                score_display = f"({result.score:.2f})" if result.score is not None else ""
                print(f"{status_emoji} {result.test_name} {score_display}")
                
                # Show performance metrics if available
                if "benchmark_metrics" in result.metadata:
                    metrics = result.metadata["benchmark_metrics"]
                    if "execution_time" in metrics:
                        print(f"    Execution Time: {metrics['execution_time']:.3f}s")
                    if "throughput" in metrics:
                        print(f"    Throughput: {metrics['throughput']:.2f} ops/s")
        
        return session
        
    finally:
        await runner.cleanup()


async def run_cross_disciplinary_example():
    """Example of cross-disciplinary validation."""
    print("\n🌐 Running Cross-Disciplinary Validation Example")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
    
    try:
        # Test across multiple disciplines
        disciplines = ["Computer Science", "Medicine", "Biology"]
        
        sessions = await runner.run_cross_disciplinary_validation(
            research_output=SAMPLE_RESEARCH_OUTPUT,
            disciplines=disciplines
        )
        
        print(f"\n📊 Cross-Disciplinary Results:")
        
        for discipline, session in sessions.items():
            print(f"\n{discipline}:")
            print(f"  Success Rate: {session.success_rate:.1%}")
            print(f"  Duration: {session.duration:.2f}s")
            print(f"  Tests: {session.passed_count}/{session.total_count}")
        
        # Generate summary
        summary = runner.get_validation_summary(list(sessions.values()))
        print(f"\nOverall Summary:")
        print(f"  Total Sessions: {summary['total_sessions']}")
        print(f"  Average Success Rate: {summary['average_success_rate']:.1%}")
        print(f"  Total Tests: {summary['total_tests']}")
        
        return sessions
        
    finally:
        await runner.cleanup()


async def run_framework_info_example():
    """Example of getting framework information."""
    print("\n🔍 Framework Information Example")
    print("=" * 50)
    
    from test_runner import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
    
    try:
        # Get framework info
        info = runner.get_framework_info()
        
        print(f"📊 Framework Statistics:")
        stats = info["framework_stats"]
        print(f"  Registered Validators: {stats['registered_validators']}")
        print(f"  Registered Benchmarks: {stats['registered_benchmarks']}")
        print(f"  Registered Database Testers: {stats['registered_database_testers']}")
        print(f"  Registered Credibility Assessors: {stats['registered_credibility_assessors']}")
        
        print(f"\n🔧 Component Details:")
        components = info["component_details"]
        
        print(f"Validators:")
        for validator in components["validators"]:
            print(f"  • {validator['name']}: {validator['description']}")
        
        return info
        
    finally:
        await runner.cleanup()


async def main():
    """Run all examples."""
    print("🚀 Academic Validation Framework - Comprehensive Examples")
    print("=" * 60)
    
    try:
        # Run basic validation
        await run_basic_validation_example()
        
        # Run PRISMA-specific validation
        await run_prisma_specific_example()
        
        # Run citation validation
        await run_citation_validation_example()
        
        # Run performance benchmarks
        await run_performance_benchmark_example()
        
        # Run cross-disciplinary validation
        await run_cross_disciplinary_example()
        
        # Show framework information
        await run_framework_info_example()
        
        print("\n✅ All examples completed successfully!")
        print("\nCheck the 'validation_results' directory for generated reports.")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())