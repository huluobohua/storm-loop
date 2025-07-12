from knowledge_storm.interface import KnowledgeCurationModule
from knowledge_storm.storm_wiki.modules.storm_dataclass import (
    DialogueTurn,
    StormInformationTable,
)
from knowledge_storm.agents.researcher import AcademicResearcherAgent
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
        planner_agent: Optional[ResearchPlannerAgent] = None,
        researcher_agent: Optional[AcademicResearcherAgent] = None,
        verifier_agent: Optional[CitationVerifierAgent] = None,
    ) -> None:
        super().__init__(config.retriever)
        self.config = config

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
        self.verifier = verifier_agent or CitationVerifierAgent(
            agent_id="verifier",
            name="Citation Verifier",
        )

    async def _safely_execute_task(self, agent, task: str, task_name: str, fallback: Any) -> Any:
        """Run a task directly on agent, returning fallback on failure."""
        try:
            # Direct agent execution without coordinator
            if hasattr(agent, 'process'):
                return await agent.process(task)
            elif hasattr(agent, 'generate'):
                return await agent.generate(task)
            else:
                return await agent(task)
        except Exception as e:  # pragma: no cover - network or agent failure
            logger.warning(f"{task_name} failed for {task}: {e}")
            return fallback

    async def _run_planning(self, topic: str) -> Any:
        return await self._safely_execute_task(
            self.planner,
            topic,
            "Planning",
            {"error": "Planning failed", "topic": topic},
        )

    async def _run_research(self, topic: str) -> Any:
        return await self._safely_execute_task(
            self.researcher,
            topic,
            "Research",
            "Research failed",
        )

    async def _run_verification(self, research_result: Any) -> Any:
        return await self._safely_execute_task(
            self.verifier,
            research_result,
            "Verification",
            "Verification failed",
        )

    def _build_conversations(
        self,
        plan: Any,
        research_result: Any,
        verify_result: Any,
    ) -> list[tuple[str, list[DialogueTurn]]]:
        return [
            (self.planner.name, [DialogueTurn(agent_utterance=str(plan))]),
            (self.researcher.name, [DialogueTurn(agent_utterance=research_result)]),
            (self.verifier.name, [DialogueTurn(agent_utterance=verify_result)]),
        ]

    def _finalize_output(
        self,
        plan: Any,
        research_result: Any,
        verify_result: Any,
        return_conversation_log: bool,
    ):
        conversations = self._build_conversations(
            plan, research_result, verify_result
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
        """Research using streamlined multi-agent workflow with verification."""
        print(f"Performing multi-agent research on topic: {topic}")
        plan = await self._run_planning(topic)
        research_res = await self._run_research(topic)
        verify_res = await self._run_verification(research_res)
        return self._finalize_output(
            plan, research_res, verify_res, return_conversation_log
        )
