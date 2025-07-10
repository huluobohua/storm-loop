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
from typing import List, Tuple

import pytest
from knowledge_storm.agent_coordinator import AgentCoordinator


@dataclass
class AgentResult:
    """Structured result from agent execution with timing data."""
    agent_id: str
    task: float
    start_time: float
    end_time: float
    
    @classmethod
    def from_agent_response(cls, response: str) -> "AgentResult":
        """Parse agent response string into structured data."""
        parts = response.split("_")
        return cls(
            agent_id=parts[1],
            task=float(parts[3]),
            start_time=float(parts[5]),
            end_time=float(parts[7])
        )


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


def _get_execution_windows(results: List[str]) -> List[Tuple[float, float]]:
    """Extract execution time windows from agent results."""
    return [(r.start_time, r.end_time) for r in [AgentResult.from_agent_response(result) for result in results]]


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
    
    assert len(results) == 3 and all("agent_" in result for result in results)
    execution_windows = _get_execution_windows(results)
    overlaps = _count_overlaps(execution_windows)
    assert overlaps > 0, f"No overlapping execution detected. Windows: {execution_windows}"


@pytest.mark.asyncio
async def test_distribute_parallel_with_no_agents():
    """Test behavior with no registered agents."""
    coordinator = AgentCoordinator()
    assignments = [("nonexistent", 1)]
    
    # The method should return a list with None values for failed tasks
    results = await coordinator.distribute_tasks_parallel(assignments)
    assert results == [None]  # Failed task returns None


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
    assert all("agent_" in result for result in results)


@pytest.mark.asyncio
async def test_distribute_parallel_with_single_agent():
    """Test with only one agent (sequential execution)."""
    coordinator = AgentCoordinator()
    coordinator.register_agent(TimestampingAgent("a1", delay=0.05))
    
    assignments = [("a1", i) for i in range(2)]
    results = await coordinator.distribute_tasks_parallel(assignments)
    
    assert len(results) == 2
    assert all("agent_a1" in result for result in results)
