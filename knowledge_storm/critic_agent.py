"""
Revolutionary CriticAgent for storm-loop: The keystone of self-improving research.

This agent provides actionable feedback across all research phases, maintaining 
consistent quality standards and knowing when to be satisfied with the output.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CriticDomain(Enum):
    """Domains of criticism for research evaluation."""
    PLANNING = "planning"
    RESEARCH = "research" 
    WRITING = "writing"
    CITATIONS = "citations"


class FeedbackSeverity(Enum):
    """Severity levels for critic feedback."""
    CRITICAL = "critical"      # Must fix before proceeding
    IMPORTANT = "important"    # Should fix for quality
    MINOR = "minor"           # Nice to have improvements
    SATISFIED = "satisfied"    # Quality threshold met


@dataclass
class CriticFeedback:
    """Structured feedback from the critic agent."""
    domain: CriticDomain
    severity: FeedbackSeverity
    issue: str
    specific_improvement: str
    quality_score: float  # 0-1 scale
    is_actionable: bool = True
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate feedback quality."""
        if self.is_actionable and not self.specific_improvement:
            raise ValueError("Actionable feedback must include specific improvements")


@dataclass
class ResearchArtifact:
    """Container for research artifacts to be evaluated."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    previous_feedback: List[CriticFeedback] = field(default_factory=list)


class CriticEvaluator(ABC):
    """Abstract base class for specialized critics."""
    
    @abstractmethod
    async def evaluate(self, artifact: ResearchArtifact) -> List[CriticFeedback]:
        """Evaluate artifact and return specific feedback."""
        pass
    
    @abstractmethod
    def get_quality_threshold(self) -> float:
        """Return minimum quality score for satisfaction."""
        pass


class PlanningCritic(CriticEvaluator):
    """Evaluates research plan quality and methodology."""
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
        self.quality_threshold = 0.8
        
    async def evaluate(self, artifact: ResearchArtifact) -> List[CriticFeedback]:
        """Evaluate research plan comprehensiveness and methodology."""
        feedback = []
        plan_content = artifact.content
        
        # Rule-based checks
        feedback.extend(self._check_plan_structure(plan_content))
        feedback.extend(self._check_methodology(plan_content))
        feedback.extend(self._check_scope_feasibility(plan_content))
        
        # LLM-based deep evaluation
        if self.lm_model:
            feedback.extend(await self._llm_evaluate_plan(plan_content))
            
        return feedback
    
    def _check_plan_structure(self, plan: str) -> List[CriticFeedback]:
        """Check if plan has required structural elements."""
        feedback = []
        required_sections = ['objectives', 'methodology', 'scope', 'timeline']
        
        for section in required_sections:
            if section.lower() not in plan.lower():
                feedback.append(CriticFeedback(
                    domain=CriticDomain.PLANNING,
                    severity=FeedbackSeverity.CRITICAL,
                    issue=f"Missing required section: {section}",
                    specific_improvement=f"Add a {section} section that clearly defines the research {section}",
                    quality_score=0.3
                ))
        
        return feedback
    
    def _check_methodology(self, plan: str) -> List[CriticFeedback]:
        """Evaluate methodological rigor."""
        feedback = []
        
        # Check for methodology keywords
        method_keywords = ['approach', 'method', 'framework', 'analysis', 'evaluation']
        if not any(keyword in plan.lower() for keyword in method_keywords):
            feedback.append(CriticFeedback(
                domain=CriticDomain.PLANNING,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Methodology insufficiently detailed",
                specific_improvement="Specify the research methodology, analytical framework, and evaluation criteria",
                quality_score=0.5
            ))
        
        return feedback
    
    def _check_scope_feasibility(self, plan: str) -> List[CriticFeedback]:
        """Check if scope is realistic and well-defined."""
        feedback = []
        
        # Simple heuristic: very short plans might be underscoped
        if len(plan.split()) < 100:
            feedback.append(CriticFeedback(
                domain=CriticDomain.PLANNING,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Research scope appears underspecified",
                specific_improvement="Expand the scope definition with specific research questions, boundaries, and deliverables",
                quality_score=0.4
            ))
        
        return feedback
    
    async def _llm_evaluate_plan(self, plan: str) -> List[CriticFeedback]:
        """Use LLM for deep plan evaluation."""
        # This would integrate with STORM's LLM components
        # For now, return placeholder feedback
        return [CriticFeedback(
            domain=CriticDomain.PLANNING,
            severity=FeedbackSeverity.MINOR,
            issue="LLM evaluation not yet implemented",
            specific_improvement="Implement LLM-based plan evaluation for deeper insights",
            quality_score=0.7
        )]
    
    def get_quality_threshold(self) -> float:
        return self.quality_threshold


class ResearchCritic(CriticEvaluator):
    """Evaluates research data comprehensiveness and quality."""
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
        self.quality_threshold = 0.75
        
    async def evaluate(self, artifact: ResearchArtifact) -> List[CriticFeedback]:
        """Evaluate research data quality and comprehensiveness."""
        feedback = []
        research_content = artifact.content
        
        # Rule-based checks
        feedback.extend(self._check_source_diversity(research_content))
        feedback.extend(self._check_coverage_depth(research_content))
        feedback.extend(self._check_recency(research_content))
        
        # LLM-based evaluation
        if self.lm_model:
            feedback.extend(await self._llm_evaluate_research(research_content))
            
        return feedback
    
    def _check_source_diversity(self, research: str) -> List[CriticFeedback]:
        """Check for diverse source types and perspectives."""
        feedback = []
        
        # Simple heuristic: count potential source indicators
        source_indicators = ['doi:', 'http', 'arxiv', 'pmid', 'isbn']
        source_count = sum(1 for indicator in source_indicators if indicator in research.lower())
        
        if source_count < 3:
            feedback.append(CriticFeedback(
                domain=CriticDomain.RESEARCH,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Limited source diversity detected",
                specific_improvement="Include more diverse sources: academic papers, reports, case studies, and expert opinions",
                quality_score=0.4
            ))
        
        return feedback
    
    def _check_coverage_depth(self, research: str) -> List[CriticFeedback]:
        """Evaluate depth and comprehensiveness of research."""
        feedback = []
        
        # Heuristic: very short research might be superficial
        if len(research.split()) < 500:
            feedback.append(CriticFeedback(
                domain=CriticDomain.RESEARCH,
                severity=FeedbackSeverity.CRITICAL,
                issue="Research depth appears insufficient",
                specific_improvement="Expand research with detailed analysis, multiple perspectives, and supporting evidence",
                quality_score=0.3
            ))
        
        return feedback
    
    def _check_recency(self, research: str) -> List[CriticFeedback]:
        """Check for recent and relevant information."""
        feedback = []
        
        # Simple check for year mentions
        import re
        years = re.findall(r'\b(20[0-2][0-9])\b', research)
        recent_years = [year for year in years if int(year) >= 2020]
        
        if len(recent_years) < 2:
            feedback.append(CriticFeedback(
                domain=CriticDomain.RESEARCH,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Limited recent sources identified",
                specific_improvement="Include more recent sources (2020+) to ensure current relevance",
                quality_score=0.6
            ))
        
        return feedback
    
    async def _llm_evaluate_research(self, research: str) -> List[CriticFeedback]:
        """Use LLM for deep research evaluation."""
        # Placeholder for LLM integration
        return []
    
    def get_quality_threshold(self) -> float:
        return self.quality_threshold


class WritingCritic(CriticEvaluator):
    """Evaluates writing quality, structure, and argument strength."""
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
        self.quality_threshold = 0.8
        
    async def evaluate(self, artifact: ResearchArtifact) -> List[CriticFeedback]:
        """Evaluate writing quality and structure."""
        feedback = []
        writing_content = artifact.content
        
        # Rule-based checks
        feedback.extend(self._check_structure(writing_content))
        feedback.extend(self._check_clarity(writing_content))
        feedback.extend(self._check_argument_flow(writing_content))
        
        # LLM-based evaluation
        if self.lm_model:
            feedback.extend(await self._llm_evaluate_writing(writing_content))
            
        return feedback
    
    def _check_structure(self, writing: str) -> List[CriticFeedback]:
        """Check document structure and organization."""
        feedback = []
        
        # Check for basic structure elements
        structure_elements = ['introduction', 'conclusion', 'summary']
        if not any(element in writing.lower() for element in structure_elements):
            feedback.append(CriticFeedback(
                domain=CriticDomain.WRITING,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Missing structural elements",
                specific_improvement="Add clear introduction, body sections, and conclusion to improve readability",
                quality_score=0.5
            ))
        
        return feedback
    
    def _check_clarity(self, writing: str) -> List[CriticFeedback]:
        """Evaluate writing clarity and readability."""
        feedback = []
        
        # Simple readability heuristic
        sentences = writing.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if avg_sentence_length > 25:
            feedback.append(CriticFeedback(
                domain=CriticDomain.WRITING,
                severity=FeedbackSeverity.MINOR,
                issue="Some sentences may be too long",
                specific_improvement="Break down complex sentences to improve readability",
                quality_score=0.7
            ))
        
        return feedback
    
    def _check_argument_flow(self, writing: str) -> List[CriticFeedback]:
        """Check logical flow and argument coherence."""
        feedback = []
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'moreover', 'furthermore', 'consequently']
        transition_count = sum(1 for word in transition_words if word in writing.lower())
        
        if transition_count < 2:
            feedback.append(CriticFeedback(
                domain=CriticDomain.WRITING,
                severity=FeedbackSeverity.MINOR,
                issue="Limited use of transition words",
                specific_improvement="Add transition words to improve logical flow between ideas",
                quality_score=0.75
            ))
        
        return feedback
    
    async def _llm_evaluate_writing(self, writing: str) -> List[CriticFeedback]:
        """Use LLM for deep writing evaluation."""
        # Placeholder for LLM integration
        return []
    
    def get_quality_threshold(self) -> float:
        return self.quality_threshold


class CitationCritic(CriticEvaluator):
    """Evaluates citation accuracy and completeness."""
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
        self.quality_threshold = 0.9
        
    async def evaluate(self, artifact: ResearchArtifact) -> List[CriticFeedback]:
        """Evaluate citation quality and accuracy."""
        feedback = []
        content = artifact.content
        
        # Rule-based checks
        feedback.extend(self._check_citation_format(content))
        feedback.extend(self._check_citation_coverage(content))
        feedback.extend(self._check_citation_quality(content))
        
        return feedback
    
    def _check_citation_format(self, content: str) -> List[CriticFeedback]:
        """Check citation format consistency."""
        feedback = []
        
        # Simple check for citation patterns
        import re
        citations = re.findall(r'\[[^\]]+\]|\([^)]+\)', content)
        
        if len(citations) < 3:
            feedback.append(CriticFeedback(
                domain=CriticDomain.CITATIONS,
                severity=FeedbackSeverity.CRITICAL,
                issue="Insufficient citations detected",
                specific_improvement="Add proper citations for all factual claims and research findings",
                quality_score=0.2
            ))
        
        return feedback
    
    def _check_citation_coverage(self, content: str) -> List[CriticFeedback]:
        """Check if claims are properly cited."""
        feedback = []
        
        # Heuristic: look for claim indicators without nearby citations
        claim_indicators = ['research shows', 'studies indicate', 'according to', 'evidence suggests']
        
        for indicator in claim_indicators:
            if indicator in content.lower():
                # Check if citation appears nearby (simple heuristic)
                indicator_pos = content.lower().find(indicator)
                nearby_text = content[indicator_pos:indicator_pos+200]
                if '[' not in nearby_text and '(' not in nearby_text:
                    feedback.append(CriticFeedback(
                        domain=CriticDomain.CITATIONS,
                        severity=FeedbackSeverity.IMPORTANT,
                        issue=f"Uncited claim detected: '{indicator}'",
                        specific_improvement=f"Add citation for claim containing '{indicator}'",
                        quality_score=0.5
                    ))
        
        return feedback
    
    def _check_citation_quality(self, content: str) -> List[CriticFeedback]:
        """Evaluate citation quality and relevance."""
        feedback = []
        
        # Check for URL vs. proper academic citations
        url_count = content.count('http')
        bracket_count = content.count('[')
        
        if url_count > bracket_count:
            feedback.append(CriticFeedback(
                domain=CriticDomain.CITATIONS,
                severity=FeedbackSeverity.IMPORTANT,
                issue="Many raw URLs detected instead of proper citations",
                specific_improvement="Convert URLs to proper academic citations with author, title, year, and source",
                quality_score=0.6
            ))
        
        return feedback
    
    def get_quality_threshold(self) -> float:
        return self.quality_threshold


class CriticAgent:
    """
    Revolutionary critic agent that provides actionable feedback across all research phases.
    
    This is the keystone of the storm-loop system, maintaining quality standards
    and driving iterative improvement through specific, actionable feedback.
    """
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
        self.critics = {
            CriticDomain.PLANNING: PlanningCritic(lm_model),
            CriticDomain.RESEARCH: ResearchCritic(lm_model),
            CriticDomain.WRITING: WritingCritic(lm_model),
            CriticDomain.CITATIONS: CitationCritic(lm_model)
        }
        
    async def evaluate_artifact(self, artifact: ResearchArtifact, domain: CriticDomain) -> List[CriticFeedback]:
        """Evaluate artifact in specific domain."""
        if domain not in self.critics:
            raise ValueError(f"Unknown domain: {domain}")
            
        critic = self.critics[domain]
        return await critic.evaluate(artifact)
    
    async def comprehensive_evaluation(self, artifact: ResearchArtifact) -> Dict[CriticDomain, List[CriticFeedback]]:
        """Perform comprehensive evaluation across all domains."""
        results = {}
        
        for domain, critic in self.critics.items():
            results[domain] = await critic.evaluate(artifact)
            
        return results
    
    def is_satisfied(self, feedback_results: Dict[CriticDomain, List[CriticFeedback]], 
                    domain: Optional[CriticDomain] = None) -> bool:
        """
        Determine if quality standards are met for satisfaction.
        
        Args:
            feedback_results: Results from evaluation
            domain: Specific domain to check, or None for all domains
            
        Returns:
            True if quality threshold is met, False otherwise
        """
        domains_to_check = [domain] if domain else self.critics.keys()
        
        for check_domain in domains_to_check:
            if check_domain not in feedback_results:
                return False
                
            feedback_list = feedback_results[check_domain]
            
            # Check for critical issues
            if any(f.severity == FeedbackSeverity.CRITICAL for f in feedback_list):
                return False
                
            # Check quality score threshold
            critic = self.critics[check_domain]
            avg_quality = sum(f.quality_score for f in feedback_list) / len(feedback_list) if feedback_list else 1.0
            
            if avg_quality < critic.get_quality_threshold():
                return False
                
        return True
    
    def get_actionable_feedback(self, feedback_results: Dict[CriticDomain, List[CriticFeedback]]) -> List[CriticFeedback]:
        """Extract actionable feedback ordered by severity."""
        all_feedback = []
        for domain_feedback in feedback_results.values():
            all_feedback.extend(f for f in domain_feedback if f.is_actionable)
        
        # Sort by severity (critical first)
        severity_order = {
            FeedbackSeverity.CRITICAL: 0,
            FeedbackSeverity.IMPORTANT: 1,
            FeedbackSeverity.MINOR: 2,
            FeedbackSeverity.SATISFIED: 3
        }
        
        return sorted(all_feedback, key=lambda f: severity_order[f.severity])
    
    def generate_improvement_summary(self, feedback_results: Dict[CriticDomain, List[CriticFeedback]]) -> str:
        """Generate human-readable improvement summary."""
        actionable_feedback = self.get_actionable_feedback(feedback_results)
        
        if not actionable_feedback:
            return "Quality standards met. No improvements needed."
        
        summary_parts = []
        
        # Group by severity
        by_severity = {}
        for feedback in actionable_feedback:
            if feedback.severity not in by_severity:
                by_severity[feedback.severity] = []
            by_severity[feedback.severity].append(feedback)
        
        for severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.IMPORTANT, FeedbackSeverity.MINOR]:
            if severity in by_severity:
                summary_parts.append(f"\n{severity.value.upper()} ISSUES:")
                for feedback in by_severity[severity]:
                    summary_parts.append(f"  • {feedback.issue}")
                    summary_parts.append(f"    → {feedback.specific_improvement}")
        
        return "\n".join(summary_parts)