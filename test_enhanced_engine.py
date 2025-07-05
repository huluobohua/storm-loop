import asyncio
from unittest.mock import AsyncMock

from knowledge_storm import STORMConfig, EnhancedSTORMEngine


class DummyRunner:
    async def run(self, *args, **kwargs):
        pass


def test_storm_config_modes():
    cfg = STORMConfig(mode="academic")
    assert cfg.academic_sources
    assert cfg.quality_gates
    assert cfg.citation_verification
    assert cfg.real_time_verification

    cfg = STORMConfig(mode="wikipedia")
    assert not cfg.academic_sources
    assert not cfg.citation_verification


def test_engine_uses_correct_workflow(monkeypatch):
    cfg = STORMConfig(mode="academic")
    runner = DummyRunner()
    engine = EnhancedSTORMEngine(cfg, runner)

    called = {}

    async def academic(*a, **k):
        called["academic"] = True

    async def original(*a, **k):
        called["original"] = True

    monkeypatch.setattr(engine, "academic_workflow", academic)
    monkeypatch.setattr(engine, "original_workflow", original)

    asyncio.run(engine.generate_article("topic"))
    assert called.get("academic")
    called.clear()

    engine.config = STORMConfig(mode="wikipedia")
    asyncio.run(engine.generate_article("topic"))
    assert called.get("original")


