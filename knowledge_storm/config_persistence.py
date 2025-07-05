import json
from pathlib import Path
from typing import Protocol

from .storm_config import STORMConfig


class ConfigPersister(Protocol):
    def save_config(self, config: STORMConfig, path: Path) -> None:
        ...

    def load_config(self, path: Path) -> STORMConfig:
        ...


class JSONConfigPersister:
    def save_config(self, config: STORMConfig, path: Path) -> None:
        config_data = {
            "mode": config.mode,
            "academic_sources": config.academic_sources,
            "quality_gates": config.quality_gates,
            "citation_verification": config.citation_verification,
            "real_time_verification": config.real_time_verification,
        }
        with path.open("w") as f:
            json.dump(config_data, f, indent=2)

    def load_config(self, path: Path) -> STORMConfig:
        with path.open("r") as f:
            config_data = json.load(f)
        return STORMConfig(mode=config_data["mode"])

