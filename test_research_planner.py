import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from knowledge_storm.services.cache_service import CacheService
from knowledge_storm.services.research_planner import ResearchPlanner
from knowledge_storm.agents.planner import ResearchPlannerAgent


def test_research_planner_basic():
    planner = ResearchPlanner()
    plan = asyncio.run(planner.plan_research("quantum computing"))
    assert plan["topic"] == "quantum computing"
    assert plan["steps"]


def test_research_planner_agent_execution():
    planner = ResearchPlanner()
    agent = ResearchPlannerAgent("p", "Planner")
    agent.planner = planner
    result = asyncio.run(agent.execute_task("machine learning"))
    assert "steps" in result


def test_research_planner_validates_empty_topic():
    planner = ResearchPlanner()
    with pytest.raises(ValueError):
        asyncio.run(planner.plan_research(" "))


def test_topic_complexity_scoring():
    planner = ResearchPlanner()
    complexity = asyncio.run(planner.analyze_topic_complexity("quantum computing"))
    assert complexity == 2


def test_plan_research_caches_result():
    cache = CacheService()
    planner = ResearchPlanner(cache)
    with patch.object(cache, "get", new=AsyncMock(return_value=None)) as get_mock, \
         patch.object(cache, "set", new=AsyncMock()) as set_mock:
        plan = asyncio.run(planner.plan_research("machine learning"))
        get_mock.assert_awaited_with("plan:machine learning")
        set_mock.assert_awaited()
        assert plan["topic"] == "machine learning"


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

