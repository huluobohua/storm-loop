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

    async def research(self, topic, ground_truth_url="", callback_handler=None, max_perspective=3, disable_perspective=False, return_conversation_log=True):
        # Placeholder for multi-agent research logic
        # This will involve orchestrating calls to self.coordinator.distribute_task
        # and potentially self.coordinator.distribute_tasks_parallel
        # The output should be an InformationTable and a conversation_log
        print(f"Performing multi-agent research on topic: {topic}")

        plan_result = await self.coordinator.distribute_task(
            self.planner.agent_id, topic
        )

        research_result = await self.coordinator.distribute_task(
            self.researcher.agent_id, topic
        )

        critique_task = (self.critic.agent_id, topic)
        verify_task = (self.verifier.agent_id, topic)
        critique_result, verify_result = await self.coordinator.distribute_tasks_parallel(
            [critique_task, verify_task]
        )

        conversations = [
            (self.planner.name, [DialogueTurn(agent_utterance=str(plan_result))]),
            (self.researcher.name, [DialogueTurn(agent_utterance=research_result)]),
            (self.critic.name, [DialogueTurn(agent_utterance=critique_result)]),
            (self.verifier.name, [DialogueTurn(agent_utterance=verify_result)]),
        ]

        info_table = StormInformationTable(conversations)
        conv_log = StormInformationTable.construct_log_dict(conversations)

        return info_table, conv_log
