#!/usr/bin/env python3
"""
Main entry point for the STORM research system
Uses the abstracted research_generator.py as the backend
"""

import asyncio
from research_generator import ResearchGenerator

async def main():
    """Main entry point for research generation"""
    from research_generator import main as research_main
    await research_main()

if __name__ == "__main__":
    asyncio.run(main())