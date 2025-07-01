import os


class Settings:
    """Configuration values for the system."""

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))


def get_settings() -> Settings:
    return Settings()
