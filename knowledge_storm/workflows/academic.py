from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from knowledge_storm.hybrid_engine import Article, WorkflowRunner
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - optional dependency
    from knowledge_storm.storm_wiki.engine import STORMWikiRunner


def slugify(text: str) -> str:
    """Convert a string to a safe filename using robust sanitization."""
    # Remove or replace unsafe characters
    # Remove special chars except words/spaces/hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)    # Replace spaces and hyphens with underscores
    text = text.strip('_')                 # Remove leading/trailing underscores
    return text or 'unnamed'               # Fallback for empty strings


@dataclass
class AcademicWorkflowRunner(WorkflowRunner):
    """Run the full STORM academic workflow using a STORMWikiRunner."""

    storm_runner: "STORMWikiRunner"
    output_filename: str = "storm_gen_article_polished.txt"

    def _get_article_path(self, topic: str) -> str:
        """Get the path to the generated article file."""
        safe_topic = slugify(topic)
        article_dir = os.path.join(self.storm_runner.args.output_dir, safe_topic)
        return os.path.join(article_dir, self.output_filename)

    def _load_article_content(self, article_path: str) -> str:
        """Load article content from file if it exists."""
        if os.path.exists(article_path):
            with open(article_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    async def run_academic_workflow(self, topic: str, **kwargs: Any) -> Article:
        await self.storm_runner.run(
            topic=topic,
            do_research=True,
            do_generate_outline=True,
            do_generate_article=True,
            do_polish_article=True,
        )
        self.storm_runner.post_run()

        article_path = self._get_article_path(topic)
        content = self._load_article_content(article_path)
        return Article(topic=topic, content=content, metadata={"type": "academic"})

    async def run_original_workflow(self, topic: str, **kwargs: Any) -> Article:
        return await self.run_academic_workflow(topic, **kwargs)
