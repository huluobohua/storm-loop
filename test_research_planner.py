import asyncio
from unittest.mock import AsyncMock, patch

from knowledge_storm.services.research_planner import ResearchPlanner
from models.agent import ResearchPlannerAgent


def test_research_planner_basic():
    planner = ResearchPlanner()
    plan = asyncio.run(planner.plan_research("quantum computing"))
    assert plan["topic"] == "quantum computing"
    assert plan["steps"]


def test_research_planner_agent_execution():
    planner = ResearchPlanner()
    agent = ResearchPlannerAgent("p", "Planner", planner=planner)
    result = asyncio.run(agent.execute_task("machine learning"))
    assert "steps" in result


def test_multi_agent_module_returns_plan():
    import sys
    import types
    import pytest

    # Provide minimal dspy modules so import does not fail
    dspy_mod = types.ModuleType("dspy")
    dsp_mod = types.ModuleType("dspy.dsp")
    modules_mod = types.ModuleType("dspy.dsp.modules")
    lm_mod = types.ModuleType("dspy.dsp.modules.lm")
    dspy_mod.dsp = dsp_mod
    sys.modules.setdefault("dspy", dspy_mod)
    sys.modules.setdefault("dspy.dsp", dsp_mod)
    sys.modules.setdefault("dspy.dsp.modules", modules_mod)
    sys.modules.setdefault("dspy.dsp.modules.lm", lm_mod)

    mod = pytest.importorskip("knowledge_storm.modules.multi_agent_knowledge_curation")
    MultiAgentKnowledgeCurationModule = mod.MultiAgentKnowledgeCurationModule

    module = MultiAgentKnowledgeCurationModule(None, None, None, None, 1, 1, 1, 1)
    with patch(
        "knowledge_storm.services.academic_source_service.AcademicSourceService.search_openalex",
        new=AsyncMock(return_value=[{"title": "A"}]),
    ), patch(
        "knowledge_storm.services.academic_source_service.AcademicSourceService.search_crossref",
        new=AsyncMock(return_value=[{"title": "B"}]),
    ), patch(
        "knowledge_storm.services.academic_source_service.AcademicSourceService.get_publication_metadata",
        new=AsyncMock(return_value={}),
    ):
        table, _ = asyncio.run(module.research("topic"))
    assert table.conversations[0][0] == "Research Planner"
