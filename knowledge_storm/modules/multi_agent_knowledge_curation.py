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

    async def research(self, topic, ground_truth_url="", callback_handler=None, max_perspective=0, disable_perspective=True, return_conversation_log=False):
        """Research using multi-agent coordination with error handling."""
        print(f"Performing multi-agent research on topic: {topic}")

        # Initialize results
        plan_result = None
        research_result = "Research completed"
        critique_result = "Critique completed"
        verify_result = "Verification completed"

        try:
            plan_result = await self.coordinator.distribute_task(
                self.planner.agent_id, topic
            )
        except Exception as e:
            logger.warning(f"Planning failed for {topic}: {e}")
            plan_result = {"error": "Planning failed", "topic": topic}

        try:
            research_result = await self.coordinator.distribute_task(
                self.researcher.agent_id, topic
            )
        except Exception as e:
            logger.warning(f"Research failed for {topic}: {e}")
            research_result = "Research failed"

        try:
            critique_result = await self.coordinator.distribute_task(
                self.critic.agent_id, research_result
            )
        except Exception as e:
            logger.warning(f"Critique failed for {topic}: {e}")
            critique_result = "Critique failed"

        try:
            verify_result = await self.coordinator.distribute_task(
                self.verifier.agent_id, research_result
            )
        except Exception as e:
            logger.warning(f"Verification failed for {topic}: {e}")
            verify_result = "Verification failed"

        conversations = [
            (self.planner.name, [DialogueTurn(agent_utterance=str(plan_result))]),
            (self.researcher.name, [DialogueTurn(agent_utterance=research_result)]),
            (self.critic.name, [DialogueTurn(agent_utterance=critique_result)]),
            (self.verifier.name, [DialogueTurn(agent_utterance=verify_result)]),
        ]

        # Create mock information table for now
        from knowledge_storm.storm_wiki.modules.storm_dataclass import StormInformationTable
        info_table = StormInformationTable()
        info_table.conversations = conversations

        if return_conversation_log:
            return info_table, conversations
        return info_table
