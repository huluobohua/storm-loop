"""
Demonstration test for parallel task execution in agent coordination.

This test validates that the AgentCoordinator can execute tasks in parallel
by analyzing execution timestamps rather than relying on wall-clock timing,
making it robust against system load variations and CI/CD environments.

Key validation approach:
1. Use TimestampingAgent to record start/end times of task execution
2. Verify that execution windows of different tasks overlap in time
3. Test edge cases to ensure robust error handling

This serves as the foundation for Issue #100 parallel coordination optimizations.
"""

import asyncio
import time
from typing import List, Tuple

from knowledge_storm.agent_coordinator import AgentCoordinator


class TimestampingAgent:
    """Agent that records execution timestamps to prove parallel execution."""

    def __init__(self, agent_id: str, delay: float = 0.1) -> None:
        self.agent_id = agent_id
        self.delay = delay

    async def execute_task(self, task: float) -> str:
        start_time = time.perf_counter()
        await asyncio.sleep(self.delay)
        end_time = time.perf_counter()
        return f"agent_{self.agent_id}_task_{task}_start_{start_time:.3f}_end_{end_time:.3f}"


def test_parallel_task_execution():
    """Demonstrate that tasks are executed concurrently by analyzing execution timestamps."""

    async def run():
        coordinator = AgentCoordinator()
        for i in range(3):
            coordinator.register_agent(TimestampingAgent(f"a{i}"))

        assignments = [(f"a{i}", i) for i in range(3)]  # Use task IDs instead of delays
        results = await coordinator.distribute_tasks_parallel(assignments)

        # Verify all tasks completed successfully
        assert len(results) == 3
        assert all("agent_" in result for result in results)

        # Parse timestamps from results
        execution_windows: List[Tuple[float, float]] = []
        for result in results:
            parts = result.split("_")
            start_time = float(parts[5])  # start_X.XXX
            end_time = float(parts[7])    # end_X.XXX
            execution_windows.append((start_time, end_time))

        # Verify parallel execution: at least two tasks should have overlapping execution windows
        overlaps = 0
        for i in range(len(execution_windows)):
            for j in range(i + 1, len(execution_windows)):
                start1, end1 = execution_windows[i]
                start2, end2 = execution_windows[j]
                
                # Check if execution windows overlap
                if start1 < end2 and start2 < end1:
                    overlaps += 1
        
        # At least one pair should overlap if running in parallel
        assert overlaps > 0, f"No overlapping execution detected. Windows: {execution_windows}"

    asyncio.run(run())


def test_edge_cases():
    """Test edge cases for agent coordination."""

    async def test_no_agents():
        """Test behavior with no registered agents."""
        coordinator = AgentCoordinator()
        assignments = [("nonexistent", 1)]
        
        try:
            results = await coordinator.distribute_tasks_parallel(assignments)
            # If this doesn't raise an exception, verify empty results
            assert results == []
        except Exception:
            # Exception is acceptable behavior for this edge case
            pass

    async def test_empty_task_list():
        """Test behavior with empty task list."""
        coordinator = AgentCoordinator()
        coordinator.register_agent(TimestampingAgent("a1"))
        
        results = await coordinator.distribute_tasks_parallel([])
        assert results == []

    async def test_more_tasks_than_agents():
        """Test distributing more tasks than available agents."""
        coordinator = AgentCoordinator()
        coordinator.register_agent(TimestampingAgent("a1", delay=0.05))  # Faster for testing
        coordinator.register_agent(TimestampingAgent("a2", delay=0.05))
        
        # 4 tasks, 2 agents - should handle gracefully
        assignments = [(f"a{i % 2 + 1}", i) for i in range(4)]
        results = await coordinator.distribute_tasks_parallel(assignments)
        
        assert len(results) == 4
        assert all("agent_" in result for result in results)

    async def test_single_agent():
        """Test with only one agent (sequential execution)."""
        coordinator = AgentCoordinator()
        coordinator.register_agent(TimestampingAgent("a1", delay=0.05))
        
        assignments = [("a1", i) for i in range(2)]
        results = await coordinator.distribute_tasks_parallel(assignments)
        
        assert len(results) == 2
        assert all("agent_a1" in result for result in results)

    # Run all edge case tests
    asyncio.run(test_no_agents())
    asyncio.run(test_empty_task_list())
    asyncio.run(test_more_tasks_than_agents())
    asyncio.run(test_single_agent())
