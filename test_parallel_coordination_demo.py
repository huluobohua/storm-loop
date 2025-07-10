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
from dataclasses import dataclass
from typing import List, Tuple, Union

import pytest
from knowledge_storm.agent_coordinator import AgentCoordinator, AgentNotFoundError


@dataclass
class AgentResult:
    """Structured result from agent execution with timing data."""
    agent_id: str
    task: float
    start_time: float
    end_time: float


class TimestampingAgent:
    """Agent that records execution timestamps to prove parallel execution."""

    def __init__(self, agent_id: str, delay: float = 0.1) -> None:
        self.agent_id = agent_id
        self.delay = delay

    async def execute_task(self, task: float) -> AgentResult:
        """Execute task and return structured result with timing data."""
        start_time = time.perf_counter()
        await asyncio.sleep(self.delay)
        end_time = time.perf_counter()
        return AgentResult(
            agent_id=self.agent_id,
            task=task,
            start_time=start_time,
            end_time=end_time
        )


def _get_execution_windows(results: List[AgentResult]) -> List[Tuple[float, float]]:
    """Extract execution time windows from agent results."""
    return [(r.start_time, r.end_time) for r in results]


def _count_overlaps(windows: List[Tuple[float, float]]) -> int:
    """Count overlapping execution windows to verify parallel execution."""
    overlaps = 0
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            start1, end1 = windows[i]
            start2, end2 = windows[j]
            if start1 < end2 and start2 < end1:
                overlaps += 1
    return overlaps


@pytest.mark.asyncio
async def test_parallel_task_execution():
    """Demonstrate that tasks are executed concurrently by analyzing execution timestamps."""
    coordinator = AgentCoordinator()
    for i in range(3):
        coordinator.register_agent(TimestampingAgent(f"a{i}"))

    assignments = [(f"a{i}", i) for i in range(3)]
    results = await coordinator.distribute_tasks_parallel(assignments)
    
    assert len(results) == 3 and all(isinstance(result, AgentResult) for result in results)
    execution_windows = _get_execution_windows(results)
    overlaps = _count_overlaps(execution_windows)
    assert overlaps > 0, f"No overlapping execution detected. Windows: {execution_windows}"


@pytest.mark.asyncio
async def test_distribute_parallel_with_no_agents():
    """Test behavior with no registered agents."""
    coordinator = AgentCoordinator()
    assignments = [("nonexistent", 1)]
    
    # Should raise AgentNotFoundError for nonexistent agent
    with pytest.raises(AgentNotFoundError) as exc_info:
        await coordinator.distribute_tasks_parallel(assignments)
    assert exc_info.value.agent_id == "nonexistent"


@pytest.mark.asyncio
async def test_distribute_parallel_with_empty_task_list():
    """Test behavior with empty task list."""
    coordinator = AgentCoordinator()
    coordinator.register_agent(TimestampingAgent("a1"))
    
    results = await coordinator.distribute_tasks_parallel([])
    assert results == []


@pytest.mark.asyncio
async def test_distribute_parallel_with_more_tasks_than_agents():
    """Test distributing more tasks than available agents."""
    coordinator = AgentCoordinator()
    coordinator.register_agent(TimestampingAgent("a1", delay=0.05))  # Faster for testing
    coordinator.register_agent(TimestampingAgent("a2", delay=0.05))
    
    # 4 tasks, 2 agents - should handle gracefully
    assignments = [(f"a{i % 2 + 1}", i) for i in range(4)]
    results = await coordinator.distribute_tasks_parallel(assignments)
    
    assert len(results) == 4
    assert all(isinstance(result, AgentResult) and result.agent_id.startswith("a") for result in results)


@pytest.mark.asyncio
async def test_distribute_parallel_with_single_agent():
    """Test with only one agent (sequential execution)."""
    coordinator = AgentCoordinator()
    coordinator.register_agent(TimestampingAgent("a1", delay=0.05))
    
    assignments = [("a1", i) for i in range(2)]
    results = await coordinator.distribute_tasks_parallel(assignments)
    
    assert len(results) == 2
    assert all(isinstance(result, AgentResult) and result.agent_id == "a1" for result in results)
