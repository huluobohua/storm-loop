class STORMConfig:
    """Configuration for STORM behavior modes."""

    def __init__(self, mode: str = "hybrid") -> None:
        self.mode = mode
        self.academic_sources = mode in ["academic", "hybrid"]
        self.quality_gates = mode in ["academic", "hybrid"]
        self.citation_verification = mode == "academic"
        self.real_time_verification = mode == "academic"

