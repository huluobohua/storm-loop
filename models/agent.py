from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

class Agent(ABC):
    """Base class for all agents in the multi-agent system."""

    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.state: dict[str, Any] = {}
        self._inbox: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    async def send_message(self, other: "Agent", message: str) -> None:
        """Asynchronously send a message to another agent."""
        await other._inbox.put((self.agent_id, message))

    async def receive_message(self) -> tuple[str, str]:
        """Receive the next message from this agent's inbox."""
        sender, message = await self._inbox.get()
        return sender, message

    def update_state(self, key: str, value: Any) -> None:
        self.state[key] = value

    @abstractmethod
    async def execute_task(self, task: str) -> str:
        """Execute a task asynchronously and return a result."""
        raise NotImplementedError

    @abstractmethod
    async def communicate(self, message: str) -> str:
        """Handle an incoming communication and return a response."""
        raise NotImplementedError


class AcademicResearcherAgent(Agent):
    """Agent specializing in academic research and data gathering."""

    def __init__(self, agent_id: str, name: str, role: str = "Academic Researcher"):
        super().__init__(agent_id, name, role)

    async def execute_task(self, task: str) -> str:
        await asyncio.sleep(0)  # allow context switch
        return f"Research results for {task}"

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} received: {message}"


class CriticAgent(Agent):
    """Agent that provides critical evaluation and review."""

    def __init__(self, agent_id: str, name: str, role: str = "Critic"):
        super().__init__(agent_id, name, role)

    async def execute_task(self, task: str) -> str:
        await asyncio.sleep(0)
        return f"Critique of {task}"

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} notes: {message}"


class CitationVerifierAgent(Agent):
    """Agent responsible for verifying citations and sources."""

    def __init__(self, agent_id: str, name: str, role: str = "Citation Verifier"):
        super().__init__(agent_id, name, role)

    async def execute_task(self, task: str) -> str:
        await asyncio.sleep(0)
        return f"Citations verified for {task}"

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} acknowledged: {message}"
