# VERIFY Research System

VERIFY-powered Academic Research Platform: Fact-verified AI research with integrated PRISMA Assistant for systematic literature reviews.

## Key Features

- **Single-Pass Research Generation**: Streamlined multi-agent workflow for efficient research
- **Real-Time Fact Verification**: Claims are verified against authoritative sources during generation
- **Targeted Fixes**: Only unsupported claims are corrected, preserving accurate content
- **PRISMA Integration**: 80% automation at 80% confidence for systematic literature reviews
- **Memory Learning**: System learns from successful research patterns for improved accuracy

## Installation

Install the entire system in development mode:

```bash
pip install -e .
```

## Usage

### PRISMA Assistant CLI

After installation, use the PRISMA Assistant CLI for systematic literature reviews:

```bash
prisma-assistant --help
prisma-assistant init --topic "diabetes treatment" --domain "medical"
prisma-assistant screen --input papers.csv --output results.json
```

### VERIFY System

The VERIFY system provides fact-verified research generation through the multi-agent knowledge curation module:

```python
from knowledge_storm.modules.multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule

# Initialize with your configuration
module = MultiAgentKnowledgeCurationModule(config)

# Generate verified research
result = await module.research(topic="your research topic")
```

## Architecture

The system uses a streamlined three-agent workflow:

1. **Research Planner**: Generates structured research plans
2. **Academic Researcher**: Conducts comprehensive research
3. **Citation Verifier**: Fact-checks claims and provides targeted corrections

This replaces the previous storm-loop approach with a more efficient verify-based system focused on accuracy and automation.
