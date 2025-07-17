"""
Integration tests for PRISMAScreenerAgent.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from knowledge_storm.agents.prisma_screener import PRISMAScreenerAgent, PRISMATask
from knowledge_storm.modules.prisma.core import Paper, SearchStrategy


class TestPRISMAScreenerAgent:
    """Integration test suite for PRISMAScreenerAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = PRISMAScreenerAgent()
    
    def create_test_papers(self):
        """Helper method to create test papers."""
        return [
            Paper(
                id="paper_1",
                title="Randomized controlled trial of medication X",
                abstract="This double-blind randomized controlled trial evaluated medication X in 200 adult patients",
                authors=["Author One", "Author Two"],
                year=2023,
                journal="Test Medical Journal",
                study_type="randomized_controlled_trial"
            ),
            Paper(
                id="paper_2",
                title="Animal study of drug Y effects",
                abstract="This study examined the effects of drug Y in laboratory mice over 12 weeks",
                authors=["Author Three"],
                year=2023,
                journal="Animal Research Journal"
            ),
            Paper(
                id="paper_3",
                title="Systematic review of intervention Z",
                abstract="This systematic review and meta-analysis examined intervention Z across 15 studies",
                authors=["Author Four", "Author Five"],
                year=2023,
                journal="Review Journal"
            )
        ]
    
    def test_agent_initialization(self):
        """Test PRISMAScreenerAgent initialization."""
        agent = PRISMAScreenerAgent()
        
        assert agent.name == "PRISMA Screener Agent"
        assert agent.description == "Automated paper screening for systematic reviews"
        assert len(agent.capabilities) == 3
        
        # Check capabilities
        capability_names = [cap.name for cap in agent.capabilities]
        assert "paper_screening" in capability_names
        assert "search_strategy" in capability_names
        assert "systematic_review_assistance" in capability_names
    
    def test_agent_capabilities_structure(self):
        """Test that agent capabilities are properly structured."""
        agent = PRISMAScreenerAgent()
        
        for capability in agent.capabilities:
            assert hasattr(capability, 'name')
            assert hasattr(capability, 'description')
            assert isinstance(capability.name, str)
            assert isinstance(capability.description, str)
            assert len(capability.name) > 0
            assert len(capability.description) > 0
    
    @pytest.mark.asyncio
    async def test_paper_screening_capability(self):
        """Test the paper screening capability."""
        agent = PRISMAScreenerAgent()
        papers = self.create_test_papers()
        
        # Create screening task
        task = PRISMATask(
            task_type="paper_screening",
            papers=papers,
            search_strategy=SearchStrategy(
                research_question="What is the effectiveness of medication X?",
                pico_elements={
                    'population': ['adults'],
                    'intervention': ['medication X'],
                    'outcome': ['effectiveness']
                },
                search_queries={'pubmed': 'medication X AND adults'},
                inclusion_criteria=['Adults', 'RCTs'],
                exclusion_criteria=['Animal studies', 'Reviews']
            )
        )
        
        # Execute screening
        result = await agent.execute_task(task)
        
        assert isinstance(result, dict)
        assert 'task_type' in result
        assert result['task_type'] == 'paper_screening'
        assert 'screening_results' in result
        assert 'performance_metrics' in result
        
        # Check screening results structure
        screening_results = result['screening_results']
        assert 'definitely_exclude' in screening_results
        assert 'definitely_include' in screening_results
        assert 'needs_human_review' in screening_results
        
        # Check performance metrics
        metrics = result['performance_metrics']
        assert 'total_papers' in metrics
        assert 'automation_rate' in metrics
        assert metrics['total_papers'] == len(papers)
    
    @pytest.mark.asyncio
    async def test_search_strategy_capability(self):
        """Test the search strategy capability."""
        agent = PRISMAScreenerAgent()
        
        # Create search strategy task
        task = PRISMATask(
            task_type="search_strategy",
            research_question="What is the effectiveness of exercise therapy in adults with arthritis?"
        )
        
        # Execute search strategy building
        result = await agent.execute_task(task)
        
        assert isinstance(result, dict)
        assert 'task_type' in result
        assert result['task_type'] == 'search_strategy'
        assert 'search_strategy' in result
        
        # Check search strategy structure
        strategy = result['search_strategy']
        assert hasattr(strategy, 'research_question')
        assert hasattr(strategy, 'pico_elements')
        assert hasattr(strategy, 'search_queries')
        assert hasattr(strategy, 'inclusion_criteria')
        assert hasattr(strategy, 'exclusion_criteria')
        
        # Check PICO elements
        pico = strategy.pico_elements
        assert 'population' in pico
        assert 'intervention' in pico
        assert 'outcome' in pico
    
    @pytest.mark.asyncio
    async def test_systematic_review_assistance_capability(self):
        """Test the systematic review assistance capability."""
        agent = PRISMAScreenerAgent()
        
        # Create systematic review task
        task = PRISMATask(
            task_type="systematic_review_assistance",
            research_question="What is the effectiveness of cognitive behavioral therapy for depression?",
            papers=self.create_test_papers()
        )
        
        # Execute systematic review assistance
        result = await agent.execute_task(task)
        
        assert isinstance(result, dict)
        assert 'task_type' in result
        assert result['task_type'] == 'systematic_review_assistance'
        assert 'search_strategy' in result
        assert 'screening_results' in result
        assert 'time_saved_hours' in result
        
        # Check that all components are present
        assert result['search_strategy'] is not None
        assert result['screening_results'] is not None
        assert isinstance(result['time_saved_hours'], (int, float))
    
    @pytest.mark.asyncio
    async def test_invalid_task_type(self):
        """Test handling of invalid task types."""
        agent = PRISMAScreenerAgent()
        
        # Create invalid task
        task = PRISMATask(
            task_type="invalid_task_type",
            research_question="Test question"
        )
        
        # Should handle gracefully
        with pytest.raises(ValueError, match="Unsupported task type"):
            await agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        agent = PRISMAScreenerAgent()
        
        # Create task missing required parameters
        task = PRISMATask(
            task_type="paper_screening"
            # Missing papers and search_strategy
        )
        
        # Should handle gracefully
        with pytest.raises(ValueError, match="Missing required parameters"):
            await agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self):
        """Test that agent tracks performance metrics."""
        agent = PRISMAScreenerAgent()
        papers = self.create_test_papers()
        
        # Execute multiple tasks
        for i in range(3):
            task = PRISMATask(
                task_type="paper_screening",
                papers=papers,
                search_strategy=SearchStrategy(
                    research_question=f"Research question {i}",
                    pico_elements={'population': ['adults']},
                    search_queries={'pubmed': f'query {i}'},
                    inclusion_criteria=['Adults'],
                    exclusion_criteria=['Animals']
                )
            )
            
            result = await agent.execute_task(task)
            assert 'performance_metrics' in result
        
        # Check that agent tracked performance
        assert hasattr(agent, 'performance_metrics')
        assert agent.performance_metrics['total_papers_processed'] >= len(papers) * 3
        assert agent.performance_metrics['total_screening_time'] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test that agent can handle concurrent tasks."""
        import asyncio
        
        agent = PRISMAScreenerAgent()
        papers = self.create_test_papers()
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = PRISMATask(
                task_type="search_strategy",
                research_question=f"Research question {i}"
            )
            tasks.append(agent.execute_task(task))
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # All tasks should complete successfully
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert 'task_type' in result
            assert result['task_type'] == 'search_strategy'
    
    def test_agent_registry_integration(self):
        """Test integration with agent registry."""
        from knowledge_storm.agents.base_agent import AgentRegistry
        
        # Create agent and register
        agent = PRISMAScreenerAgent()
        registry = AgentRegistry()
        registry.register_agent(agent)
        
        # Check that agent is registered
        assert agent.agent_id in registry.agents
        
        # Check that capabilities are discoverable
        screening_agents = registry.find_agents_by_capability("paper_screening")
        assert len(screening_agents) > 0
        assert agent.agent_id in [a.agent_id for a in screening_agents]
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling."""
        agent = PRISMAScreenerAgent()
        
        # Create task with invalid data
        task = PRISMATask(
            task_type="paper_screening",
            papers=None,  # Invalid papers
            search_strategy=SearchStrategy(
                research_question="Test",
                pico_elements={'population': ['adults']},
                search_queries={'pubmed': 'test'},
                inclusion_criteria=['Adults'],
                exclusion_criteria=['Animals']
            )
        )
        
        # Should handle error gracefully
        with pytest.raises(ValueError):
            await agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_agent_real_world_scenario(self):
        """Test agent with a realistic systematic review scenario."""
        agent = PRISMAScreenerAgent()
        
        # Create realistic papers
        papers = [
            Paper(
                id="paper_diabetes_1",
                title="Efficacy of metformin in type 2 diabetes: a randomized controlled trial",
                abstract="This double-blind randomized controlled trial evaluated metformin effectiveness in 300 adults with type 2 diabetes over 12 months. Primary outcome was HbA1c reduction.",
                authors=["Smith, J.", "Johnson, A."],
                year=2023,
                journal="Diabetes Care",
                study_type="randomized_controlled_trial"
            ),
            Paper(
                id="paper_diabetes_2",
                title="Effects of insulin on glucose metabolism in diabetic mice",
                abstract="This study examined insulin's effects on glucose metabolism in 50 diabetic mice over 8 weeks using standard laboratory protocols.",
                authors=["Brown, K."],
                year=2023,
                journal="Animal Diabetes Research"
            ),
            Paper(
                id="paper_diabetes_3",
                title="Systematic review of diabetes medications",
                abstract="This systematic review analyzed 45 studies examining various diabetes medications and their effectiveness in adults.",
                authors=["Williams, R.", "Davis, M."],
                year=2023,
                journal="Diabetes Reviews"
            ),
            Paper(
                id="paper_diabetes_4",
                title="Lifestyle interventions for diabetes management: a cohort study",
                abstract="This prospective cohort study followed 500 adults with diabetes for 2 years to evaluate lifestyle interventions.",
                authors=["Taylor, S."],
                year=2023,
                journal="Public Health Diabetes"
            )
        ]
        
        # Create realistic search strategy
        search_strategy = SearchStrategy(
            research_question="What is the effectiveness of pharmacological interventions for type 2 diabetes in adults?",
            pico_elements={
                'population': ['adults', 'type 2 diabetes', 'diabetic patients'],
                'intervention': ['metformin', 'insulin', 'pharmacological interventions'],
                'comparison': ['placebo', 'standard care'],
                'outcome': ['HbA1c reduction', 'blood glucose control', 'glycemic control']
            },
            search_queries={
                'pubmed': 'type 2 diabetes AND adults AND (metformin OR insulin) AND (randomized OR controlled)',
                'embase': 'type 2 diabetes AND adult AND pharmacological intervention',
                'cochrane': 'diabetes AND medication AND adult'
            },
            inclusion_criteria=[
                'Adults aged 18+ with type 2 diabetes',
                'Randomized controlled trials',
                'Pharmacological interventions',
                'English language publications'
            ],
            exclusion_criteria=[
                'Animal studies',
                'Type 1 diabetes',
                'Pediatric populations',
                'Case reports',
                'Systematic reviews'
            ]
        )
        
        # Execute screening
        task = PRISMATask(
            task_type="paper_screening",
            papers=papers,
            search_strategy=search_strategy
        )
        
        result = await agent.execute_task(task)
        
        # Validate results
        assert isinstance(result, dict)
        assert 'screening_results' in result
        
        screening_results = result['screening_results']
        
        # Should exclude animal study and systematic review
        excluded_papers = screening_results['definitely_exclude']
        excluded_titles = [p.title for p in excluded_papers]
        assert any("mice" in title for title in excluded_titles)
        assert any("systematic review" in title.lower() for title in excluded_titles)
        
        # Should include or consider the RCT
        included_papers = screening_results['definitely_include']
        review_papers = screening_results['needs_human_review']
        all_considered = included_papers + review_papers
        considered_titles = [p.title for p in all_considered]
        assert any("randomized controlled trial" in title.lower() for title in considered_titles)
        
        # Check automation rate
        metrics = result['performance_metrics']
        assert metrics['automation_rate'] >= 0.5  # Should automate at least 50%


if __name__ == "__main__":
    pytest.main([__file__])
