"""
Main VERIFY system orchestrator.

The complete VERIFY system for efficient, validated research.
Focuses on single-pass generation, fact verification, targeted fixes, and learning.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .models import Claim
from .fact_checker import FactChecker
from .memory import ResearchMemory
from .fixer import TargetedFixer

logger = logging.getLogger(__name__)


class VERIFYSystem:
    """
    The complete VERIFY system for efficient, validated research.
    
    Focus on:
    - Single-pass generation with maximum context
    - Fact verification over format checking  
    - Targeted fixes over wholesale regeneration
    - Learning from each research project
    """
    
    def __init__(self, 
                 lm_model=None,
                 retrieval_module=None,
                 memory_path="research_memory"):
        
        self.lm_model = lm_model
        self.retrieval_module = retrieval_module
        
        # Core components
        self.fact_checker = FactChecker(retrieval_module)
        self.memory = ResearchMemory(memory_path)
        self.fixer = TargetedFixer(lm_model)
        
        # Metrics
        self.total_cost = 0.0
        self.total_time = 0.0
        self.api_calls = 0
    
    async def generate_research(self, 
                              topic: str, 
                              domain: str = "general",
                              user_requirements: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate research with single-pass generation and targeted verification.
        
        This is the main entry point showing the efficient approach.
        """
        start_time = datetime.now()
        
        # 1. Get relevant context from memory
        logger.info(f"Loading learned patterns for domain: {domain}")
        context = self.memory.get_relevant_context(topic, domain)
        
        # 2. Single-pass generation with maximum context
        logger.info("Generating research in single pass with learned context")
        research_text = await self._generate_with_context(topic, context, user_requirements)
        self.api_calls += 1
        
        # 3. Retrieve sources for fact checking
        logger.info("Retrieving sources for verification")
        sources = await self._retrieve_sources(topic, research_text)
        
        # 4. Verify facts and claims
        logger.info("Verifying claims against sources")
        verification_results = await self.fact_checker.verify_research(research_text, sources)
        
        # 5. Fix only what's broken
        error_count = sum(1 for r in verification_results if r.severity == "error")
        if error_count > 0:
            logger.info(f"Fixing {error_count} verification errors")
            research_text = await self.fixer.fix_issues(research_text, verification_results)
            self.api_calls += 1  # Only for fixes
        
        # 6. Learn for next time
        logger.info("Learning patterns from this research")
        self.memory.learn_from_research(research_text, verification_results, domain)
        
        # Calculate metrics
        end_time = datetime.now()
        self.total_time = (end_time - start_time).total_seconds()
        
        # Prepare results
        return {
            "research": research_text,
            "verification_results": verification_results,
            "metrics": {
                "total_time": self.total_time,
                "api_calls": self.api_calls,
                "estimated_cost": self.api_calls * 0.03,  # Rough estimate
                "claims_verified": len(verification_results),
                "error_rate": error_count / len(verification_results) if verification_results else 0,
                "sources_used": len(sources)
            },
            "domain": domain,
            "learned_patterns": len(context.get("domain_patterns", []))
        }
    
    async def _generate_with_context(self, 
                                   topic: str, 
                                   context: Dict[str, Any],
                                   user_requirements: Optional[Dict] = None) -> str:
        """Generate research with learned context."""
        
        # Build enhanced prompt with learned patterns
        prompt = f"""Generate comprehensive research on: {topic}

Based on successful patterns for this domain:
- Structure: {json.dumps(context.get('successful_structures', [])[:2], indent=2)}
- Common pitfalls to avoid: {'; '.join(context.get('common_pitfalls', []))}
- Recommended sources: {', '.join(list(context.get('domain_knowledge', {}).get('common_sources', {}).keys())[:5])}

Requirements:
{json.dumps(user_requirements or {}, indent=2)}

Generate a well-researched article with proper citations."""

        # In production, this would call the actual LM
        # For demo, return placeholder
        return f"""# Research on {topic}

## Introduction
This research examines {topic} with a focus on recent developments and empirical evidence.

## Key Findings
Recent studies indicate significant developments in {topic}. According to Smith et al. (2023), 
the impact has been measured at 45% improvement over baseline approaches [1].

## Analysis
The data suggests multiple factors contribute to these outcomes. A 2024 meta-analysis 
by Johnson Research Institute found consistent patterns across 127 studies [2].

## Conclusion
The evidence supports continued investigation into {topic}, with particular attention 
to implementation challenges and scalability concerns.

References:
[1] Smith et al. (2023). "Advances in {topic}". Journal of Research.
[2] Johnson Research Institute (2024). "Meta-analysis of {topic} Studies"."""
    
    async def _retrieve_sources(self, topic: str, research_text: str) -> List[Dict]:
        """Retrieve sources for fact verification."""
        if not self.retrieval_module:
            return []
        
        # Extract key terms for search
        key_terms = self._extract_key_terms(research_text)
        
        # Search for sources
        sources = []
        for term in key_terms[:5]:  # Limit searches for efficiency
            try:
                results = await self.retrieval_module.search(f"{topic} {term}")
                sources.extend(results)
            except:
                pass
        
        return sources
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms for source retrieval."""
        # Simple implementation - in production use NLP
        # Look for capitalized phrases and quoted terms
        terms = re.findall(r'"([^"]+)"|([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        return [t[0] or t[1] for t in terms if t[0] or t[1]]

    async def _generate_initial_research(self, topic: str) -> str:
        """Generate initial research content. For test mocking."""
        return await self._generate_with_context(topic, {}, None)

    async def verify_and_fix(self, research_text: str) -> str:
        """Verify and fix research text. Public interface for tests."""
        # Extract sources from the research text for verification
        sources = []  # In real implementation, would extract from text
        
        # Verify claims
        verification_results = await self.fact_checker.verify_research(research_text, sources)
        
        # Apply fixes only to unsupported claims
        for result in verification_results:
            if not result.is_supported and result.suggested_fix:
                research_text = await self.fixer.apply_fix(research_text, result)
        
        return research_text

    def _calculate_overall_confidence(self, claims: List[Claim]) -> float:
        """Calculate overall confidence score from claims."""
        if not claims:
            return 0.0
        
        total_confidence = sum(claim.confidence for claim in claims)
        return total_confidence / len(claims)

    def _assess_claim_quality(self, claim: Claim) -> float:
        """Assess the quality of a claim for PRISMA scoring."""
        score = 0.0
        
        # Check for citation
        if claim.source_cited:
            score += 0.4
        
        # Check for specific details (numbers, dates, etc.)
        if re.search(r'\d+[%]?|\b\d{4}\b', claim.text):
            score += 0.3
        
        # Check for academic language
        academic_terms = ['study', 'research', 'analysis', 'significant', 'demonstrated']
        if any(term in claim.text.lower() for term in academic_terms):
            score += 0.2
        
        # Check context quality
        if len(claim.context) > 100:  # Substantial context
            score += 0.1
        
        return min(1.0, score)