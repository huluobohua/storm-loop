import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict


@dataclass
class ResearchChunk:
    chunk_id: int
    data: Dict[str, Any]
    is_final: bool = False

    def is_valid(self) -> bool:
        return bool(self.data)


class StreamingResearchProcessor:
    """Provide research results in chunks."""

    def __init__(self, chunk_count: int = 3) -> None:
        self.chunk_count = chunk_count

    async def start_streaming_research(self, topic: str) -> AsyncGenerator[ResearchChunk, None]:
        for i in range(self.chunk_count):
            await asyncio.sleep(0.05)
            yield ResearchChunk(i, {"topic": topic, "index": i}, i == self.chunk_count - 1)
