#!/bin/bash

# Add new prisma module directory
git add knowledge_storm/modules/prisma/

# Add refactored main file
git add knowledge_storm/modules/prisma_assistant_refactored.py

# Add modified files
git add knowledge_storm/agents/prisma_screener.py
git add knowledge_storm/workflows/systematic_review.py

# Commit with detailed message
git commit -m "refactor: Break down monolithic PRISMA assistant into focused modules

- Extract SearchStrategyBuilder to search_strategy.py (142 lines)
- Extract ScreeningAssistant to screening.py (261 lines)
- Extract DataExtractionHelper to extraction.py (62 lines)
- Extract ZeroDraftGenerator to draft_generation.py (65 lines)
- Create core.py for shared data models (70 lines)
- Create main coordinator in prisma_assistant_refactored.py (108 lines)
- Update imports in agents and workflows

Addresses PR #143 critical feedback:
- CRITICAL: Architectural Violation - Single file with 1,191 lines violates SRP
- Break into focused, single-responsibility modules
- Each module now has clear, focused purpose
- Improves maintainability and testability"

# Push to current branch
git push

echo "Git operations completed!"