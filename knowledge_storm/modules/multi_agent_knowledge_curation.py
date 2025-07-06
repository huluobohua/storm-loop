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
from dataclasses import dataclass
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeCurationConfig:
    retriever: Any
    persona_generator: Any
    conv_simulator_lm: Any
    question_asker_lm: Any
    max_search_queries_per_turn: int
    search_top_k: int
    max_conv_turn: int
    max_thread_num: int

class MultiAgentKnowledgeCurationModule(KnowledgeCurationModule):
    def __init__(
        self,
        config: KnowledgeCurationConfig,
        *,
        coordinator: Optional[AgentCoordinator] = None,
        planner_agent: Optional[ResearchPlannerAgent] = None,
        researcher_agent: Optional[AcademicResearcherAgent] = None,
        critic_agent: Optional[CriticAgent] = None,
        verifier_agent: Optional[CitationVerifierAgent] = None,
    ) -> None:
        super().__init__(config.retriever)
        self.config = config
        self.coordinator = coordinator or AgentCoordinator()

        from ..services.research_planner import ResearchPlanner

        self.planner = planner_agent or ResearchPlannerAgent(
            agent_id="planner",
            name="Research Planner",
            planner=ResearchPlanner(),
        )
        self.researcher = researcher_agent or AcademicResearcherAgent(
            agent_id="researcher",
            name="Academic Researcher",
        )
        self.critic = critic_agent or CriticAgent(agent_id="critic", name="Critic")
        self.verifier = verifier_agent or CitationVerifierAgent(
            agent_id="verifier",
            name="Citation Verifier",
        )

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

    async def _run_planning(self, topic: str) -> Any:
        return await self._safely_execute_task(
            self.planner.agent_id,
            topic,
            "Planning",
            {"error": "Planning failed", "topic": topic},
        )

    async def _run_research(self, topic: str) -> Any:
        return await self._safely_execute_task(
            self.researcher.agent_id,
            topic,
            "Research",
            "Research failed",
        )

    async def _run_analysis(self, research_result: Any) -> tuple[Any, Any]:
        critique_task = (self.critic.agent_id, research_result)
        verify_task = (self.verifier.agent_id, research_result)
        try:
            return await self.coordinator.distribute_tasks_parallel([
                critique_task,
                verify_task,
            ])
        except Exception as e:
            logger.warning(f"Parallel analysis tasks failed: {e}")
            return "Critique failed", "Verification failed"

    def _build_conversations(
        self,
        plan: Any,
        research_result: Any,
        critique_result: Any,
        verify_result: Any,
    ) -> list[tuple[str, list[DialogueTurn]]]:
        return [
            (self.planner.name, [DialogueTurn(agent_utterance=str(plan))]),
            (self.researcher.name, [DialogueTurn(agent_utterance=research_result)]),
            (self.critic.name, [DialogueTurn(agent_utterance=critique_result)]),
            (self.verifier.name, [DialogueTurn(agent_utterance=verify_result)]),
        ]

    def _finalize_output(
        self,
        plan: Any,
        research_result: Any,
        critique_result: Any,
        verify_result: Any,
        return_conversation_log: bool,
    ):
        conversations = self._build_conversations(
            plan, research_result, critique_result, verify_result
        )
        info_table = StormInformationTable(conversations)
        if return_conversation_log:
            conv_log = StormInformationTable.construct_log_dict(conversations)
            return info_table, conv_log
        return info_table

    async def research(
        self,
        topic,
        ground_truth_url="",
        callback_handler=None,
        max_perspective=3,
        disable_perspective=False,
        return_conversation_log=True,
    ):
        """Research using multi-agent coordination with error handling."""
        print(f"Performing multi-agent research on topic: {topic}")
        plan = await self._run_planning(topic)
        research_res = await self._run_research(topic)
        critique_res, verify_res = await self._run_analysis(research_res)
        return self._finalize_output(
            plan, research_res, critique_res, verify_res, return_conversation_log
        )
