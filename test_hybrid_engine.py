import asyncio
from knowledge_storm import STORMConfig, EnhancedSTORMEngine


def test_config_modes():
    cfg = STORMConfig()
    assert cfg.mode == "hybrid"
    assert cfg.academic_sources
    assert cfg.quality_gates
    assert not cfg.citation_verification

    cfg.switch_mode("wikipedia")
    assert cfg.mode == "wikipedia"
    assert not cfg.academic_sources

    cfg.switch_mode("academic")
    assert cfg.citation_verification


def test_engine_routing(monkeypatch):
    cfg = STORMConfig("academic")
    engine = EnhancedSTORMEngine(cfg)

    async def academic(topic, **kw):
        return "A"

    async def original(topic, **kw):
        return "O"

    class Runner:
        async def run_academic_workflow(self, topic: str, **kw):
            return await academic(topic, **kw)

        async def run_original_workflow(self, topic: str, **kw):
            return await original(topic, **kw)

    engine._workflow_runner = Runner()

    assert asyncio.run(engine.generate_article("t")) == "A"

    cfg.switch_mode("wikipedia")
    assert asyncio.run(engine.generate_article("t")) == "O"
