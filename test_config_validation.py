import asyncio
import pytest

from knowledge_storm.config_validators import (
    STORMMode, StrictConfigValidator,
)
from knowledge_storm.storm_config import STORMConfig
from knowledge_storm.environment_config import (
    TestEnvironmentReader as EnvReader,
    create_config_from_environment,
)


class TestConfigValidation:
    def test_valid_modes_accepted(self):
        validator = StrictConfigValidator()
        assert validator.validate_mode("academic") == STORMMode.ACADEMIC
        assert validator.validate_mode("wikipedia") == STORMMode.WIKIPEDIA
        assert validator.validate_mode("hybrid") == STORMMode.HYBRID

    def test_invalid_mode_raises_detailed_error(self):
        validator = StrictConfigValidator()
        with pytest.raises(ValueError, match="Invalid mode 'invalid'.*academic.*wikipedia.*hybrid"):
            validator.validate_mode("invalid")

    def test_empty_mode_raises_error(self):
        validator = StrictConfigValidator()
        with pytest.raises(ValueError):
            validator.validate_mode("")

    def test_none_mode_raises_error(self):
        validator = StrictConfigValidator()
        with pytest.raises(ValueError):
            validator.validate_mode(None)  # type: ignore[arg-type]


class TestSTORMConfig:
    def test_string_mode_initialization(self):
        config = STORMConfig("academic")
        assert config.mode == "academic"
        assert config.citation_verification

    def test_enum_mode_initialization(self):
        config = STORMConfig(STORMMode.WIKIPEDIA)
        assert config.mode == "wikipedia"
        assert not config.academic_sources

    def test_mode_switching_updates_all_flags(self):
        config = STORMConfig("wikipedia")
        assert not config.academic_sources

        config.switch_mode("academic")
        assert config.academic_sources
        assert config.citation_verification

    def test_invalid_mode_switch_preserves_state(self):
        config = STORMConfig("academic")
        original_mode = config.mode

        with pytest.raises(ValueError):
            config.switch_mode("invalid")

        assert config.mode == original_mode
        assert config.citation_verification  # State preserved


class TestEnvironmentConfiguration:
    def test_environment_mode_override(self):
        reader = EnvReader("academic")
        config = create_config_from_environment(reader)
        assert config.mode == "academic"

    def test_missing_environment_defaults_hybrid(self):
        reader = EnvReader(None)
        config = create_config_from_environment(reader)
        assert config.mode == "hybrid"

    def test_invalid_environment_mode_raises_error(self):
        reader = EnvReader("invalid")
        with pytest.raises(ValueError):
            create_config_from_environment(reader)


class TestConcurrentAccess:
    def test_concurrent_mode_switches(self):
        config = STORMConfig("hybrid")

        async def switch_to_academic():
            config.switch_mode("academic")
            await asyncio.sleep(0.01)
            assert config.mode == "academic"

        async def switch_to_wikipedia():
            config.switch_mode("wikipedia")
            await asyncio.sleep(0.01)
            assert config.mode == "wikipedia"

        async def run():
            tasks = [switch_to_academic(), switch_to_wikipedia()]
            await asyncio.gather(*tasks, return_exceptions=True)

        asyncio.run(run())


