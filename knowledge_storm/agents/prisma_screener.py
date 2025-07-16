"""
PRISMAScreenerAgent: Multi-agent wrapper for PRISMA Assistant systematic review screening.

Integrates PRISMA Assistant into the STORM-Academic multi-agent ecosystem,
providing specialized systematic review capabilities with 80/20 methodology.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Base agent infrastructure
from .base_agent import BaseAgent, AgentCapability

# PRISMA Assistant core - refactored modules
from ..modules.prisma import (
    Paper,
    SearchStrategy,
    ScreeningResult,
    PRISMAScreener
)
from ..modules.prisma_assistant_refactored import PRISMAAssistant

# Check integration availability
try:
    from ..services.citation_verifier import CitationVerifier
    VERIFY_INTEGRATION_AVAILABLE = True
except ImportError:
    VERIFY_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PRISMATask:
    """Task specification for PRISMA screening operations."""
    task_type: str  # 'screen_papers', 'build_strategy', 'generate_draft'
    research_question: Optional[str] = None
    papers: Optional[List[Paper]] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    confidence_threshold: float = 0.8
    generate_draft: bool = False


class PRISMAScreenerAgent(BaseAgent):
    """
    Specialized agent for systematic review screening using PRISMA methodology.
    
    Capabilities:
    - Automated paper screening with 80/20 methodology
    - Search strategy development
    - PRISMA 2020 compliance checking
    - Zero draft generation for systematic reviews
    - Integration with VERIFY system for enhanced validation
    """
    
    def __init__(self, 
                 agent_id: str = "prisma_screener",
                 name: str = "PRISMA Screener Agent",
                 description: str = "Systematic review screening with 80/20 methodology"):
        
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="paper_screening",
                description="Automated screening of research papers using PRISMA methodology",
                input_types=["List[Paper]", "SearchStrategy"],
                output_types=["ScreeningResults"]
            ),
            AgentCapability(
                name="search_strategy",
                description="Development of comprehensive search strategies with PICO framework", 
                input_types=["str"],  # research question
                output_types=["SearchStrategy"]
            ),
            AgentCapability(
                name="systematic_review_assistance",
                description="Complete systematic review workflow assistance",
                input_types=["str", "List[Paper]"],
                output_types=["Dict[str, Any]"]
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities
        )
        
        # Initialize PRISMA components
        self.prisma_assistant = PRISMAAssistant()
        self.prisma_screener = PRISMAScreener()
        
        # Track performance metrics
        self.screening_stats = {
            'total_papers_processed': 0,
            'automation_rate_average': 0.0,
            'tasks_completed': 0
        }
        
    async def execute_task(self, task: PRISMATask) -> Dict[str, Any]:
        """Execute a PRISMA-related task."""
        logger.info(f"PRISMAScreenerAgent executing task: {task.task_type}")
        
        try:
            if task.task_type == "screen_papers":
                return await self._screen_papers(task)
            elif task.task_type == "build_strategy":
                return await self._build_search_strategy(task)
            elif task.task_type == "systematic_review_assistance":
                return await self._assist_systematic_review(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.error(f"PRISMAScreenerAgent task failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }
    
    async def _screen_papers(self, task: PRISMATask) -> Dict[str, Any]:
        """Screen papers using PRISMA 80/20 methodology."""
        if not task.papers:
            raise ValueError("No papers provided for screening")
        
        # Configure screener with task parameters
        screener = PRISMAScreener(
            include_patterns=task.include_patterns or [],
            exclude_patterns=task.exclude_patterns or [],
            threshold=task.confidence_threshold
        )
        
        # Perform screening
        screening_results = await screener.screen_papers(task.papers)
        
        # Update stats
        self._update_screening_stats(screening_results)
        
        return {
            'success': True,
            'task_type': 'screen_papers',
            'screening_results': screening_results,
            'papers_processed': len(task.papers),
            'agent_performance': self.screening_stats,
            'agent_id': self.agent_id
        }
    
    async def _build_search_strategy(self, task: PRISMATask) -> Dict[str, Any]:
        """Build comprehensive search strategy from research question."""
        if not task.research_question:
            raise ValueError("No research question provided")
        
        # Use PRISMA assistant to build strategy
        search_strategy = self.prisma_assistant.search_builder.build_search_strategy(
            task.research_question
        )
        
        return {
            'success': True,
            'task_type': 'build_strategy',
            'search_strategy': search_strategy,
            'pico_elements': search_strategy.pico_elements,
            'database_queries': search_strategy.search_queries,
            'criteria_count': {
                'inclusion': len(search_strategy.inclusion_criteria),
                'exclusion': len(search_strategy.exclusion_criteria)
            },
            'agent_id': self.agent_id
        }
    
    async def _assist_systematic_review(self, task: PRISMATask) -> Dict[str, Any]:
        """Complete systematic review assistance workflow."""
        if not task.research_question:
            raise ValueError("No research question provided")
        
        # Run complete PRISMA assistance
        assistance_results = await self.prisma_assistant.assist_systematic_review(
            research_question=task.research_question,
            papers=task.papers,
            generate_draft=task.generate_draft
        )
        
        # Update stats if papers were processed
        if task.papers:
            self._update_screening_stats(assistance_results.get('screening_results', {}))
        
        return {
            'success': True,
            'task_type': 'systematic_review_assistance',
            'assistance_results': assistance_results,
            'time_saved_hours': assistance_results.get('time_saved_hours', 0),
            'papers_processed': assistance_results.get('papers_processed', 0),
            'integration_status': assistance_results.get('integration_status', {}),
            'agent_id': self.agent_id
        }
    
    def _update_screening_stats(self, screening_results: Dict[str, Any]):
        """Update agent performance statistics."""
        if not screening_results or 'performance_metrics' not in screening_results:
            return
            
        metrics = screening_results['performance_metrics']
        self.screening_stats['tasks_completed'] += 1
        self.screening_stats['total_papers_processed'] += metrics.get('total_papers', 0)
        
        # Update running average of automation rate
        current_rate = metrics.get('automation_rate', 0)
        task_count = self.screening_stats['tasks_completed']
        current_avg = self.screening_stats['automation_rate_average']
        
        # Calculate new average
        self.screening_stats['automation_rate_average'] = (
            (current_avg * (task_count - 1) + current_rate) / task_count
        )
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get summary of agent capabilities and current performance."""
        return {
            'agent_info': {
                'id': self.agent_id,
                'name': self.name,
                'description': self.description,
                'type': 'systematic_review_specialist'
            },
            'capabilities': [cap.name for cap in self.capabilities],
            'performance_stats': self.screening_stats,
            'integration_status': {
                'verify_system': VERIFY_INTEGRATION_AVAILABLE,
                'prisma_core': True,
                'multi_agent_ready': True
            },
            'methodology': {
                'name': '80/20 PRISMA Screening',
                'target_automation': '60-80%',
                'confidence_threshold': 'Configurable (default: 0.8)',
                'compliance': 'PRISMA 2020 guidelines'
            }
        }


class PRISMAAgentCoordinator:
    """
    Coordinator for PRISMA Agent operations within the multi-agent system.
    Handles task distribution and agent communication for systematic reviews.
    """
    
    def __init__(self, prisma_agent: Optional[PRISMAScreenerAgent] = None):
        self.prisma_agent = prisma_agent or PRISMAScreenerAgent()
        self.active_tasks = {}
        
    async def distribute_systematic_review_task(self, 
                                              research_question: str,
                                              papers: Optional[List[Paper]] = None,
                                              task_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Distribute systematic review task to PRISMA agent.
        
        Args:
            research_question: The research question for systematic review
            papers: Optional list of papers to screen
            task_preferences: Optional preferences for task execution
            
        Returns:
            Task execution results from PRISMA agent
        """
        # Create task specification
        task = PRISMATask(
            task_type="systematic_review_assistance",
            research_question=research_question,
            papers=papers,
            confidence_threshold=task_preferences.get('confidence_threshold', 0.8) if task_preferences else 0.8,
            generate_draft=task_preferences.get('generate_draft', False) if task_preferences else False
        )
        
        # Execute task
        task_id = f"prisma_task_{len(self.active_tasks) + 1}"
        self.active_tasks[task_id] = task
        
        try:
            results = await self.prisma_agent.execute_task(task)
            results['task_id'] = task_id
            return results
            
        except Exception as e:
            logger.error(f"Systematic review task failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id,
                'agent_id': self.prisma_agent.agent_id
            }
    
    async def screen_papers_batch(self, 
                                papers: List[Paper],
                                inclusion_patterns: Optional[List[str]] = None,
                                exclusion_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Screen a batch of papers using PRISMA methodology.
        
        Args:
            papers: List of papers to screen
            inclusion_patterns: Optional patterns for inclusion
            exclusion_patterns: Optional patterns for exclusion
            
        Returns:
            Screening results
        """
        task = PRISMATask(
            task_type="screen_papers",
            papers=papers,
            include_patterns=inclusion_patterns,
            exclude_patterns=exclusion_patterns
        )
        
        return await self.prisma_agent.execute_task(task)


# Export main classes
__all__ = [
    'PRISMAScreenerAgent',
    'PRISMATask', 
    'PRISMAAgentCoordinator'
]