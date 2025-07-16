"""
PRISMA Assistant Demonstration

Shows how an honest research assistant can save 80% of the grunt work
while being transparent about what requires human expertise.
"""

import asyncio
from datetime import datetime
from typing import List

from knowledge_storm.prisma_assistant import (
    PRISMAAssistant, Paper, SearchStrategy
)


async def demonstrate_prisma_assistant():
    """Full demonstration of PRISMA Assistant capabilities."""
    
    print("🎓 PRISMA ASSISTANT DEMONSTRATION")
    print("An Honest Systematic Review Assistant")
    print("=" * 60)
    
    # Research question
    research_question = "What is the diagnostic accuracy of AI algorithms for detecting diabetic retinopathy compared to ophthalmologist assessment?"
    
    print(f"\n📋 Research Question:")
    print(f"   {research_question}")
    print("=" * 60)
    
    # Initialize assistant
    assistant = PRISMAAssistant()
    
    # Simulate some papers for demonstration
    mock_papers = create_mock_papers()
    
    print(f"\n📚 Processing {len(mock_papers)} papers from database searches...")
    
    # Run the assistant
    results = await assistant.assist_systematic_review(
        research_question=research_question,
        papers=mock_papers,
        generate_draft=True  # Include zero draft
    )
    
    # Display results
    display_results(results)
    
    # Show time/cost comparison
    show_efficiency_comparison(results)
    
    # Show zero draft excerpt
    if results['zero_draft']:
        show_draft_excerpt(results['zero_draft'])


def create_mock_papers() -> List[Paper]:
    """Create realistic mock papers for demonstration."""
    return [
        # Definitely include
        Paper(
            id="1",
            title="Deep Learning Algorithm for Automated Detection of Diabetic Retinopathy: A Diagnostic Accuracy Study",
            abstract="This study evaluated a deep learning algorithm for detecting diabetic retinopathy. Methods: 10,000 retinal images were analyzed. The algorithm achieved sensitivity of 90.3% and specificity of 98.1% compared to ophthalmologist grading.",
            authors=["Smith J", "Chen L", "Williams K"],
            year=2023,
            journal="JAMA Ophthalmology"
        ),
        
        # Definitely include
        Paper(
            id="2", 
            title="Artificial Intelligence Screening for Diabetic Retinopathy: Systematic Validation Against Clinical Standards",
            abstract="Prospective validation study of AI system for DR screening. The AI system analyzed 5,000 patients with diabetes. Results showed 87% sensitivity and 94% specificity using ophthalmologist assessment as reference standard.",
            authors=["Johnson A", "Patel R"],
            year=2022,
            journal="Diabetes Care"
        ),
        
        # Needs human review (unclear methodology)
        Paper(
            id="3",
            title="Machine Learning in Diabetic Eye Disease: A Pilot Study",
            abstract="We explored machine learning for diabetic complications. Our approach showed promise in identifying retinal changes. Further research with larger samples is needed to validate these preliminary findings.",
            authors=["Davis M"],
            year=2021,
            journal="Journal of Medical AI"
        ),
        
        # Definitely exclude (animal study)
        Paper(
            id="4",
            title="Automated Detection of Retinopathy in Diabetic Rats Using Computer Vision",
            abstract="This study developed an algorithm to detect retinal changes in rat models of diabetes. Using 500 images from diabetic rats, we achieved high accuracy in detecting vascular changes.",
            authors=["Lee S", "Kim J"],
            year=2023,
            journal="Experimental Eye Research"
        ),
        
        # Definitely exclude (wrong topic)
        Paper(
            id="5",
            title="AI-Powered Insulin Dosing for Type 1 Diabetes Management",
            abstract="This RCT evaluated an AI system for optimizing insulin dosing in type 1 diabetes. The system improved glycemic control compared to standard care.",
            authors=["Brown T"],
            year=2023,
            journal="Diabetes Technology"
        ),
        
        # Needs human review (conference abstract)
        Paper(
            id="6",
            title="Novel CNN Architecture for Diabetic Retinopathy Screening",
            abstract="Conference Abstract: We present a new convolutional neural network achieving 92% accuracy in DR detection. Full results will be presented at the conference.",
            authors=["Wilson E"],
            year=2023,
            journal="ARVO Annual Meeting Abstracts"
        ),
        
        # Definitely include  
        Paper(
            id="7",
            title="Comparative Study of AI and Human Graders in Diabetic Retinopathy Assessment",
            abstract="Head-to-head comparison of AI system versus retinal specialists. 15,000 images graded by both AI and 3 ophthalmologists. AI sensitivity 89.2%, specificity 95.7%. Strong agreement between AI and human graders (kappa=0.85).",
            authors=["Garcia M", "Thompson K"],
            year=2023,
            journal="Ophthalmology"
        ),
        
        # Definitely exclude (editorial)
        Paper(
            id="8",
            title="Editorial: The Promise and Pitfalls of AI in Diabetic Eye Care",
            abstract="Editorial discussing the potential of artificial intelligence in ophthalmology. We review recent developments and offer perspectives on future directions.",
            authors=["Editorial Board"],
            year=2023,
            journal="Eye"
        ),
        
        # More papers for realistic volume...
        *[Paper(
            id=str(i),
            title=f"Study {i}: Various Aspects of Diabetic Retinopathy",
            abstract=f"Abstract for study {i} with various findings...",
            authors=[f"Author{i}"],
            year=2020 + (i % 4),
            journal="Various Journals"
        ) for i in range(9, 101)]  # Simulate 100 total papers
    ]


def display_results(results: dict):
    """Display the assistant results in a clear format."""
    
    print("\n🔍 1. SEARCH STRATEGY DEVELOPED")
    print("-" * 50)
    strategy = results['search_strategy']
    
    print("📊 PICO Elements Identified:")
    for element, terms in strategy.pico_elements.items():
        if terms:
            print(f"   {element.upper()}: {', '.join(terms)}")
    
    print("\n🔎 Database-Specific Queries Generated:")
    for db, query in list(strategy.search_queries.items())[:3]:  # Show first 3
        print(f"\n   {db.upper()}:")
        print(f"   {query[:100]}...")  # First 100 chars
    
    print(f"\n   ✅ Queries generated for {len(strategy.search_queries)} databases")
    
    print("\n\n📑 2. SCREENING RESULTS (80/20 TARGET)")
    print("-" * 50)
    screening = results['screening_results']
    
    print(f"   Total papers screened: {results['metrics']['papers_processed']}")
    print(f"   ✅ Auto-INCLUDED (≥80% confidence): {screening['definitely_include']} papers")
    print(f"   ❌ Auto-EXCLUDED (≥80% confidence): {screening['definitely_exclude']} papers")
    print(f"   ❓ Need human review (<80% confidence): {screening['needs_human_review']} papers")
    
    # Show 80/20 performance
    if 'performance_metrics' in results:
        perf = results['performance_metrics']
        print(f"\n   📊 80/20 Performance:")
        print(f"      • Auto-decision rate: {perf.get('auto_decision_rate', 0):.1%} (target: 80%)")
        print(f"      • Human review rate: {perf.get('human_review_rate', 0):.1%} (target: 20%)")
        print(f"      • Target achieved: {'✅ YES' if perf.get('target_achieved', False) else '❌ NO'}")
    
    print("\n   Exclusion reasons:")
    for reason, count in screening['exclusion_stats'].items():
        print(f"      • {reason}: {count} papers")
    
    print("\n\n📊 3. DATA EXTRACTION TEMPLATE")
    print("-" * 50)
    template = results['extraction_template']
    
    print("   Standard fields configured:")
    for field, config in list(template.fields.items())[:5]:  # Show first 5
        print(f"      • {field}: {config['type']} {'(required)' if config['required'] else '(optional)'}")
    
    print(f"\n   ✅ Total fields configured: {len(template.fields)}")
    print(f"   ✅ Outcome measures identified: {len(template.outcome_measures)}")
    print(f"   ✅ Quality indicators included: {len(template.quality_indicators)}")
    
    print("\n\n📋 4. PRISMA TEMPLATES")
    print("-" * 50)
    print("   ✅ PRISMA flow diagram data prepared")
    print("   ✅ PRISMA checklist generated with progress tracking")
    print("   ✅ Reporting templates ready for completion")


def show_efficiency_comparison(results: dict):
    """Show time and cost savings."""
    
    print("\n\n💰 EFFICIENCY ANALYSIS")
    print("=" * 60)
    
    metrics = results['metrics']
    time_saved = metrics['time_saved_hours']
    
    print("⏱️  TIME COMPARISON:")
    print(f"   Traditional approach: ~{time_saved * 5:.0f} hours")
    print(f"   With PRISMA Assistant: ~{time_saved * 4:.0f} hours")
    print(f"   Time saved: {time_saved:.1f} hours ({time_saved/5:.0%} reduction)")
    
    print("\n💵 COST COMPARISON (at $50/hour for RA):")
    print(f"   Traditional cost: ${time_saved * 5 * 50:.0f}")
    print(f"   With Assistant: ${time_saved * 4 * 50:.0f}")
    print(f"   Money saved: ${time_saved * 50:.0f}")
    
    print("\n✅ QUALITY IMPROVEMENTS:")
    print("   • Consistent application of inclusion/exclusion criteria")
    print("   • No missed papers due to fatigue")
    print("   • Standardized data extraction templates")
    print("   • Audit trail for all decisions")
    
    print("\n👤 HUMAN TASKS REMAINING:")
    for task in metrics['human_tasks']:
        print(f"   • {task}")


def show_draft_excerpt(zero_draft: str):
    """Show excerpt from zero draft."""
    
    print("\n\n📝 ZERO DRAFT EXCERPT")
    print("=" * 60)
    print("⚠️  NOTE: This is to overcome blank page syndrome only")
    print("-" * 60)
    
    # Show first 1000 characters
    excerpt = zero_draft[:1000] + "\n\n[... DRAFT CONTINUES ...]"
    print(excerpt)
    
    print("\n" + "=" * 60)
    print("✅ Full draft includes all PRISMA sections with placeholders")
    print("✅ Clear markers for what needs human verification")
    print("✅ Checklist of remaining tasks")


async def demonstrate_real_world_scenario():
    """Demonstrate a real-world research scenario."""
    
    print("\n\n🌍 REAL-WORLD SCENARIO")
    print("=" * 60)
    
    print("\n📚 Dr. Sarah Chen, Ophthalmology Researcher")
    print("   Task: Systematic review on AI in diabetic retinopathy")
    print("   Deadline: 3 months")
    print("   Resources: 1 part-time research assistant")
    
    print("\n⚡ WITHOUT PRISMA Assistant:")
    print("   Week 1-2: Developing search strategy")
    print("   Week 3-6: Screening 2,000 abstracts") 
    print("   Week 7-8: Setting up data extraction")
    print("   Week 9-12: Extraction, synthesis, writing")
    print("   Total: 12 weeks, high burnout risk")
    
    print("\n✨ WITH PRISMA Assistant:")
    print("   Day 1: Search strategy + initial screening (80% automated)")
    print("   Week 1-2: Review uncertain papers + full-text screening")
    print("   Week 3-6: Data extraction + synthesis (templates ready)")
    print("   Week 7-8: Writing + revisions (zero draft available)")
    print("   Total: 8 weeks, focused on high-value tasks")
    
    print("\n💡 OUTCOME:")
    print("   ✅ 33% faster completion")
    print("   ✅ More time for quality assessment")
    print("   ✅ Better work-life balance")
    print("   ✅ Comprehensive audit trail")


async def main():
    """Run all demonstrations."""
    
    # Main demonstration
    await demonstrate_prisma_assistant()
    
    # Real-world scenario
    await demonstrate_real_world_scenario()
    
    print("\n\n🎯 KEY TAKEAWAY")
    print("=" * 60)
    print("The PRISMA Assistant handles the tedious 80% so researchers")
    print("can focus on the critical 20% that requires expertise.")
    print("\nHonest automation > Overpromising AI")


if __name__ == "__main__":
    asyncio.run(main())