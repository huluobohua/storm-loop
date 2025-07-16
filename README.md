# STORM-Academic Hybrid System

An AI-assisted research and writing platform that enhances the original STORM (Synthesis of Topic Outline through Retrieval and Multi-perspective question asking) with academic rigor and verification capabilities.

## 🎯 System Overview

**Primary System**: Enhanced STORM engine with academic research capabilities  
**Core Enhancement**: Citation verification and quality assurance for academic rigor  
**Architecture**: Multi-agent system with specialized academic research workflow

### Key Features

- **Single-Pass Research Generation**: Streamlined multi-agent workflow for efficient research
- **Real-Time Fact Verification**: Claims are verified against authoritative sources during generation
- **Targeted Fixes**: Only unsupported claims are corrected, preserving accurate content
- **PRISMA Integration**: 80% automation at 80% confidence for systematic literature reviews
- **Memory Learning**: System learns from successful research patterns for improved accuracy

### Key Components

- **Enhanced STORM Engine** - Academic workflow selector and hybrid processing
- **Citation Verification** - Real-time academic source validation
- **Multi-Agent Architecture** - Specialized agents for research, criticism, and verification
- **Academic Workflow** - Comprehensive research pipeline with quality gates

## 🏗️ Architecture Clarification

This system combines:
1. **STORM Framework** - Original topic outline and article generation
2. **Academic Enhancements** - Research verification and quality assurance
3. **Verification Services** - Citation and claim validation

The system focuses on enhancing STORM with academic verification capabilities.

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

This approach enhances the original STORM framework with verification capabilities for improved accuracy and academic rigor.
