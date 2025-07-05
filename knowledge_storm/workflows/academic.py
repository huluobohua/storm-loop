from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from knowledge_storm.hybrid_engine import Article, WorkflowRunner
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - optional dependency
    from knowledge_storm.storm_wiki.engine import STORMWikiRunner


@dataclass
class AcademicWorkflowRunner(WorkflowRunner):
    """Run the full STORM academic workflow using a STORMWikiRunner."""

    storm_runner: "STORMWikiRunner"

    async def run_academic_workflow(self, topic: str, **kwargs: Any) -> Article:
        await self.storm_runner.run(
            topic=topic,
            do_research=True,
            do_generate_outline=True,
            do_generate_article=True,
            do_polish_article=True,
        )
        self.storm_runner.post_run()

        article_dir = os.path.join(
            self.storm_runner.args.output_dir,
            topic.replace(" ", "_").replace("/", "_"),
        )
        article_path = os.path.join(article_dir, "storm_gen_article_polished.txt")
        content = ""
        if os.path.exists(article_path):
            with open(article_path, "r", encoding="utf-8") as f:
                content = f.read()
        return Article(topic=topic, content=content, metadata={"type": "academic"})

    async def run_original_workflow(self, topic: str, **kwargs: Any) -> Article:
        return await self.run_academic_workflow(topic, **kwargs)
