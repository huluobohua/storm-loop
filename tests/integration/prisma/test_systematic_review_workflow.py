"""
Integration tests for SystematicReviewWorkflow.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from knowledge_storm.workflows.systematic_review import SystematicReviewWorkflow
from knowledge_storm.modules.prisma.core import Paper


class TestSystematicReviewWorkflow:
    """Integration test suite for SystematicReviewWorkflow."""
    
    def create_test_papers(self):
        """Helper method to create test papers."""
        return [
            Paper(
                id="paper_1",
                title="Randomized controlled trial of cognitive behavioral therapy for depression",
                abstract="This RCT evaluated CBT effectiveness in 150 adults with major depression over 12 weeks",
                authors=["Smith, J.", "Johnson, A."],
                year=2023,
                journal="Journal of Clinical Psychology",
                study_type="randomized_controlled_trial"
            ),
            Paper(
                id="paper_2",
                title="Effects of antidepressants in mouse models of depression",
                abstract="This study examined antidepressant effects in 40 mice using forced swim test",
                authors=["Brown, K."],
                year=2023,
                journal="Animal Behavior Research"
            ),
            Paper(
                id="paper_3",
                title="Systematic review of psychotherapy for depression",
                abstract="This systematic review analyzed 30 studies of psychotherapy interventions for depression",
                authors=["Williams, R."],
                year=2023,
                journal="Psychological Medicine"
            ),
            Paper(
                id="paper_4",
                title="Mindfulness-based intervention for depression: a pilot study",
                abstract="This pilot study evaluated mindfulness intervention in 25 adults with depression",
                authors=["Davis, M."],
                year=2023,
                journal="Mindfulness Research"
            ),
            Paper(
                id="paper_5",
                title="Case report: Treatment-resistant depression",
                abstract="We report a case of treatment-resistant depression in a 35-year-old patient",
                authors=["Taylor, S."],
                year=2023,
                journal="Case Reports in Psychiatry"
            )
        ]
    
    def test_workflow_initialization(self):
        """Test SystematicReviewWorkflow initialization."""
        workflow = SystematicReviewWorkflow()
        
        assert workflow is not None
        assert hasattr(workflow, 'conduct_systematic_review')
        assert hasattr(workflow, 'prisma_assistant')
        assert hasattr(workflow, 'progress_tracker')
        assert hasattr(workflow, 'agent_coordinator')
    
    @pytest.mark.asyncio
    async def test_conduct_systematic_review_complete_workflow(self):
        """Test complete systematic review workflow."""
        workflow = SystematicReviewWorkflow()
        
        # Mock the paper retrieval to avoid external dependencies
        papers = self.create_test_papers()
        
        config = {
            "research_question": "What is the effectiveness of psychotherapy for depression in adults?",
            "databases": ["pubmed", "embase", "psycinfo"],
            "date_range": (2010, 2023),
            "study_types": ["randomized_controlled_trial", "controlled_trial"],
            "generate_report": True
        }
        
        # Mock external dependencies
        with patch.object(workflow, '_retrieve_papers', return_value=papers):
            result = await workflow.conduct_systematic_review(config)
        
        # Validate workflow results
        assert isinstance(result, dict)
        assert 'search_strategy' in result
        assert 'screening_results' in result
        assert 'full_text_results' in result
        assert 'data_extraction' in result
        assert 'final_report' in result
        assert 'workflow_metadata' in result
        
        # Check search strategy
        search_strategy = result['search_strategy']
        assert hasattr(search_strategy, 'research_question')
        assert search_strategy.research_question == config['research_question']
        assert hasattr(search_strategy, 'pico_elements')
        assert hasattr(search_strategy, 'search_queries')
        
        # Check screening results
        screening_results = result['screening_results']
        assert 'definitely_exclude' in screening_results
        assert 'definitely_include' in screening_results
        assert 'needs_human_review' in screening_results
        
        # Check workflow metadata
        metadata = result['workflow_metadata']
        assert 'total_papers_screened' in metadata
        assert 'automation_rate' in metadata
        assert 'time_saved_hours' in metadata
        assert 'workflow_steps_completed' in metadata
    
    @pytest.mark.asyncio
    async def test_systematic_review_with_minimal_config(self):
        """Test systematic review with minimal configuration."""
        workflow = SystematicReviewWorkflow()
        
        config = {
            "research_question": "What is the effectiveness of exercise for depression?"
        }
        
        # Mock paper retrieval
        with patch.object(workflow, '_retrieve_papers', return_value=self.create_test_papers()):
            result = await workflow.conduct_systematic_review(config)
        
        # Should work with minimal config
        assert isinstance(result, dict)
        assert 'search_strategy' in result
        assert 'screening_results' in result
        assert result['search_strategy'].research_question == config['research_question']
    
    @pytest.mark.asyncio
    async def test_systematic_review_with_provided_papers(self):
        """Test systematic review with pre-provided papers."""
        workflow = SystematicReviewWorkflow()
        papers = self.create_test_papers()
        
        config = {
            "research_question": "What is the effectiveness of CBT for depression?",
            "papers": papers  # Pre-provided papers
        }
        
        result = await workflow.conduct_systematic_review(config)
        
        # Should use provided papers
        assert isinstance(result, dict)
        assert 'screening_results' in result
        
        # Check that all papers were processed
        screening_results = result['screening_results']
        total_processed = (len(screening_results['definitely_exclude']) + 
                          len(screening_results['definitely_include']) + 
                          len(screening_results['needs_human_review']))
        assert total_processed == len(papers)
    
    @pytest.mark.asyncio
    async def test_workflow_progress_tracking(self):
        """Test that workflow tracks progress correctly."""
        workflow = SystematicReviewWorkflow()
        
        config = {
            "research_question": "What is the effectiveness of medication for anxiety?",
            "track_progress": True
        }
        
        # Mock paper retrieval
        with patch.object(workflow, '_retrieve_papers', return_value=self.create_test_papers()):
            result = await workflow.conduct_systematic_review(config)
        
        # Check progress tracking
        assert 'workflow_metadata' in result
        metadata = result['workflow_metadata']
        assert 'workflow_steps_completed' in metadata
        assert 'step_durations' in metadata
        assert 'total_workflow_time' in metadata
        
        # Should have completed all major steps
        steps_completed = metadata['workflow_steps_completed']
        expected_steps = [
            'search_strategy_development',
            'paper_screening',
            'full_text_review',
            'data_extraction',
            'report_generation'
        ]
        
        for step in expected_steps:
            assert step in steps_completed
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling."""
        workflow = SystematicReviewWorkflow()
        
        # Test with invalid config
        config = {
            "research_question": ""  # Empty research question
        }
        
        with pytest.raises(ValueError, match="Research question cannot be empty"):
            await workflow.conduct_systematic_review(config)
    
    @pytest.mark.asyncio
    async def test_workflow_with_agent_coordination(self):
        """Test workflow with agent coordination."""
        workflow = SystematicReviewWorkflow()
        
        config = {
            "research_question": "What is the effectiveness of therapy for PTSD?",
            "use_agent_coordination": True
        }
        
        # Mock agent coordinator
        mock_coordinator = MagicMock()
        mock_coordinator.coordinate_screening = AsyncMock(return_value={
            'definitely_exclude': [],
            'definitely_include': self.create_test_papers()[:2],
            'needs_human_review': self.create_test_papers()[2:],
            'performance_metrics': {'automation_rate': 0.8}
        })
        
        with patch.object(workflow, 'agent_coordinator', mock_coordinator):
            with patch.object(workflow, '_retrieve_papers', return_value=self.create_test_papers()):
                result = await workflow.conduct_systematic_review(config)
        
        # Should use agent coordination
        assert isinstance(result, dict)
        assert 'screening_results' in result
        mock_coordinator.coordinate_screening.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_report_generation(self):
        """Test workflow report generation."""
        workflow = SystematicReviewWorkflow()
        
        config = {
            "research_question": "What is the effectiveness of meditation for stress?",
            "generate_report": True,
            "report_format": "full"
        }
        
        with patch.object(workflow, '_retrieve_papers', return_value=self.create_test_papers()):
            result = await workflow.conduct_systematic_review(config)
        
        # Should generate comprehensive report
        assert 'final_report' in result
        final_report = result['final_report']
        
        assert 'abstract' in final_report
        assert 'methods' in final_report
        assert 'results' in final_report
        assert 'discussion' in final_report
        
        # Report sections should be substantial
        assert len(final_report['abstract']) > 100
        assert len(final_report['methods']) > 200
        assert len(final_report['results']) > 150
    
    @pytest.mark.asyncio
    async def test_workflow_automation_metrics(self):
        """Test workflow automation metrics calculation."""
        workflow = SystematicReviewWorkflow()
        papers = self.create_test_papers()
        
        config = {
            "research_question": "What is the effectiveness of exercise for mental health?",
            "papers": papers
        }
        
        result = await workflow.conduct_systematic_review(config)
        
        # Check automation metrics
        assert 'workflow_metadata' in result
        metadata = result['workflow_metadata']
        
        assert 'automation_rate' in metadata
        assert 'time_saved_hours' in metadata
        assert 'efficiency_score' in metadata
        
        # Automation rate should be reasonable
        assert 0.0 <= metadata['automation_rate'] <= 1.0
        assert metadata['time_saved_hours'] > 0
        assert 0.0 <= metadata['efficiency_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_workflow_with_different_study_types(self):
        """Test workflow handling different study types."""
        workflow = SystematicReviewWorkflow()
        
        # Mix of different study types
        papers = self.create_test_papers()
        
        config = {
            "research_question": "What is the effectiveness of interventions for anxiety?",
            "study_types": ["randomized_controlled_trial", "cohort_study"],
            "papers": papers
        }
        
        result = await workflow.conduct_systematic_review(config)
        
        # Should handle different study types appropriately
        assert isinstance(result, dict)
        screening_results = result['screening_results']
        
        # Should include appropriate study types
        included_papers = screening_results['definitely_include']
        review_papers = screening_results['needs_human_review']
        
        # RCT should be included or reviewed
        all_considered = included_papers + review_papers
        titles = [p.title for p in all_considered]
        assert any("randomized controlled trial" in title.lower() for title in titles)
    
    @pytest.mark.asyncio
    async def test_workflow_performance_optimization(self):
        """Test workflow performance with larger datasets."""
        workflow = SystematicReviewWorkflow()
        
        # Create larger dataset
        papers = []
        for i in range(20):
            papers.append(Paper(
                id=f"paper_{i}",
                title=f"Study {i}: Research on topic {i}",
                abstract=f"This study examined topic {i} in a controlled setting",
                authors=[f"Author {i}"],
                year=2023,
                journal="Test Journal"
            ))
        
        config = {
            "research_question": "What is the effectiveness of various interventions?",
            "papers": papers,
            "optimize_performance": True
        }
        
        import time
        start_time = time.time()
        
        result = await workflow.conduct_systematic_review(config)
        
        end_time = time.time()
        workflow_time = end_time - start_time
        
        # Should complete in reasonable time
        assert workflow_time < 30  # Should complete within 30 seconds
        
        # Should process all papers
        assert isinstance(result, dict)
        metadata = result['workflow_metadata']
        assert metadata['total_papers_screened'] == len(papers)
    
    @pytest.mark.asyncio
    async def test_workflow_concurrent_processing(self):
        """Test workflow can handle concurrent processing."""
        import asyncio
        
        workflow = SystematicReviewWorkflow()
        
        # Create multiple workflow instances
        configs = [
            {"research_question": "What is the effectiveness of therapy A?"},
            {"research_question": "What is the effectiveness of therapy B?"},
            {"research_question": "What is the effectiveness of therapy C?"}
        ]
        
        # Mock paper retrieval for all instances
        with patch.object(workflow, '_retrieve_papers', return_value=self.create_test_papers()[:3]):
            # Run workflows concurrently
            tasks = [workflow.conduct_systematic_review(config) for config in configs]
            results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert 'search_strategy' in result
            assert 'screening_results' in result


if __name__ == "__main__":
    pytest.main([__file__])
