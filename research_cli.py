#!/usr/bin/env python3
"""
Elite research CLI following all engineering standards.

TDD-tested, SOLID principles, Sandi Metz rules, secure API handling.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from research import ResearchService, ResearchConfig
from research.factory import ResearchServiceFactory


class ResearchCLI:
    """Simple CLI for research service - no blocking input()."""
    
    def __init__(self, config: ResearchConfig):
        """Initialize with configuration."""
        self.service = ResearchServiceFactory.create(config)
        self.output_dir = "results"
    
    async def generate_report(self, topic: str) -> str:
        """Generate research report for topic."""
        print(f"🔬 Generating research for: {topic}")
        result = await self.service.generate_research(topic)
        output_path = self._save_results(topic, result)
        self._display_summary(result, output_path)
        return output_path
    
    def _save_results(self, topic: str, result: dict) -> str:
        """Save research results to files."""
        sanitized = self._sanitize_topic(topic)
        topic_dir = os.path.join(self.output_dir, f"{sanitized}_research")
        os.makedirs(topic_dir, exist_ok=True)
        
        files = {
            "queries.txt": "\n".join(result['queries']),
            "outline.txt": result['outline'],
            "article.txt": result['polished_article'],
            "metadata.json": self._build_metadata(topic, result)
        }
        
        for filename, content in files.items():
            filepath = os.path.join(topic_dir, filename)
            with open(filepath, 'w') as f:
                if filename.endswith('.json'):
                    json.dump(content, f, indent=2)
                else:
                    f.write(str(content))
        
        return topic_dir
    
    def _sanitize_topic(self, topic: str) -> str:
        """Sanitize topic for filename."""
        import re
        clean = re.sub(r'[^\w\s-]', '', topic.lower())
        return re.sub(r'[-\s]+', '_', clean)[:50]
    
    def _build_metadata(self, topic: str, result: dict) -> dict:
        """Build metadata for research."""
        return {
            'topic': topic,
            'generated_at': datetime.now().isoformat(),
            'queries_count': len(result['queries']),
            'sources_count': len(result['search_results'])
        }
    
    def _display_summary(self, result: dict, output_path: str):
        """Display research summary."""
        print(f"✅ Research complete!")
        print(f"📁 Saved to: {output_path}")
        print(f"📋 Queries: {len(result['queries'])}")
        print(f"🔍 Sources: {len(result['search_results'])}")
        article_len = len(result['polished_article'])
        words = len(result['polished_article'].split())
        print(f"📄 Article: {article_len} chars, {words} words")


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python research_cli.py '<research topic>'")
        print("Example: python research_cli.py 'AI advances in healthcare'")
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:])
    
    # Get API keys from environment
    search_key = os.getenv('SERPAPI_KEY')
    llm_key = os.getenv('OPENAI_API_KEY')
    
    if not search_key or not llm_key:
        print("❌ Missing API keys:")
        print("  Set SERPAPI_KEY environment variable")
        print("  Set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    try:
        config = ResearchConfig(
            search_api_key=search_key,
            llm_api_key=llm_key
        )
        
        cli = ResearchCLI(config)
        await cli.generate_report(topic)
        
    except Exception as e:
        print(f"❌ Research failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())