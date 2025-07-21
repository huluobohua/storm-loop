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
        topic_dir = self._create_output_directory(topic)
        files = self._prepare_output_files(topic, result)
        self._write_all_files(topic_dir, files)
        return topic_dir
    
    def _create_output_directory(self, topic: str) -> str:
        """Create output directory for topic."""
        sanitized = self._sanitize_topic(topic)
        topic_dir = os.path.join(self.output_dir, f"{sanitized}_research")
        os.makedirs(topic_dir, exist_ok=True)
        return topic_dir
    
    def _prepare_output_files(self, topic: str, result: dict) -> dict:
        """Prepare files for output."""
        text_files = self._prepare_text_files(result)
        metadata = {"metadata.json": self._build_metadata(topic, result)}
        return {**text_files, **metadata}
    
    def _prepare_text_files(self, result: dict) -> dict:
        """Prepare text output files."""
        return {
            "queries.txt": "\n".join(result['queries']),
            "outline.txt": result['outline'],
            "article.txt": result['polished_article']
        }
    
    def _write_all_files(self, topic_dir: str, files: dict):
        """Write all files to directory."""
        for filename, content in files.items():
            self._write_single_file(topic_dir, filename, content)
    
    def _write_single_file(self, topic_dir: str, filename: str, content):
        """Write single file to directory."""
        filepath = os.path.join(topic_dir, filename)
        with open(filepath, 'w') as f:
            self._write_content(f, filename, content)
    
    def _write_content(self, file_handle, filename: str, content):
        """Write content to file handle."""
        if filename.endswith('.json'):
            json.dump(content, file_handle, indent=2)
        else:
            file_handle.write(str(content))
    
    def _sanitize_topic(self, topic: str) -> str:
        """Sanitize topic for filename."""
        import re
        clean = re.sub(r'[^\w\s-]', '', topic.lower())
        return re.sub(r'[-\s]+', '_', clean)[:50]
    
    def _build_metadata(self, topic: str, result: dict) -> dict:
        """Build metadata for research."""
        basic_info = {'topic': topic, 'generated_at': datetime.now().isoformat()}
        counts = self._build_counts(result)
        return {**basic_info, **counts}
    
    def _build_counts(self, result: dict) -> dict:
        """Build count statistics."""
        return {
            'queries_count': len(result['queries']),
            'sources_count': len(result['search_results'])
        }
    
    def _display_summary(self, result: dict, output_path: str):
        """Display research summary."""
        self._print_completion_status(output_path)
        self._print_statistics(result)
    
    def _print_completion_status(self, output_path: str):
        """Print completion status."""
        print(f"✅ Research complete!")
        print(f"📁 Saved to: {output_path}")
    
    def _print_statistics(self, result: dict):
        """Print research statistics."""
        print(f"📋 Queries: {len(result['queries'])}")
        print(f"🔍 Sources: {len(result['search_results'])}")
        self._print_article_stats(result['polished_article'])
    
    def _print_article_stats(self, article: str):
        """Print article statistics."""
        article_len, words = len(article), len(article.split())
        print(f"📄 Article: {article_len} chars, {words} words")


async def main():
    """Main CLI entry point."""
    topic = _validate_arguments_and_get_topic()
    api_keys = _get_and_validate_api_keys()
    await _execute_research(topic, api_keys)

def _validate_arguments_and_get_topic() -> str:
    """Validate command line arguments and extract topic."""
    if len(sys.argv) < 2:
        _print_usage_and_exit()
    return " ".join(sys.argv[1:])

def _print_usage_and_exit():
    """Print usage instructions and exit."""
    print("Usage: python research_cli.py '<research topic>'")
    print("Example: python research_cli.py 'AI advances in healthcare'")
    sys.exit(1)

def _get_and_validate_api_keys() -> tuple:
    """Get and validate API keys from environment."""
    search_key = os.getenv('SERPAPI_KEY')
    llm_key = os.getenv('OPENAI_API_KEY')
    _validate_api_keys(search_key, llm_key)
    return search_key, llm_key

def _validate_api_keys(search_key: str, llm_key: str):
    """Validate that required API keys are present."""
    if not search_key or not llm_key:
        _print_missing_keys_and_exit()

def _print_missing_keys_and_exit():
    """Print missing keys message and exit."""
    print("❌ Missing API keys:")
    print("  Set SERPAPI_KEY environment variable")  
    print("  Set OPENAI_API_KEY environment variable")
    sys.exit(1)

async def _execute_research(topic: str, api_keys: tuple):
    """Execute research with error handling."""
    try:
        config = _create_config(api_keys)
        cli = ResearchCLI(config)
        await cli.generate_report(topic)
    except Exception as e:
        _handle_research_error(e)

def _create_config(api_keys: tuple) -> 'ResearchConfig':
    """Create research configuration from API keys."""
    search_key, llm_key = api_keys
    return ResearchConfig(search_api_key=search_key, llm_api_key=llm_key)

def _handle_research_error(error: Exception):
    """Handle research execution errors."""
    print(f"❌ Research failed: {error}")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())