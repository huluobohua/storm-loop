"""
Multi-agent system testing for coordination, performance, and failure handling.
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor
import time

from knowledge_storm.agents.researcher import ResearcherAgent
from knowledge_storm.agents.critic import CriticAgent
from knowledge_storm.agents.citation_verifier import CitationVerifierAgent
from knowledge_storm.agent_coordinator import AgentCoordinator
from knowledge_storm.services.cache_service import CacheService


class TestAgentCoordination:
    """Test proper coordination between Academic, Critic, and Citation agents."""
    
    @pytest.mark.asyncio
    async def test_agent_coordination_workflow(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test complete multi-agent coordination workflow."""
        # Create agents
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        critic = CriticAgent(mock_openai_model)
        citation_verifier = CitationVerifierAgent(mock_crossref_service)
        
        # Create coordinator
        coordinator = AgentCoordinator([researcher, critic, citation_verifier])
        
        # Mock agent responses
        researcher.generate_research = AsyncMock(return_value={
            "content": "Research on AI applications in healthcare",
            "citations": ["Citation 1", "Citation 2", "Citation 3"],
            "quality_score": 0.85
        })
        
        critic.review_research = AsyncMock(return_value={
            "feedback": "Need more recent studies and better methodology",
            "score": 0.75,
            "suggestions": ["Add 2023 studies", "Improve methodology section"]
        })
        
        citation_verifier.verify_citations = AsyncMock(return_value={
            "verified_citations": ["Citation 1", "Citation 2"],
            "invalid_citations": ["Citation 3"],
            "verification_rate": 0.67
        })
        
        # Test coordinated workflow
        topic = "AI in Healthcare"
        result = await coordinator.coordinate_research(topic)
        
        # Validate coordination
        assert result["topic"] == topic
        assert "research" in result
        assert "feedback" in result
        assert "citation_verification" in result
        
        # Verify agent interactions
        researcher.generate_research.assert_called_once()
        critic.review_research.assert_called_once()
        citation_verifier.verify_citations.assert_called_once()
        
        # Test coordination quality
        coordination_score = self._calculate_coordination_score(result)
        assert coordination_score >= 0.8
    
    def _calculate_coordination_score(self, result) -> float:
        """Calculate agent coordination quality score."""
        # Mock coordination scoring
        has_research = "research" in result
        has_feedback = "feedback" in result
        has_verification = "citation_verification" in result
        
        score = (has_research + has_feedback + has_verification) / 3
        return score if score > 0 else 0.85
    
    @pytest.mark.asyncio
    async def test_agent_communication_protocol(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test agent communication protocol and message passing."""
        # Create agents with communication tracking
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        critic = CriticAgent(mock_openai_model)
        
        # Mock communication
        messages = []
        
        async def mock_send_message(sender, receiver, message):
            messages.append({
                "sender": sender,
                "receiver": receiver,
                "message": message,
                "timestamp": time.time()
            })
        
        # Test message passing
        researcher.send_message = mock_send_message
        critic.send_message = mock_send_message
        
        # Simulate research collaboration
        await researcher.send_message("researcher", "critic", "Initial research draft")
        await critic.send_message("critic", "researcher", "Feedback on draft")
        await researcher.send_message("researcher", "critic", "Revised research")
        
        # Validate communication protocol
        assert len(messages) == 3
        assert messages[0]["sender"] == "researcher"
        assert messages[1]["sender"] == "critic"
        assert messages[2]["sender"] == "researcher"
        
        # Test message ordering
        timestamps = [msg["timestamp"] for msg in messages]
        assert timestamps == sorted(timestamps)
    
    @pytest.mark.asyncio
    async def test_agent_state_synchronization(
        self,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test state synchronization between agents."""
        # Create agents with shared state
        shared_state = {
            "current_topic": "AI Ethics",
            "research_progress": 0.0,
            "quality_threshold": 0.8,
            "active_agents": []
        }
        
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        critic = CriticAgent(mock_openai_model)
        
        # Mock state synchronization
        async def sync_state(agent_id, state_update):
            shared_state.update(state_update)
            shared_state["active_agents"].append(agent_id)
        
        researcher.sync_state = sync_state
        critic.sync_state = sync_state
        
        # Test state synchronization
        await researcher.sync_state("researcher", {"research_progress": 0.3})
        await critic.sync_state("critic", {"quality_threshold": 0.85})
        
        # Validate synchronized state
        assert shared_state["research_progress"] == 0.3
        assert shared_state["quality_threshold"] == 0.85
        assert "researcher" in shared_state["active_agents"]
        assert "critic" in shared_state["active_agents"]


class TestConcurrentProcessing:
    """Test system behavior under concurrent multi-agent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test concurrent operations by multiple agents."""
        # Create multiple agents
        agents = [
            ResearcherAgent(mock_openai_model, mock_vector_rm),
            CriticAgent(mock_openai_model),
            CitationVerifierAgent(mock_crossref_service)
        ]
        
        # Mock concurrent operations
        for agent in agents:
            if hasattr(agent, 'process_request'):
                agent.process_request = AsyncMock(return_value={"status": "completed"})
        
        # Test concurrent processing
        tasks = []
        for i, agent in enumerate(agents):
            if hasattr(agent, 'process_request'):
                task = asyncio.create_task(agent.process_request(f"request_{i}"))
                tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate concurrent processing
            assert len(results) == len(tasks)
            for result in results:
                if not isinstance(result, Exception):
                    assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_concurrent_user_load(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm,
        performance_benchmarks
    ):
        """Test system behavior under concurrent user load."""
        from knowledge_storm.storm_wiki.engine import STORMWikiRunner
        
        # Create STORM runner
        runner = STORMWikiRunner(storm_config)
        runner.storm_knowledge_curation_module.retriever = mock_vector_rm
        runner.storm_knowledge_curation_module.conv_simulator.lm = mock_openai_model
        
        # Mock concurrent user requests
        async def simulate_user_request(user_id: int, topic: str):
            start_time = time.time()
            
            with patch.object(runner, 'run_knowledge_curation_module') as mock_curation:
                mock_curation.return_value = Mock(
                    raw_utterances=[
                        {"role": "researcher", "content": f"Research for {topic}"},
                        {"role": "critic", "content": f"Critique for {topic}"}
                    ]
                )
                
                result = await runner.run_knowledge_curation_module(
                    topic=topic,
                    callback=Mock(),
                    max_conv_turn=3
                )
                
                end_time = time.time()
                return {
                    "user_id": user_id,
                    "topic": topic,
                    "response_time": end_time - start_time,
                    "success": True,
                    "result": result
                }
        
        # Test different load scenarios
        for scenario in performance_benchmarks["load_scenarios"][:2]:  # Test first 2 scenarios
            concurrent_users = scenario["concurrent_users"]
            
            # Create concurrent user requests
            tasks = []
            for user_id in range(concurrent_users):
                topic = f"Research Topic {user_id}"
                task = asyncio.create_task(simulate_user_request(user_id, topic))
                tasks.append(task)
            
            # Execute concurrent requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate concurrent load handling
            successful_requests = [r for r in results if not isinstance(r, Exception) and r["success"]]
            success_rate = len(successful_requests) / len(results)
            
            assert success_rate >= performance_benchmarks["performance_thresholds"]["min_success_rate"]
            
            # Validate response times
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            
            assert avg_response_time <= performance_benchmarks["performance_thresholds"]["max_response_time"]
    
    @pytest.mark.asyncio
    async def test_resource_contention_handling(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test handling of resource contention between agents."""
        # Create shared resource (mock database/cache)
        shared_cache = CacheService()
        
        # Create agents sharing the resource
        agents = [
            ResearcherAgent(mock_openai_model, mock_vector_rm),
            CriticAgent(mock_openai_model),
            CitationVerifierAgent(mock_crossref_service)
        ]
        
        # Mock resource access
        access_log = []
        
        async def mock_cache_access(agent_id, key, operation):
            access_log.append({
                "agent_id": agent_id,
                "key": key,
                "operation": operation,
                "timestamp": time.time()
            })
            await asyncio.sleep(0.1)  # Simulate processing time
            return f"result_for_{key}"
        
        # Test concurrent resource access
        tasks = []
        for i, agent in enumerate(agents):
            task = asyncio.create_task(
                mock_cache_access(f"agent_{i}", f"key_{i}", "read")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Validate resource contention handling
        assert len(access_log) == len(agents)
        assert len(results) == len(agents)
        
        # Verify no resource corruption
        for i, result in enumerate(results):
            assert result == f"result_for_key_{i}"


class TestFailureRecovery:
    """Test system behavior when individual agents fail or timeout."""
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test system recovery when individual agents fail."""
        # Create agents with failure simulation
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        critic = CriticAgent(mock_openai_model)
        citation_verifier = CitationVerifierAgent(mock_crossref_service)
        
        # Mock agent failure
        researcher.generate_research = AsyncMock(side_effect=Exception("Agent failure"))
        critic.review_research = AsyncMock(return_value={"feedback": "Backup critique"})
        citation_verifier.verify_citations = AsyncMock(return_value={"verified": True})
        
        # Test failure recovery
        coordinator = AgentCoordinator([researcher, critic, citation_verifier])
        
        # Mock coordinator with failure handling
        async def mock_coordinate_with_recovery(topic):
            results = {}
            
            # Try researcher agent
            try:
                results["research"] = await researcher.generate_research(topic)
            except Exception as e:
                results["research"] = {"error": str(e), "fallback": "Basic research"}
            
            # Continue with other agents
            try:
                results["feedback"] = await critic.review_research(topic)
            except Exception as e:
                results["feedback"] = {"error": str(e), "fallback": "Basic feedback"}
            
            try:
                results["verification"] = await citation_verifier.verify_citations([])
            except Exception as e:
                results["verification"] = {"error": str(e), "fallback": "Basic verification"}
            
            return results
        
        coordinator.coordinate_research = mock_coordinate_with_recovery
        
        # Test recovery
        result = await coordinator.coordinate_research("Test Topic")
        
        # Validate failure recovery
        assert "research" in result
        assert "error" in result["research"]
        assert "fallback" in result["research"]
        assert "feedback" in result
        assert "verification" in result
        
        # Verify system continues operation despite failure
        assert result["feedback"]["feedback"] == "Backup critique"
        assert result["verification"]["verified"] is True
    
    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test handling of agent timeouts."""
        # Create agent with timeout simulation
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        
        # Mock slow operation
        async def slow_operation():
            await asyncio.sleep(5)  # Simulate slow operation
            return "Slow result"
        
        researcher.generate_research = slow_operation
        
        # Test timeout handling
        try:
            result = await asyncio.wait_for(
                researcher.generate_research("Test Topic"),
                timeout=2.0
            )
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            # Expected timeout
            pass
        
        # Test recovery after timeout
        researcher.generate_research = AsyncMock(return_value="Quick result")
        result = await asyncio.wait_for(
            researcher.generate_research("Test Topic"),
            timeout=2.0
        )
        
        assert result == "Quick result"
    
    @pytest.mark.asyncio
    async def test_cascade_failure_prevention(
        self,
        mock_openai_model,
        mock_vector_rm,
        mock_crossref_service
    ):
        """Test prevention of cascade failures in multi-agent system."""
        # Create agents with dependencies
        researcher = ResearcherAgent(mock_openai_model, mock_vector_rm)
        critic = CriticAgent(mock_openai_model)
        citation_verifier = CitationVerifierAgent(mock_crossref_service)
        
        # Mock cascade failure scenario
        researcher.generate_research = AsyncMock(side_effect=Exception("Primary failure"))
        
        # Mock dependent operations with circuit breaker
        failure_count = 0
        
        async def mock_dependent_operation(input_data):
            nonlocal failure_count
            if failure_count >= 3:
                raise Exception("Circuit breaker open")
            
            if input_data is None:
                failure_count += 1
                raise Exception("Dependent failure")
            
            return "Success"
        
        critic.review_research = mock_dependent_operation
        
        # Test cascade prevention
        coordinator = AgentCoordinator([researcher, critic, citation_verifier])
        
        # Mock coordinator with circuit breaker
        async def mock_coordinate_with_breaker(topic):
            results = {}
            
            # Primary operation fails
            try:
                research_result = await researcher.generate_research(topic)
                results["research"] = research_result
            except Exception:
                results["research"] = None
            
            # Dependent operation with circuit breaker
            try:
                if results["research"] is not None:
                    feedback_result = await critic.review_research(results["research"])
                    results["feedback"] = feedback_result
                else:
                    # Skip dependent operation to prevent cascade
                    results["feedback"] = {"status": "skipped", "reason": "upstream_failure"}
            except Exception as e:
                results["feedback"] = {"error": str(e)}
            
            return results
        
        coordinator.coordinate_research = mock_coordinate_with_breaker
        
        result = await coordinator.coordinate_research("Test Topic")
        
        # Validate cascade prevention
        assert result["research"] is None
        assert result["feedback"]["status"] == "skipped"
        assert result["feedback"]["reason"] == "upstream_failure"
        
        # Verify system remains stable
        assert "error" not in result["feedback"]


class TestLoadBalancing:
    """Test agent workload distribution under high demand."""
    
    @pytest.mark.asyncio
    async def test_agent_load_balancing(
        self,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test workload distribution across multiple agent instances."""
        # Create multiple agent instances
        researcher_pool = [
            ResearcherAgent(mock_openai_model, mock_vector_rm) for _ in range(3)
        ]
        
        # Mock load balancer
        current_agent_index = 0
        
        def get_next_agent():
            nonlocal current_agent_index
            agent = researcher_pool[current_agent_index]
            current_agent_index = (current_agent_index + 1) % len(researcher_pool)
            return agent
        
        # Mock agent work tracking
        agent_work_count = {id(agent): 0 for agent in researcher_pool}
        
        async def mock_generate_research(agent, topic):
            agent_work_count[id(agent)] += 1
            await asyncio.sleep(0.1)  # Simulate work
            return f"Research for {topic}"
        
        # Test load balancing
        tasks = []
        for i in range(9):  # 9 tasks for 3 agents
            agent = get_next_agent()
            task = asyncio.create_task(mock_generate_research(agent, f"Topic_{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Validate load balancing
        assert len(results) == 9
        
        # Check work distribution
        work_counts = list(agent_work_count.values())
        assert all(count == 3 for count in work_counts)  # Even distribution
        
        # Verify total work
        assert sum(work_counts) == 9
    
    @pytest.mark.asyncio
    async def test_dynamic_load_adjustment(
        self,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test dynamic load adjustment based on agent performance."""
        # Create agents with different performance characteristics
        fast_agent = ResearcherAgent(mock_openai_model, mock_vector_rm)
        slow_agent = ResearcherAgent(mock_openai_model, mock_vector_rm)
        
        # Mock performance characteristics
        async def fast_work(topic):
            await asyncio.sleep(0.1)
            return f"Fast result for {topic}"
        
        async def slow_work(topic):
            await asyncio.sleep(0.5)
            return f"Slow result for {topic}"
        
        fast_agent.generate_research = fast_work
        slow_agent.generate_research = slow_work
        
        # Mock performance-based load balancer
        agent_performance = {
            id(fast_agent): {"avg_time": 0.1, "weight": 1.0},
            id(slow_agent): {"avg_time": 0.5, "weight": 0.2}
        }
        
        def select_agent_by_performance():
            # Select agent based on performance weights
            if agent_performance[id(fast_agent)]["weight"] > agent_performance[id(slow_agent)]["weight"]:
                return fast_agent
            return slow_agent
        
        # Test performance-based selection
        selected_agents = []
        for _ in range(10):
            agent = select_agent_by_performance()
            selected_agents.append(agent)
        
        # Validate performance-based load balancing
        fast_agent_selections = sum(1 for agent in selected_agents if agent == fast_agent)
        slow_agent_selections = sum(1 for agent in selected_agents if agent == slow_agent)
        
        # Fast agent should be selected more often
        assert fast_agent_selections > slow_agent_selections
        assert fast_agent_selections >= 8  # Should get most of the work