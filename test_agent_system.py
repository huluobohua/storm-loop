import asyncio
from unittest.mock import patch

from models.agent import AcademicResearcherAgent, CriticAgent, CitationVerifierAgent
from knowledge_storm.agent_coordinator import AgentCoordinator


def test_agent_execution_and_coordination():
    async def run():
        researcher = AcademicResearcherAgent("r1", "Researcher")
        critic = CriticAgent("c1", "Critic")
        verifier = CitationVerifierAgent("v1", "Verifier")

        coordinator = AgentCoordinator()
        coordinator.register_agent(researcher)
        coordinator.register_agent(critic)
        coordinator.register_agent(verifier)

        tasks = [
            (researcher.agent_id, "quantum computing"),
            (critic.agent_id, "quantum computing"),
            (verifier.agent_id, "quantum computing"),
        ]
        with patch("knowledge_storm.services.academic_source_service.AcademicSourceService.search_openalex", return_value=[{"title": "X"}]), patch("knowledge_storm.services.academic_source_service.AcademicSourceService.search_crossref", return_value=[{"title": "Y"}]), patch("knowledge_storm.services.academic_source_service.AcademicSourceService.get_publication_metadata", return_value={"title": "Z"}):
            results = await coordinator.distribute_tasks_parallel(tasks)

        assert len(results) == 3
        assert isinstance(results[0], list) or isinstance(results[0], str)

    asyncio.run(run())
def test_agent_communication():
    async def run():
        sender = AcademicResearcherAgent("s", "Sender")
        receiver = CriticAgent("r", "Receiver")

        await sender.send_message(receiver, "hello")
        snd, msg = await receiver.receive_message()

        assert snd == sender.agent_id
        assert msg == "hello"

    asyncio.run(run())


if __name__ == "__main__":
    test_agent_execution_and_coordination()
    test_agent_communication()
