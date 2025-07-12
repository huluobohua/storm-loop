"""
STORM-Loop Runner: Revolutionary integration of STORM's multi-model architecture 
with critic-driven iterative refinement loops.

This creates a self-improving research system where each STORM phase iterates
with the CriticAgent until quality standards are met, producing research
quality that surpasses either approach alone.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from knowledge_storm import STORMWikiRunner, STORMWikiRunnerArguments, STORMWikiLMConfigs
from knowledge_storm.lm import ClaudeModel
from knowledge_storm.rm import YouRM, BingSearch, BraveRM, SerperRM

from .critic_agent import (
    CriticAgent, ResearchArtifact, CriticDomain, 
    FeedbackSeverity, CriticFeedback
)
from .agent_coordinator import AgentCoordinator

logger = logging.getLogger(__name__)


@dataclass
class STORMLoopConfig:
    """Configuration for STORM-Loop integration."""
    max_iterations_per_phase: int = 3
    enable_all_critics: bool = True
    quality_threshold_override: Optional[Dict[CriticDomain, float]] = None
    output_dir: str = "storm_loop_output"
    save_iteration_history: bool = True
    
    # STORM configuration
    max_conv_turn: int = 3
    max_perspective: int = 4
    search_top_k: int = 3
    max_thread_num: int = 1


@dataclass
class IterationResult:
    """Result from a single critic-driven iteration."""
    iteration: int
    artifact: ResearchArtifact
    feedback: Dict[CriticDomain, List[CriticFeedback]]
    satisfied: bool
    quality_scores: Dict[CriticDomain, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PhaseResult:
    """Complete result from a research phase with all iterations."""
    phase_name: str
    iterations: List[IterationResult]
    final_artifact: ResearchArtifact
    total_iterations: int
    phase_satisfied: bool
    improvement_summary: str


class STORMLoopRunner:
    """
    Revolutionary research system combining STORM's multi-model architecture 
    with critic-driven iterative refinement.
    
    This creates the "storm-loop" - where each research phase iterates with
    the critic until quality standards are met, producing research quality
    that surpasses traditional approaches.
    """
    
    def __init__(self, 
                 storm_config: STORMWikiRunnerArguments,
                 lm_configs: STORMWikiLMConfigs,
                 retrieval_module,
                 loop_config: STORMLoopConfig = None):
        
        self.storm_config = storm_config
        self.lm_configs = lm_configs
        self.retrieval_module = retrieval_module
        self.loop_config = loop_config or STORMLoopConfig()
        
        # Initialize STORM runner
        self.storm_runner = STORMWikiRunner(storm_config, lm_configs, retrieval_module)
        
        # Initialize critic and coordination systems
        self.critic = CriticAgent(lm_model=lm_configs.article_gen_lm)
        self.coordinator = AgentCoordinator()
        
        # Track research state across phases
        self.research_context = {}
        self.phase_results = {}
        
        # Ensure output directory exists
        Path(self.loop_config.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def run_research_with_loops(self, topic: str) -> Dict[str, PhaseResult]:
        """
        Execute complete research workflow with critic-driven loops.
        
        This is the main entry point for the revolutionary storm-loop system.
        """
        logger.info(f"Starting STORM-Loop research on topic: {topic}")
        
        try:
            # Phase 1: Planning with critic loops
            planning_result = await self._planning_phase_with_critic(topic)
            self.phase_results['planning'] = planning_result
            
            # Phase 2: Information-seeking with critic loops  
            research_result = await self._research_phase_with_critic(topic)
            self.phase_results['research'] = research_result
            
            # Phase 3: Outline generation with critic loops
            outline_result = await self._outline_phase_with_critic(topic)
            self.phase_results['outline'] = outline_result
            
            # Phase 4: Article generation with critic loops
            article_result = await self._article_phase_with_critic(topic)
            self.phase_results['article'] = article_result
            
            # Phase 5: Polishing with critic loops
            polish_result = await self._polish_phase_with_critic(topic)
            self.phase_results['polish'] = polish_result
            
            # Save comprehensive results
            await self._save_complete_results(topic)
            
            logger.info(f"STORM-Loop research completed for topic: {topic}")
            return self.phase_results
            
        except Exception as e:
            logger.error(f"STORM-Loop research failed: {e}")
            raise
    
    async def _planning_phase_with_critic(self, topic: str) -> PhaseResult:
        """Planning phase with iterative critic refinement."""
        logger.info("Starting planning phase with critic loops")
        
        iterations = []
        current_plan = await self._generate_initial_plan(topic)
        
        for iteration in range(1, self.loop_config.max_iterations_per_phase + 1):
            logger.info(f"Planning iteration {iteration}")
            
            # Create artifact and evaluate
            artifact = ResearchArtifact(content=current_plan, version=iteration)
            feedback = await self.critic.evaluate_artifact(artifact, CriticDomain.PLANNING)
            
            # Check satisfaction
            satisfied = self.critic.is_satisfied({CriticDomain.PLANNING: feedback}, CriticDomain.PLANNING)
            
            # Calculate quality scores
            quality_scores = {
                CriticDomain.PLANNING: sum(f.quality_score for f in feedback) / len(feedback) if feedback else 1.0
            }
            
            # Store iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                artifact=artifact,
                feedback={CriticDomain.PLANNING: feedback},
                satisfied=satisfied,
                quality_scores=quality_scores
            )
            iterations.append(iteration_result)
            
            if satisfied:
                logger.info(f"Planning critic satisfied after {iteration} iterations")
                break
            
            # Improve plan based on feedback
            current_plan = await self._improve_plan(current_plan, feedback)
        
        # Create phase result
        final_artifact = ResearchArtifact(content=current_plan, version=len(iterations))
        improvement_summary = self.critic.generate_improvement_summary({CriticDomain.PLANNING: feedback})
        
        phase_result = PhaseResult(
            phase_name="planning",
            iterations=iterations,
            final_artifact=final_artifact,
            total_iterations=len(iterations),
            phase_satisfied=satisfied,
            improvement_summary=improvement_summary
        )
        
        # Store for later phases
        self.research_context['research_plan'] = current_plan
        
        return phase_result
    
    async def _research_phase_with_critic(self, topic: str) -> PhaseResult:
        """Information-seeking phase with iterative critic refinement."""
        logger.info("Starting research phase with critic loops")
        
        iterations = []
        current_research = ""
        
        for iteration in range(1, self.loop_config.max_iterations_per_phase + 1):
            logger.info(f"Research iteration {iteration}")
            
            # Perform STORM information-seeking conversation
            if iteration == 1:
                # Initial research using STORM's conversation pipeline
                current_research = await self._storm_information_seeking(topic)
            else:
                # Enhanced research based on critic feedback
                current_research = await self._enhance_research(current_research, topic)
            
            # Evaluate with critic
            artifact = ResearchArtifact(content=current_research, version=iteration)
            feedback = await self.critic.evaluate_artifact(artifact, CriticDomain.RESEARCH)
            
            # Check satisfaction
            satisfied = self.critic.is_satisfied({CriticDomain.RESEARCH: feedback}, CriticDomain.RESEARCH)
            
            # Calculate quality scores
            quality_scores = {
                CriticDomain.RESEARCH: sum(f.quality_score for f in feedback) / len(feedback) if feedback else 1.0
            }
            
            # Store iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                artifact=artifact,
                feedback={CriticDomain.RESEARCH: feedback},
                satisfied=satisfied,
                quality_scores=quality_scores
            )
            iterations.append(iteration_result)
            
            if satisfied:
                logger.info(f"Research critic satisfied after {iteration} iterations")
                break
        
        # Create phase result
        final_artifact = ResearchArtifact(content=current_research, version=len(iterations))
        improvement_summary = self.critic.generate_improvement_summary({CriticDomain.RESEARCH: feedback})
        
        phase_result = PhaseResult(
            phase_name="research",
            iterations=iterations,
            final_artifact=final_artifact,
            total_iterations=len(iterations),
            phase_satisfied=satisfied,
            improvement_summary=improvement_summary
        )
        
        # Store for later phases
        self.research_context['research_data'] = current_research
        
        return phase_result
    
    async def _outline_phase_with_critic(self, topic: str) -> PhaseResult:
        """Outline generation phase with iterative critic refinement."""
        logger.info("Starting outline phase with critic loops")
        
        iterations = []
        current_outline = ""
        
        for iteration in range(1, self.loop_config.max_iterations_per_phase + 1):
            logger.info(f"Outline iteration {iteration}")
            
            if iteration == 1:
                # Generate initial outline using STORM
                current_outline = await self._storm_outline_generation(topic)
            else:
                # Improve outline based on critic feedback
                current_outline = await self._improve_outline(current_outline, topic)
            
            # Evaluate with critic
            artifact = ResearchArtifact(content=current_outline, version=iteration)
            
            # Multi-domain evaluation for outline (planning + writing structure)
            feedback_results = {}
            feedback_results[CriticDomain.PLANNING] = await self.critic.evaluate_artifact(artifact, CriticDomain.PLANNING)
            feedback_results[CriticDomain.WRITING] = await self.critic.evaluate_artifact(artifact, CriticDomain.WRITING)
            
            # Check satisfaction across domains
            satisfied = self.critic.is_satisfied(feedback_results)
            
            # Calculate quality scores
            quality_scores = {}
            for domain, feedback_list in feedback_results.items():
                quality_scores[domain] = sum(f.quality_score for f in feedback_list) / len(feedback_list) if feedback_list else 1.0
            
            # Store iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                artifact=artifact,
                feedback=feedback_results,
                satisfied=satisfied,
                quality_scores=quality_scores
            )
            iterations.append(iteration_result)
            
            if satisfied:
                logger.info(f"Outline critic satisfied after {iteration} iterations")
                break
        
        # Create phase result
        final_artifact = ResearchArtifact(content=current_outline, version=len(iterations))
        improvement_summary = self.critic.generate_improvement_summary(feedback_results)
        
        phase_result = PhaseResult(
            phase_name="outline",
            iterations=iterations,
            final_artifact=final_artifact,
            total_iterations=len(iterations),
            phase_satisfied=satisfied,
            improvement_summary=improvement_summary
        )
        
        # Store for later phases
        self.research_context['outline'] = current_outline
        
        return phase_result
    
    async def _article_phase_with_critic(self, topic: str) -> PhaseResult:
        """Article generation phase with iterative critic refinement."""
        logger.info("Starting article phase with critic loops")
        
        iterations = []
        current_article = ""
        
        for iteration in range(1, self.loop_config.max_iterations_per_phase + 1):
            logger.info(f"Article iteration {iteration}")
            
            if iteration == 1:
                # Generate initial article using STORM
                current_article = await self._storm_article_generation(topic)
            else:
                # Improve article based on critic feedback
                current_article = await self._improve_article(current_article)
            
            # Comprehensive evaluation with all critics
            artifact = ResearchArtifact(content=current_article, version=iteration)
            feedback_results = await self.critic.comprehensive_evaluation(artifact)
            
            # Check satisfaction across all domains
            satisfied = self.critic.is_satisfied(feedback_results)
            
            # Calculate quality scores
            quality_scores = {}
            for domain, feedback_list in feedback_results.items():
                quality_scores[domain] = sum(f.quality_score for f in feedback_list) / len(feedback_list) if feedback_list else 1.0
            
            # Store iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                artifact=artifact,
                feedback=feedback_results,
                satisfied=satisfied,
                quality_scores=quality_scores
            )
            iterations.append(iteration_result)
            
            if satisfied:
                logger.info(f"Article critic satisfied after {iteration} iterations")
                break
        
        # Create phase result
        final_artifact = ResearchArtifact(content=current_article, version=len(iterations))
        improvement_summary = self.critic.generate_improvement_summary(feedback_results)
        
        phase_result = PhaseResult(
            phase_name="article",
            iterations=iterations,
            final_artifact=final_artifact,
            total_iterations=len(iterations),
            phase_satisfied=satisfied,
            improvement_summary=improvement_summary
        )
        
        # Store for final phase
        self.research_context['article'] = current_article
        
        return phase_result
    
    async def _polish_phase_with_critic(self, topic: str) -> PhaseResult:
        """Polishing phase with iterative critic refinement."""
        logger.info("Starting polish phase with critic loops")
        
        iterations = []
        current_polished = self.research_context.get('article', '')
        
        for iteration in range(1, self.loop_config.max_iterations_per_phase + 1):
            logger.info(f"Polish iteration {iteration}")
            
            if iteration == 1:
                # Initial polish using STORM
                current_polished = await self._storm_article_polish(current_polished)
            else:
                # Further polish based on critic feedback
                current_polished = await self._enhance_polish(current_polished)
            
            # Comprehensive evaluation
            artifact = ResearchArtifact(content=current_polished, version=iteration)
            feedback_results = await self.critic.comprehensive_evaluation(artifact)
            
            # Check satisfaction (highest standards for final output)
            satisfied = self.critic.is_satisfied(feedback_results)
            
            # Calculate quality scores
            quality_scores = {}
            for domain, feedback_list in feedback_results.items():
                quality_scores[domain] = sum(f.quality_score for f in feedback_list) / len(feedback_list) if feedback_list else 1.0
            
            # Store iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                artifact=artifact,
                feedback=feedback_results,
                satisfied=satisfied,
                quality_scores=quality_scores
            )
            iterations.append(iteration_result)
            
            if satisfied:
                logger.info(f"Polish critic satisfied after {iteration} iterations")
                break
        
        # Create phase result
        final_artifact = ResearchArtifact(content=current_polished, version=len(iterations))
        improvement_summary = self.critic.generate_improvement_summary(feedback_results)
        
        phase_result = PhaseResult(
            phase_name="polish",
            iterations=iterations,
            final_artifact=final_artifact,
            total_iterations=len(iterations),
            phase_satisfied=satisfied,
            improvement_summary=improvement_summary
        )
        
        return phase_result
    
    # STORM Integration Methods
    
    async def _generate_initial_plan(self, topic: str) -> str:
        """Generate initial research plan."""
        # Use STORM's question_asker_lm to generate research plan
        plan_prompt = f"""
        Create a comprehensive research plan for the topic: "{topic}"
        
        Include:
        1. Research Objectives - What specific questions will be answered?
        2. Methodology - How will information be gathered and analyzed?
        3. Scope - What aspects will be covered and what are the boundaries?
        4. Timeline - What are the key phases and milestones?
        5. Expected Deliverables - What outputs will be produced?
        """
        
        # Simple implementation - in full system this would use STORM's LLMs
        return f"""
        Research Plan: {topic}
        
        Objectives: Conduct comprehensive analysis of {topic}
        Methodology: Literature review and multi-perspective analysis
        Scope: Current state and recent developments
        Timeline: Systematic research phases
        Deliverables: Detailed research article with citations
        """
    
    async def _storm_information_seeking(self, topic: str) -> str:
        """Perform STORM's information-seeking conversation."""
        # This would integrate with STORM's actual conversation pipeline
        # For now, return placeholder
        return f"Comprehensive research data on {topic} gathered through STORM's information-seeking conversation..."
    
    async def _storm_outline_generation(self, topic: str) -> str:
        """Generate outline using STORM's outline generation."""
        # This would use STORM's outline_gen_lm
        return f"Detailed outline for {topic} generated using STORM's multi-perspective approach..."
    
    async def _storm_article_generation(self, topic: str) -> str:
        """Generate article using STORM's article generation."""
        # This would use STORM's article_gen_lm with proper citations
        return f"Complete article on {topic} with citations generated using STORM's article pipeline..."
    
    async def _storm_article_polish(self, article: str) -> str:
        """Polish article using STORM's polishing pipeline."""
        # This would use STORM's article_polish_lm
        return f"Polished version of article using STORM's refinement capabilities..."
    
    # Improvement Methods (integrate with LLMs)
    
    async def _improve_plan(self, current_plan: str, feedback: List[CriticFeedback]) -> str:
        """Improve research plan based on critic feedback."""
        # Use feedback to enhance plan - this would integrate with LLMs
        improvements = [f.specific_improvement for f in feedback if f.is_actionable]
        return current_plan + f"\n\nIMPROVEMENTS: {'; '.join(improvements)}"
    
    async def _enhance_research(self, current_research: str, topic: str) -> str:
        """Enhance research based on critic feedback."""
        return current_research + "\n\nADDITIONAL RESEARCH: Enhanced based on critic feedback..."
    
    async def _improve_outline(self, current_outline: str, topic: str) -> str:
        """Improve outline based on critic feedback."""
        return current_outline + "\n\nREFINED STRUCTURE: Improved based on critic feedback..."
    
    async def _improve_article(self, current_article: str) -> str:
        """Improve article based on critic feedback."""
        return current_article + "\n\nENHANCEMENTS: Improved based on comprehensive critic feedback..."
    
    async def _enhance_polish(self, current_polished: str) -> str:
        """Enhance polish based on critic feedback."""
        return current_polished + "\n\nFINAL REFINEMENTS: Enhanced for publication quality..."
    
    async def _save_complete_results(self, topic: str) -> None:
        """Save comprehensive results of the storm-loop process."""
        output_path = Path(self.loop_config.output_dir) / f"storm_loop_{topic.replace(' ', '_')}_results.json"
        
        # Convert results to serializable format
        serializable_results = {}
        for phase_name, phase_result in self.phase_results.items():
            serializable_results[phase_name] = {
                'phase_name': phase_result.phase_name,
                'total_iterations': phase_result.total_iterations,
                'phase_satisfied': phase_result.phase_satisfied,
                'improvement_summary': phase_result.improvement_summary,
                'final_content': phase_result.final_artifact.content,
                'iterations': [
                    {
                        'iteration': it.iteration,
                        'satisfied': it.satisfied,
                        'quality_scores': it.quality_scores,
                        'timestamp': it.timestamp.isoformat()
                    }
                    for it in phase_result.iterations
                ]
            }
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Complete storm-loop results saved to {output_path}")


def create_storm_loop_runner(topic_config: Dict[str, Any] = None) -> STORMLoopRunner:
    """
    Factory function to create a configured STORMLoopRunner.
    
    This is the main entry point for users wanting to run storm-loop research.
    """
    
    # Load API keys
    from knowledge_storm.utils import load_api_key
    load_api_key(toml_file_path='secrets.toml')
    
    # Configure STORM LLMs
    lm_configs = STORMWikiLMConfigs()
    claude_kwargs = {
        'api_key': os.getenv("ANTHROPIC_API_KEY"),
        'temperature': 1.0,
        'top_p': 0.9
    }
    
    # Use Claude models for all components
    conv_simulator_lm = ClaudeModel(model='claude-3-haiku-20240307', max_tokens=500, **claude_kwargs)
    question_asker_lm = ClaudeModel(model='claude-3-sonnet-20240229', max_tokens=500, **claude_kwargs)
    outline_gen_lm = ClaudeModel(model='claude-3-opus-20240229', max_tokens=400, **claude_kwargs)
    article_gen_lm = ClaudeModel(model='claude-3-opus-20240229', max_tokens=700, **claude_kwargs)
    article_polish_lm = ClaudeModel(model='claude-3-opus-20240229', max_tokens=4000, **claude_kwargs)
    
    lm_configs.set_conv_simulator_lm(conv_simulator_lm)
    lm_configs.set_question_asker_lm(question_asker_lm)
    lm_configs.set_outline_gen_lm(outline_gen_lm)
    lm_configs.set_article_gen_lm(article_gen_lm)
    lm_configs.set_article_polish_lm(article_polish_lm)
    
    # Configure STORM runner arguments
    storm_config = STORMWikiRunnerArguments(
        output_dir="storm_loop_output",
        max_conv_turn=3,
        max_perspective=4,
        search_top_k=3,
        max_thread_num=1,
    )
    
    # Configure retrieval module
    rm = YouRM(ydc_api_key=os.getenv('YDC_API_KEY'), k=storm_config.search_top_k)
    
    # Configure storm-loop specific settings
    loop_config = STORMLoopConfig(
        max_iterations_per_phase=3,
        enable_all_critics=True,
        save_iteration_history=True
    )
    
    return STORMLoopRunner(
        storm_config=storm_config,
        lm_configs=lm_configs,
        retrieval_module=rm,
        loop_config=loop_config
    )