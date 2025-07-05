import asyncio
from knowledge_storm import STORMConfig, EnhancedSTORMEngine


def test_config_modes():
    cfg = STORMConfig(mode="hybrid")
    assert cfg.academic_sources
    assert cfg.quality_gates
    assert not cfg.citation_verification

    cfg.set_mode("wikipedia")
    assert not cfg.academic_sources
    assert not cfg.quality_gates

    cfg.set_mode("academic")
    assert cfg.citation_verification
    assert cfg.real_time_verification


def test_engine_dispatch():
    cfg = STORMConfig(mode="wikipedia")
    engine = EnhancedSTORMEngine(cfg)

    async def run():
        result = await engine.generate_article("topic")
        assert result == "original:topic"

    asyncio.run(run())
