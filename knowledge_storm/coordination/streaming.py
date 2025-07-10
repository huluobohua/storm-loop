import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict

@dataclass
class ResearchChunk:
    chunk_id: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]

    def is_valid(self) -> bool:
        return bool(self.data)

class StreamingResearchProcessor:
    def __init__(self, chunk_size: int = 10):
        self.chunk_size = chunk_size

    async def start_streaming_research(self, topic: str) -> AsyncGenerator[ResearchChunk, None]:
        for i in range(5):
            await asyncio.sleep(0.05)
            data = {"topic": topic, "sources": [f"src_{i}_{j}" for j in range(self.chunk_size)]}
            meta = {"index": i}
            yield ResearchChunk(i, data, meta)

    async def stream_analysis(self, stream: AsyncGenerator[ResearchChunk, None]) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunk in stream:
            await asyncio.sleep(0.01)
            yield {"chunk": chunk.chunk_id}
