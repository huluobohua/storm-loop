from __future__ import annotations

from typing import Callable
import threading
import os

from .config_validators import STORMMode, ConfigValidator, StrictConfigValidator


class STORMConfig:
    def __init__(self, mode: str | STORMMode = STORMMode.HYBRID,
                 validator: ConfigValidator | None = None) -> None:
        self._lock = threading.RLock()
        self._validator = validator or StrictConfigValidator()
        self._mode_handlers = self._build_mode_handlers()
        self.set_mode(mode)

    def _build_mode_handlers(self) -> dict[STORMMode, Callable[[], None]]:
        return {
            STORMMode.ACADEMIC: self._configure_academic_mode,
            STORMMode.WIKIPEDIA: self._configure_wikipedia_mode,
            STORMMode.HYBRID: self._configure_hybrid_mode,
        }

    def set_mode(self, mode: str | STORMMode) -> None:
        if isinstance(mode, str):
            mode = self._validator.validate_mode(mode)
        self._current_mode = mode
        self._mode_handlers[mode]()

    def switch_mode(self, mode: str | STORMMode) -> None:
        with self._lock:
            self.set_mode(mode)

    def _configure_academic_mode(self) -> None:
        self.academic_sources = True
        self.quality_gates = True
        self.citation_verification = True
        self.real_time_verification = True

    def _configure_wikipedia_mode(self) -> None:
        self.academic_sources = False
        self.quality_gates = False
        self.citation_verification = False
        self.real_time_verification = False

    def _configure_hybrid_mode(self) -> None:
        self.academic_sources = True
        self.quality_gates = True
        self.citation_verification = False
        self.real_time_verification = False
        
        # Performance configuration with specific error handling
        try:
            self.cache_warm_parallel = int(os.getenv('STORM_CACHE_PARALLEL', '5'))
            if self.cache_warm_parallel < 1:
                raise ValueError("STORM_CACHE_PARALLEL must be positive")
        except (ValueError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid STORM_CACHE_PARALLEL value, using default 5: {e}")
            self.cache_warm_parallel = 5
        
        try:
            self.api_rate_limit = int(os.getenv('STORM_API_RATE_LIMIT', '10'))
            if self.api_rate_limit < 1:
                raise ValueError("STORM_API_RATE_LIMIT must be positive")
        except (ValueError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid STORM_API_RATE_LIMIT value, using default 10: {e}")
            self.api_rate_limit = 10

    @property
    def mode(self) -> str:
        with self._lock:
            return self._current_mode.value

