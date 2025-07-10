import os
from typing import Protocol, Optional

from .storm_config import STORMConfig


class EnvironmentReader(Protocol):
    def get_storm_mode(self) -> Optional[str]:
        ...


class ProductionEnvironmentReader:
    def get_storm_mode(self) -> Optional[str]:
        return os.getenv("STORM_MODE")


class TestEnvironmentReader:
    def __init__(self, mode: str | None = None) -> None:
        self._mode = mode

    def get_storm_mode(self) -> str | None:
        return self._mode


def create_config_from_environment(
    env_reader: EnvironmentReader | None = None,
) -> STORMConfig:
    reader = env_reader or ProductionEnvironmentReader()
    mode = reader.get_storm_mode() or "hybrid"
    return STORMConfig(mode=mode)

