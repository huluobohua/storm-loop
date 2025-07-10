"""Streaming processor yielding research chunks for analysis."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List


@dataclass
class ResearchChunk:
    """Chunk of research data."""

    chunk_id: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    is_final: bool = False

    def is_valid(self) -> bool:
        return bool(self.data)


class StreamingResearchProcessor:
    """Generate and process research chunks asynchronously."""

    def __init__(self, chunk_size: int = 5) -> None:
        self.chunk_size = chunk_size

    async def start_streaming_research(self, topic: str) -> AsyncGenerator[ResearchChunk, None]:
        for i in range(5):
            await asyncio.sleep(0.02)
            chunk = ResearchChunk(
                i,
                {"topic": topic, "sources": [f"{topic}_{j}" for j in range(self.chunk_size)]},
                {"stage": "research"},
                i == 4,
            )
            yield chunk

    async def stream_analysis(self, research_stream: AsyncGenerator[ResearchChunk, None]) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunk in research_stream:
            result = await self._analyze_chunk(chunk)
            yield result

    async def _analyze_chunk(self, chunk: ResearchChunk) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"chunk_id": chunk.chunk_id, "analysis": "ok"}
