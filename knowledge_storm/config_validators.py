from enum import Enum
from typing import Protocol


class STORMMode(Enum):
    ACADEMIC = "academic"
    WIKIPEDIA = "wikipedia"
    HYBRID = "hybrid"


class ConfigValidator(Protocol):
    def validate_mode(self, mode: str) -> STORMMode:
        ...


class StrictConfigValidator:
    def validate_mode(self, mode: str) -> STORMMode:
        try:
            return STORMMode(mode)
        except ValueError:
            valid_modes = [m.value for m in STORMMode]
            raise ValueError(
                f"Invalid mode '{mode}'. Valid modes: {valid_modes}"
            )

