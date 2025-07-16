"""
PRISMA Agent Coordinator: Multi-agent coordination for systematic reviews.

Handles task distribution and agent communication for PRISMA-based 
systematic review workflows within the STORM-Academic multi-agent ecosystem.
"""

import logging
from typing import Dict, List, Optional, Any

# PRISMA components
from ..modules.prisma import Paper

# Import from the same agents package
from .prisma_screener import PRISMAScreenerAgent, PRISMATask

logger = logging.getLogger(__name__)


class PRISMAAgentCoordinator:
    """
    Coordinator for PRISMA Agent operations within the multi-agent system.
    Handles task distribution and agent communication for systematic reviews.
    
    Responsibilities:
    - Task distribution to PRISMA agents
    - Agent communication coordination
    - Task lifecycle management
    - Result aggregation and reporting
    """
    
    def __init__(self, prisma_agent: Optional[PRISMAScreenerAgent] = None):
        """
        Initialize coordinator with optional PRISMA agent.
        
        Args:
            prisma_agent: Optional pre-configured PRISMA agent instance
        """
        self.prisma_agent = prisma_agent or PRISMAScreenerAgent()
        self.active_tasks = {}
        
        logger.info(f"PRISMAAgentCoordinator initialized with agent: {self.prisma_agent.agent_id}")
        
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
        logger.info(f"Distributing systematic review task: {research_question[:100]}...")
        
        # Create task specification
        task = PRISMATask(
            task_type="systematic_review_assistance",
            research_question=research_question,
            papers=papers,
            confidence_threshold=task_preferences.get('confidence_threshold', 0.8) if task_preferences else 0.8,
            generate_draft=task_preferences.get('generate_draft', False) if task_preferences else False
        )
        
        # Generate unique task ID
        task_id = f"prisma_task_{len(self.active_tasks) + 1}"
        self.active_tasks[task_id] = task
        
        try:
            logger.info(f"Executing systematic review task: {task_id}")
            results = await self.prisma_agent.execute_task(task)
            results['task_id'] = task_id
            
            logger.info(f"Systematic review task completed: {task_id}")
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
        logger.info(f"Screening batch of {len(papers)} papers")
        
        task = PRISMATask(
            task_type="screen_papers",
            papers=papers,
            include_patterns=inclusion_patterns,
            exclude_patterns=exclusion_patterns
        )
        
        return await self.prisma_agent.execute_task(task)
    
    async def build_search_strategy(self, research_question: str) -> Dict[str, Any]:
        """
        Build comprehensive search strategy for research question.
        
        Args:
            research_question: The research question to build strategy for
            
        Returns:
            Search strategy development results
        """
        logger.info(f"Building search strategy for: {research_question[:100]}...")
        
        task = PRISMATask(
            task_type="build_strategy",
            research_question=research_question
        )
        
        return await self.prisma_agent.execute_task(task)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of coordinated PRISMA agent.
        
        Returns:
            Agent status and performance information
        """
        return {
            'coordinator_info': {
                'active_tasks': len(self.active_tasks),
                'task_ids': list(self.active_tasks.keys())
            },
            'agent_status': self.prisma_agent.get_status(),
            'agent_capabilities': self.prisma_agent.get_capabilities_summary()
        }
    
    def get_task_history(self) -> Dict[str, Any]:
        """
        Get history of coordinated tasks.
        
        Returns:
            Task history and execution summary
        """
        return {
            'total_tasks_coordinated': len(self.active_tasks),
            'active_tasks': self.active_tasks,
            'agent_performance': self.prisma_agent.screening_stats
        }
    
    async def coordinate_multi_step_review(self,
                                         research_question: str,
                                         papers: Optional[List[Paper]] = None) -> Dict[str, Any]:
        """
        Coordinate a complete multi-step systematic review workflow.
        
        Args:
            research_question: The research question
            papers: Optional papers to include in review
            
        Returns:
            Complete systematic review results
        """
        logger.info(f"Coordinating multi-step review: {research_question[:100]}...")
        
        results = {
            'research_question': research_question,
            'steps_completed': [],
            'overall_success': True
        }
        
        try:
            # Step 1: Build search strategy
            strategy_result = await self.build_search_strategy(research_question)
            results['steps_completed'].append('search_strategy')
            results['search_strategy'] = strategy_result
            
            # Step 2: Screen papers (if provided)
            if papers:
                screening_result = await self.screen_papers_batch(papers)
                results['steps_completed'].append('paper_screening')
                results['screening'] = screening_result
            
            # Step 3: Complete systematic review assistance
            review_result = await self.distribute_systematic_review_task(
                research_question, papers, {'generate_draft': True}
            )
            results['steps_completed'].append('systematic_review')
            results['systematic_review'] = review_result
            
            logger.info("Multi-step review coordination completed successfully")
            
        except Exception as e:
            logger.error(f"Multi-step review coordination failed: {e}")
            results['overall_success'] = False
            results['error'] = str(e)
        
        return results


# Export classes
__all__ = ['PRISMAAgentCoordinator']