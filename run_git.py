#!/usr/bin/env python3
import subprocess
import os

# Change to the project directory
os.chdir('/Users/melvinbreton/Dropbox/AI_projects/storm-loop')

# Git commands to execute
commands = [
    ['git', 'add', 'knowledge_storm/modules/prisma/'],
    ['git', 'add', 'knowledge_storm/modules/prisma_assistant_refactored.py'],
    ['git', 'add', 'knowledge_storm/agents/prisma_screener.py'],
    ['git', 'add', 'knowledge_storm/workflows/systematic_review.py'],
    ['git', 'status', '--short'],
    ['git', 'commit', '-m', '''refactor: Break down monolithic PRISMA assistant into focused modules

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
- Improves maintainability and testability'''],
    ['git', 'push']
]

# Execute each command
for cmd in commands:
    print(f"\nExecuting: {' '.join(cmd[:3])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        break

print("\nGit operations completed!")