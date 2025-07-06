from knowledge_storm.interface import KnowledgeCurationModule
from knowledge_storm.storm_wiki.modules.storm_dataclass import (
    DialogueTurn,
    StormInformationTable,
)
from knowledge_storm.agent_coordinator import AgentCoordinator
from knowledge_storm.agents.researcher import AcademicResearcherAgent
from knowledge_storm.agents.critic import CriticAgent
from knowledge_storm.agents.citation_verifier import CitationVerifierAgent
from knowledge_storm.agents.planner import ResearchPlannerAgent
from typing import Any
import logging

logger = logging.getLogger(__name__)

class MultiAgentKnowledgeCurationModule(KnowledgeCurationModule):
    def __init__(self, retriever, persona_generator, conv_simulator_lm, question_asker_lm, max_search_queries_per_turn, search_top_k, max_conv_turn, max_thread_num):
        super().__init__(retriever)
        self.persona_generator = persona_generator
        self.conv_simulator_lm = conv_simulator_lm
        self.question_asker_lm = question_asker_lm
        self.max_search_queries_per_turn = max_search_queries_per_turn
        self.search_top_k = search_top_k
        self.max_conv_turn = max_conv_turn
        self.max_thread_num = max_thread_num
        self.coordinator = AgentCoordinator()

        # Register agents
        self.planner = ResearchPlannerAgent(agent_id="planner", name="Research Planner")
        self.researcher = AcademicResearcherAgent(agent_id="researcher", name="Academic Researcher")
        self.critic = CriticAgent(agent_id="critic", name="Critic")
        self.verifier = CitationVerifierAgent(agent_id="verifier", name="Citation Verifier")

        self.coordinator.register_agent(self.planner)
        self.coordinator.register_agent(self.researcher)
        self.coordinator.register_agent(self.critic)
        self.coordinator.register_agent(self.verifier)

    async def _safely_execute_task(self, agent_id: str, task: str, task_name: str, fallback: Any) -> Any:
        """Run a task through the coordinator, returning fallback on failure."""
        try:
            return await self.coordinator.distribute_task(agent_id, task)
        except Exception as e:  # pragma: no cover - network or agent failure
            logger.warning(f"{task_name} failed for {task}: {e}")
            return fallback

    async def research(self, topic, ground_truth_url="", callback_handler=None, max_perspective=0, disable_perspective=True, return_conversation_log=False):
        """Research using multi-agent coordination with error handling."""
        print(f"Performing multi-agent research on topic: {topic}")

        plan_result = await self._safely_execute_task(
            self.planner.agent_id,
            topic,
            "Planning",
            {"error": "Planning failed", "topic": topic},
        )

        research_result = await self._safely_execute_task(
            self.researcher.agent_id,
            topic,
            "Research",
            "Research failed",
        )

        critique_result = await self._safely_execute_task(
            self.critic.agent_id,
            research_result,
            "Critique",
            "Critique failed",
        )

        verify_result = await self._safely_execute_task(
            self.verifier.agent_id,
            research_result,
            "Verification",
            "Verification failed",
        )

        conversations = [
            (self.planner.name, [DialogueTurn(agent_utterance=str(plan_result))]),
            (self.researcher.name, [DialogueTurn(agent_utterance=research_result)]),
            (self.critic.name, [DialogueTurn(agent_utterance=critique_result)]),
            (self.verifier.name, [DialogueTurn(agent_utterance=verify_result)]),
        ]

        info_table = StormInformationTable()
        info_table.conversations = conversations

        if return_conversation_log:
            return info_table, conversations
        return info_table
