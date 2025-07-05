class STORMConfig:
    """Configuration settings for running STORM in different modes."""

    VALID_MODES = {"academic", "wikipedia", "hybrid"}

    def __init__(self, mode: str = "hybrid"):
        self.set_mode(mode)

    def set_mode(self, mode: str) -> None:
        """Set the engine mode and update feature flags."""
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.academic_sources = mode in ["academic", "hybrid"]
        self.quality_gates = mode in ["academic", "hybrid"]
        self.citation_verification = mode == "academic"
        self.real_time_verification = mode == "academic"

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "academic_sources": self.academic_sources,
            "quality_gates": self.quality_gates,
            "citation_verification": self.citation_verification,
            "real_time_verification": self.real_time_verification,
        }


class EnhancedSTORMEngine:
    """Unified entry point for STORM functionality with configurable modes."""

    def __init__(self, config: STORMConfig | None = None):
        self.config = config or STORMConfig()
        self.setup_components_based_on_mode()

    def setup_components_based_on_mode(self) -> None:
        """Placeholder for initializing components based on configuration."""
        # In the lightweight test implementation we simply store the flags.
        self.components = {
            "academic": self.config.academic_sources,
            "quality": self.config.quality_gates,
        }

    async def original_workflow(self, topic: str, **kwargs):
        """Stub for the original STORM workflow."""
        return f"original:{topic}"

    async def academic_workflow(self, topic: str, **kwargs):
        """Stub for the enhanced academic workflow."""
        # Reuse original workflow for the test harness.
        return await self.original_workflow(topic, **kwargs)

    async def generate_article(self, topic: str, **kwargs):
        if self.config.academic_sources:
            return await self.academic_workflow(topic, **kwargs)
        return await self.original_workflow(topic, **kwargs)
