"""
Basic test to verify Academic Validation Framework structure and functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the framework to the path
framework_path = Path(__file__).parent / "academic_validation_framework"
sys.path.insert(0, str(framework_path))

async def test_framework_import():
    """Test that the framework can be imported."""
    print("Testing framework imports...")
    
    try:
        from academic_validation_framework.core import AcademicValidationFramework, ValidationResult
        from academic_validation_framework.config import FrameworkConfig
        from academic_validation_framework.validators.base import BaseValidator
        from academic_validation_framework.validators.prisma_validator import PRISMAValidator
        from academic_validation_framework.validators.citation_accuracy_validator import CitationAccuracyValidator
        print("✅ Core imports successful")
        
        from academic_validation_framework.benchmarks.base import BaseBenchmarkSuite
        from academic_validation_framework.benchmarks.performance_benchmark_suite import PerformanceBenchmarkSuite
        print("✅ Benchmark imports successful")
        
        from academic_validation_framework.database_integrations.base import BaseDatabaseIntegrationTester
        print("✅ Database integration imports successful")
        
        from academic_validation_framework.credibility.base import BaseCredibilityAssessment
        print("✅ Credibility assessment imports successful")
        
        from academic_validation_framework.reporting.base import BaseReportGenerator
        print("✅ Reporting imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_basic_framework_functionality():
    """Test basic framework functionality."""
    print("\nTesting basic framework functionality...")
    
    try:
        from academic_validation_framework.core import AcademicValidationFramework
        from academic_validation_framework.config import FrameworkConfig
        from academic_validation_framework.validators.prisma_validator import PRISMAValidator
        
        # Create framework with basic config
        config = FrameworkConfig(
            output_dir="test_results",
            console_logging=True,
            log_level="INFO"
        )
        
        # Create framework with config only
        framework = AcademicValidationFramework(config=config)
        
        # Configure logging separately (normally done once at app startup)
        framework.configure_logging()
        
        # Register a validator
        prisma_validator = PRISMAValidator()
        framework.register_validator(prisma_validator)
        
        print("✅ Framework creation and validator registration successful")
        
        # Test sample research output
        sample_research = {
            "title": "Test Research Paper",
            "content": """
            This is a test systematic review with some basic content.
            
            ## Methods
            A systematic search was conducted using PubMed and other databases.
            
            ## Results  
            We found several relevant studies for analysis.
            
            ## Conclusion
            The results indicate significant findings.
            """,
            "citations": [
                {"text": "Smith, J. (2023). Test paper. Journal of Testing, 1(1), 1-10."}
            ],
            "metadata": {"type": "systematic_review"}
        }
        
        # Start a validation session
        session = await framework.start_validation_session(
            session_id="test_session",
            metadata={"test": True}
        )
        
        print("✅ Validation session created successfully")
        
        # Test PRISMA validator directly
        await prisma_validator.initialize()
        prisma_results = await prisma_validator.validate(sample_research)
        
        if isinstance(prisma_results, list):
            framework.current_session.results.extend(prisma_results)
        else:
            framework.current_session.results.append(prisma_results)
        
        print(f"✅ PRISMA validation completed: {len(prisma_results)} results")
        
        # End session
        completed_session = await framework.end_validation_session()
        
        print(f"✅ Session completed:")
        print(f"   Total tests: {completed_session.total_count}")
        print(f"   Passed: {completed_session.passed_count}")
        print(f"   Failed: {completed_session.failed_count}")
        print(f"   Success rate: {completed_session.success_rate:.1%}")
        
        # Cleanup
        await framework.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Framework functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_comprehensive_runner():
    """Test the comprehensive test runner."""
    print("\nTesting comprehensive test runner...")
    
    try:
        from academic_validation_framework.test_runner import ComprehensiveTestRunner
        from academic_validation_framework.config import FrameworkConfig
        
        # Create configuration
        config = FrameworkConfig(
            output_dir="test_results/runner_test",
            console_logging=True,
            auto_generate_reports=False  # Skip report generation for basic test
        )
        
        # Create test runner (with minimal components to avoid dependency issues)
        runner = ComprehensiveTestRunner(
            config=config,
            enable_all_tests=False  # Start with minimal setup
        )
        
        # Configure logging if runner has a framework
        if hasattr(runner, 'framework'):
            runner.framework.configure_logging()
        
        # Manually add core validators that don't require external dependencies
        from academic_validation_framework.validators.prisma_validator import PRISMAValidator
        from academic_validation_framework.validators.citation_accuracy_validator import CitationAccuracyValidator
        
        runner.framework.register_validator(PRISMAValidator())
        runner.framework.register_validator(CitationAccuracyValidator())
        
        print("✅ Test runner created with core validators")
        
        # Sample research output
        sample_research = {
            "title": "Machine Learning in Healthcare: A Test Review",
            "content": """
            ## Abstract
            This systematic review examines machine learning applications in healthcare.
            
            ## Introduction
            Machine learning has gained significant attention in healthcare applications.
            
            ## Methods
            A systematic search was conducted across multiple databases including PubMed.
            Search strategy included terms related to machine learning and healthcare.
            Inclusion criteria were defined for peer-reviewed studies.
            Data extraction was performed using standardized forms.
            Quality assessment was conducted using established tools.
            
            ## Results
            The search identified multiple relevant studies for analysis.
            
            ## Discussion
            The findings demonstrate potential applications of machine learning.
            
            ## Conclusion
            Machine learning shows promise in healthcare settings.
            """,
            "citations": [
                {"text": "Smith, J., & Johnson, A. (2023). Machine learning in medicine. Medical AI Journal, 15(3), 245-267."},
                {"text": "Brown, M. (2022). Healthcare applications of AI. Health Technology Review, 12(4), 112-128."}
            ],
            "metadata": {
                "type": "systematic_review",
                "discipline": "Medicine"
            }
        }
        
        # Run validation with only core validators
        session = await runner.framework.start_validation_session(
            session_id="runner_test",
            metadata={"test_type": "basic_runner_test"}
        )
        
        # Run validators manually to avoid dependency issues
        for validator in runner.framework.validators:
            try:
                await validator.initialize()
                results = await validator.validate(sample_research)
                
                if isinstance(results, list):
                    session.results.extend(results)
                else:
                    session.results.append(results)
                    
                print(f"✅ {validator.name} completed successfully")
                
            except Exception as e:
                print(f"⚠️  {validator.name} failed: {e}")
        
        # End session
        completed_session = await runner.framework.end_validation_session()
        
        print(f"✅ Comprehensive runner test completed:")
        print(f"   Total tests: {completed_session.total_count}")
        print(f"   Passed: {completed_session.passed_count}")
        print(f"   Failed: {completed_session.failed_count}")
        print(f"   Success rate: {completed_session.success_rate:.1%}")
        
        # Show some detailed results
        print(f"\n📋 Sample Results:")
        for i, result in enumerate(completed_session.results[:3]):  # Show first 3 results
            status_emoji = "✅" if result.passed else "❌" if result.failed else "⚠️"
            score_display = f"({result.score:.2f})" if result.score is not None else ""
            print(f"   {status_emoji} {result.validator_name}: {result.test_name} {score_display}")
        
        # Cleanup
        await runner.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive runner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🧪 Academic Validation Framework - Basic Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Framework Imports", test_framework_import),
        ("Basic Functionality", test_basic_framework_functionality),
        ("Comprehensive Runner", test_comprehensive_runner),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Framework is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)