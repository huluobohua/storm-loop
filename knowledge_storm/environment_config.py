import os
from typing import Protocol

from .storm_config import STORMConfig


class EnvironmentReader(Protocol):
    def get_storm_mode(self) -> str | None:
        ...


class ProductionEnvironmentReader:
    def get_storm_mode(self) -> str | None:
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

