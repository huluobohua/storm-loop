from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from knowledge_storm.services.academic_source_service import (
    AcademicSourceService,
    SourceQualityScorer,
)

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

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str = "Academic Researcher",
        service: AcademicSourceService | None = None,
    ) -> None:
        super().__init__(agent_id, name, role)
        self.service = service or AcademicSourceService()
        self.scorer = SourceQualityScorer()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    async def execute_task(self, task: str) -> List[Dict[str, Any]]:
        if task in self._cache:
            return self._cache[task]

        openalex = await asyncio.to_thread(self.service.search_openalex, task, 3)
        crossref = await asyncio.to_thread(self.service.search_crossref, task, 3)
        combined = openalex + crossref
        for entry in combined:
            entry["score"] = self.scorer.score_source(entry)
        self._cache[task] = combined
        return combined

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} received: {message}"


class CriticAgent(Agent):
    """Agent that provides critical evaluation and review."""

    def __init__(self, agent_id: str, name: str, role: str = "Critic"):
        super().__init__(agent_id, name, role)

    def _score_text(self, text: str) -> float:
        """Very naive quality score based on length."""
        return min(len(text) / 100.0, 10.0)

    async def execute_task(self, task: str) -> str:
        await asyncio.sleep(0)
        score = self._score_text(task)
        return f"Quality score: {score:.2f}"

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} notes: {message}"


class CitationVerifierAgent(Agent):
    """Agent responsible for verifying citations and sources."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str = "Citation Verifier",
        service: AcademicSourceService | None = None,
    ) -> None:
        super().__init__(agent_id, name, role)
        self.service = service or AcademicSourceService()

    async def execute_task(self, task: str) -> str:
        metadata = await asyncio.to_thread(self.service.get_publication_metadata, task)
        if metadata:
            return "DOI verified"
        return "DOI not found"

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} acknowledged: {message}"


class WriterAgent(Agent):
    """Agent that generates simple academic text with citations."""

    def __init__(self, agent_id: str, name: str, role: str = "Writer", citation_style: str = "APA") -> None:
        super().__init__(agent_id, name, role)
        self.citation_style = citation_style

    def _format_citation(self, ref: Dict[str, Any]) -> str:
        authors = ref.get("author", "Unknown")
        year = ref.get("publication_year") or "n.d."
        title = ref.get("title", "")
        doi = ref.get("doi", "")
        return f"{authors} ({year}). {title}. DOI:{doi}"

    async def execute_task(self, task: str) -> str:
        refs: List[Dict[str, Any]] = self.state.get("references", [])
        citations = [self._format_citation(r) for r in refs]
        await asyncio.sleep(0)
        return f"Article on {task}\n" + "\n".join(citations)

    async def communicate(self, message: str) -> str:
        await asyncio.sleep(0)
        return f"{self.name} acknowledges: {message}"

