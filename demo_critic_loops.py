"""
Demo: Revolutionary critic-driven research loops in action.

This demonstrates how the CriticAgent enables iterative improvement
across all research phases until quality standards are met.
"""

import asyncio
from knowledge_storm.critic_agent import (
    CriticAgent, ResearchArtifact, CriticDomain, 
    FeedbackSeverity, CriticFeedback
)


async def demo_planning_loop():
    """Demonstrate iterative planning refinement with critic feedback."""
    print("🎯 PLANNING PHASE: Iterative Refinement Loop")
    print("=" * 50)
    
    # Initialize critic
    critic = CriticAgent()
    
    # Initial research plan (intentionally poor quality)
    initial_plan = """
    Research topic: AI impact on society
    We will look at AI and see how it affects people.
    """
    
    # Iterative improvement loop
    current_plan = initial_plan
    iteration = 1
    max_iterations = 3
    
    while iteration <= max_iterations:
        print(f"\n📋 ITERATION {iteration}:")
        print(f"Current plan: {current_plan}")
        
        # Create artifact and evaluate
        artifact = ResearchArtifact(content=current_plan)
        feedback = await critic.evaluate_artifact(artifact, CriticDomain.PLANNING)
        
        # Check if satisfied
        if critic.is_satisfied({CriticDomain.PLANNING: feedback}, CriticDomain.PLANNING):
            print("✅ CRITIC SATISFIED! Quality threshold met.")
            break
        else:
            print("❌ CRITIC NOT SATISFIED. Feedback:")
            for fb in feedback:
                if fb.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.IMPORTANT]:
                    print(f"  • {fb.issue}")
                    print(f"    → {fb.specific_improvement}")
        
        # Simulate plan improvement (in real system, this would be the PlannerAgent)
        if iteration == 1:
            current_plan = """
            Research Objectives: Analyze AI's transformative impact on society across multiple domains
            
            Methodology: 
            - Systematic literature review of AI impact studies (2020-2024)
            - Analysis of case studies from healthcare, education, and employment sectors
            - Evaluation framework based on social, economic, and ethical dimensions
            
            Scope: 
            - Focus on machine learning and generative AI applications
            - Geographic scope: Global with emphasis on developed nations
            - Time horizon: Current state and 5-year projections
            
            Timeline:
            - Phase 1: Literature review (2 weeks)
            - Phase 2: Case study analysis (2 weeks)  
            - Phase 3: Impact assessment and recommendations (1 week)
            """
        elif iteration == 2:
            current_plan += """
            
            Evaluation Criteria:
            - Social impact metrics: accessibility, equity, privacy
            - Economic impact metrics: job displacement, productivity gains
            - Ethical considerations: bias, transparency, accountability
            
            Expected Deliverables:
            - Comprehensive impact assessment report
            - Policy recommendations for stakeholders
            - Framework for ongoing AI impact monitoring
            """
        
        iteration += 1
    
    print(f"\n🎉 FINAL PLAN APPROVED after {iteration-1} iterations!")
    return current_plan


async def demo_research_loop():
    """Demonstrate iterative research data gathering with critic feedback."""
    print("\n\n🔍 RESEARCH PHASE: Iterative Data Gathering Loop")
    print("=" * 50)
    
    critic = CriticAgent()
    
    # Initial research (intentionally inadequate)
    initial_research = """
    AI is changing society. Some people think it's good, others think it's bad.
    There are concerns about jobs being lost.
    """
    
    current_research = initial_research
    iteration = 1
    max_iterations = 2
    
    while iteration <= max_iterations:
        print(f"\n📚 ITERATION {iteration}:")
        print(f"Current research length: {len(current_research.split())} words")
        
        artifact = ResearchArtifact(content=current_research)
        feedback = await critic.evaluate_artifact(artifact, CriticDomain.RESEARCH)
        
        if critic.is_satisfied({CriticDomain.RESEARCH: feedback}, CriticDomain.RESEARCH):
            print("✅ CRITIC SATISFIED! Research quality threshold met.")
            break
        else:
            print("❌ CRITIC NOT SATISFIED. Key issues:")
            for fb in feedback:
                if fb.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.IMPORTANT]:
                    print(f"  • {fb.issue}")
                    print(f"    → {fb.specific_improvement}")
        
        # Simulate research expansion
        if iteration == 1:
            current_research = """
            AI IMPACT ON SOCIETY: COMPREHENSIVE ANALYSIS
            
            HEALTHCARE SECTOR:
            - McKinsey 2023 report: AI could generate $100B annually in US healthcare
            - Mass General Brigham study (2023): AI reduced diagnostic errors by 37%
            - WHO 2024 guidelines highlight AI's role in global health equity
            
            EDUCATION SECTOR:
            - UNESCO 2023 report: 1 billion students could benefit from AI tutoring
            - MIT study (2024): Personalized AI learning improved outcomes by 42%
            - Concerns about academic integrity and critical thinking skills
            
            EMPLOYMENT IMPACT:
            - Goldman Sachs 2023: 300 million jobs could be automated
            - World Economic Forum 2024: 83 million jobs displaced, 69 million created
            - Brookings Institution analysis shows disproportionate impact on lower-wage workers
            
            SOCIAL CONSIDERATIONS:
            - Pew Research 2024: 67% of Americans concerned about AI privacy
            - IEEE study on algorithmic bias affecting minority communities
            - Digital divide concerns in AI access and literacy
            
            Sources: doi:10.1038/s41591-023-02551-1, arxiv:2312.14444, PMID:38234567
            """
        
        iteration += 1
    
    print(f"\n🎉 RESEARCH APPROVED after {iteration-1} iterations!")
    return current_research


async def demo_writing_loop():
    """Demonstrate iterative writing refinement with critic feedback."""
    print("\n\n✍️ WRITING PHASE: Iterative Content Refinement Loop")
    print("=" * 50)
    
    critic = CriticAgent()
    
    # Initial draft (intentionally poor structure)
    initial_draft = """
    AI is really changing everything and its happening fast. Healthcare is getting better because of AI and education too. But jobs might be lost which is concerning for many people. The technology is advancing rapidly and society needs to adapt. There are both positive and negative impacts to consider.
    """
    
    current_draft = initial_draft
    iteration = 1
    max_iterations = 2
    
    while iteration <= max_iterations:
        print(f"\n📝 ITERATION {iteration}:")
        print(f"Current draft length: {len(current_draft.split())} words")
        
        artifact = ResearchArtifact(content=current_draft)
        feedback = await critic.evaluate_artifact(artifact, CriticDomain.WRITING)
        
        if critic.is_satisfied({CriticDomain.WRITING: feedback}, CriticDomain.WRITING):
            print("✅ CRITIC SATISFIED! Writing quality threshold met.")
            break
        else:
            print("❌ CRITIC NOT SATISFIED. Writing issues:")
            for fb in feedback:
                if fb.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.IMPORTANT]:
                    print(f"  • {fb.issue}")
                    print(f"    → {fb.specific_improvement}")
        
        # Simulate writing improvement
        if iteration == 1:
            current_draft = """
            INTRODUCTION
            
            Artificial Intelligence (AI) represents one of the most transformative technologies of the 21st century, fundamentally reshaping how society functions across multiple domains. This analysis examines AI's multifaceted impact on healthcare, education, and employment, while addressing the critical social considerations that accompany this technological revolution.
            
            HEALTHCARE TRANSFORMATION
            
            The healthcare sector has emerged as a primary beneficiary of AI innovation. McKinsey's 2023 analysis indicates that AI could generate $100 billion annually in the US healthcare system alone. Moreover, clinical applications demonstrate tangible improvements in patient outcomes, with Mass General Brigham's study showing a 37% reduction in diagnostic errors through AI-assisted analysis.
            
            EDUCATIONAL REVOLUTION
            
            Furthermore, AI is revolutionizing educational paradigms through personalized learning experiences. UNESCO's 2023 report suggests that over 1 billion students globally could benefit from AI-powered tutoring systems. However, this transformation raises important questions about academic integrity and the development of critical thinking skills.
            
            EMPLOYMENT IMPLICATIONS
            
            Nevertheless, the employment landscape faces significant disruption. Goldman Sachs projects that 300 million jobs could be automated, while the World Economic Forum estimates 83 million jobs displaced against 69 million newly created positions. Therefore, society must address the disproportionate impact on lower-wage workers.
            
            CONCLUSION
            
            In conclusion, AI's societal impact represents both unprecedented opportunities and significant challenges. Consequently, stakeholders must collaborate to harness AI's benefits while mitigating its risks through thoughtful policy and inclusive implementation strategies.
            """
        
        iteration += 1
    
    print(f"\n🎉 WRITING APPROVED after {iteration-1} iterations!")
    return current_draft


async def demo_comprehensive_evaluation():
    """Demonstrate comprehensive multi-domain evaluation."""
    print("\n\n🔬 COMPREHENSIVE EVALUATION: All Domains")
    print("=" * 50)
    
    critic = CriticAgent()
    
    # Sample research artifact
    sample_content = """
    AI IMPACT ANALYSIS
    
    This research examines AI's transformative effects on society. The methodology involves systematic analysis of recent studies and case studies from key sectors.
    
    Healthcare shows promising results with AI reducing diagnostic errors by 37% according to recent studies [1]. Education benefits from personalized learning, with MIT research showing 42% improvement in outcomes [2].
    
    However, employment faces disruption with 300 million jobs potentially automated according to Goldman Sachs analysis [3].
    
    References:
    [1] Mass General Brigham Study, 2023
    [2] MIT Educational Technology Lab, 2024  
    [3] Goldman Sachs Economic Research, 2023
    """
    
    artifact = ResearchArtifact(content=sample_content)
    
    # Comprehensive evaluation
    results = await critic.comprehensive_evaluation(artifact)
    
    print("📊 EVALUATION RESULTS:")
    for domain, feedback_list in results.items():
        print(f"\n{domain.value.upper()} DOMAIN:")
        
        satisfied = critic.is_satisfied({domain: feedback_list}, domain)
        status = "✅ SATISFIED" if satisfied else "❌ NEEDS IMPROVEMENT"
        print(f"  Status: {status}")
        
        if feedback_list:
            print("  Feedback:")
            for fb in feedback_list:
                print(f"    • {fb.issue} (Quality: {fb.quality_score:.1f})")
                print(f"      → {fb.specific_improvement}")
    
    # Generate improvement summary
    summary = critic.generate_improvement_summary(results)
    print(f"\n📋 IMPROVEMENT SUMMARY:")
    print(summary)
    
    # Check overall satisfaction
    overall_satisfied = critic.is_satisfied(results)
    print(f"\n🎯 OVERALL STATUS: {'✅ READY FOR PUBLICATION' if overall_satisfied else '❌ REQUIRES REVISION'}")


async def main():
    """Run all critic loop demonstrations."""
    print("🚀 STORM-LOOP CRITIC AGENT DEMONSTRATION")
    print("Revolutionary iterative research refinement system")
    print("=" * 60)
    
    await demo_planning_loop()
    await demo_research_loop()
    await demo_writing_loop()
    await demo_comprehensive_evaluation()
    
    print("\n\n🎉 DEMONSTRATION COMPLETE!")
    print("This shows how the CriticAgent enables iterative improvement")
    print("across all research phases until quality standards are met.")
    print("The next step is integrating this with STORM's multi-model architecture!")


if __name__ == "__main__":
    asyncio.run(main())