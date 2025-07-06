import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from knowledge_storm.services.research_planner import ResearchPlanner
from knowledge_storm.agents.planner import ResearchPlannerAgent


def test_research_planner_basic():
    planner = ResearchPlanner()
    plan = asyncio.run(planner.plan_research("quantum computing"))
    assert plan["topic"] == "quantum computing"
    assert plan["steps"]


def test_research_planner_agent_execution():
    planner = ResearchPlanner()
    agent = ResearchPlannerAgent("p", "Planner", planner)
    result = asyncio.run(agent.execute_task("machine learning"))
    assert "steps" in result


def test_plan_research_validates_topic():
    planner = ResearchPlanner()
    with pytest.raises(ValueError):
        asyncio.run(planner.plan_research(""))


def test_analyze_topic_complexity_caps_at_10():
    planner = ResearchPlanner()
    topic = "word " * 20
    complexity = asyncio.run(planner.analyze_topic_complexity(topic))
    assert complexity == 10


def test_plan_research_handles_cache_get_failure():
    """Test fallback when cache.get() fails."""
    cache = AsyncMock()
    cache.get.side_effect = Exception("Cache read failed")
    cache.set = AsyncMock()

    planner = ResearchPlanner(cache)
    plan = asyncio.run(planner.plan_research("test topic"))

    assert plan["topic"] == "test topic"
    assert "steps" in plan
    assert "error" not in plan


def test_plan_research_handles_cache_set_failure():
    """Test graceful degradation when cache.set() fails."""
    cache = AsyncMock()
    cache.get.return_value = None
    cache.set.side_effect = Exception("Cache write failed")

    planner = ResearchPlanner(cache)
    plan = asyncio.run(planner.plan_research("test topic"))

    assert plan["topic"] == "test topic"
    assert "steps" in plan


def test_plan_research_returns_fallback_on_total_failure():
    """Test fallback plan when everything fails."""
    planner = ResearchPlanner()
    with patch.object(planner, "analyze_topic_complexity", side_effect=Exception("Analysis failed")):
        plan = asyncio.run(planner.plan_research("test topic"))

        assert plan["topic"] == "test topic"
        assert plan["complexity"] == 1
        assert plan["steps"] == ["search literature", "draft article"]
        assert plan["error"] == "Planning failed, using fallback"


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
