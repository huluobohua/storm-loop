# STORM Research Loop - Universal Research Generator

A comprehensive research report generation system that can produce high-quality research articles on any topic using AI-powered search, analysis, and writing.

## Quick Start

### Basic Usage
```bash
# Run the interactive research generator
python research_generator.py

# Or use the main entry point
python run_research.py
```

### E2E Research Pipeline

The system follows this workflow:
1. **Topic Input**: User provides any research topic
2. **Query Generation**: LLM generates 8 focused search queries  
3. **User Approval**: Interactive approval/modification of queries
4. **Search**: Real Google searches via SerpAPI
5. **Outline**: AI-generated research outline
6. **Article**: Comprehensive research article (3000+ words)  
7. **Polish**: Publication-ready final version
8. **Save**: Organized output with all artifacts

### User Approval Process

When queries are generated, you have these options:
- **"yes"/"y"** - Approve and continue with research
- **"no"/"n"** - Regenerate queries without instructions
- **"modify: <instructions>"** - Regenerate with specific feedback
- **"quit"/"q"** - Exit the system

Example:
```
Do you approve these search queries?
Options:
  'yes' or 'y' - Approve and continue
  'no' or 'n' - Regenerate without instructions  
  'modify: focus more on recent developments' - Regenerate with your specific instructions
  'quit' or 'q' - Exit

Your choice: modify: focus more on recent developments and practical applications
```

## Requirements

### Environment Variables
Create `.env` file with:
```bash
OPENAI_API_KEY=your_openai_key
SERPAPI_KEY=your_serpapi_key
```

### Dependencies  
```bash
pip install openai python-dotenv requests dspy-ai
```

## Output Structure

Each research generates:
```
results/
└── {topic_name}_research/
    └── {sanitized_topic}/
        ├── approved_search_queries.txt    # Final approved queries
        ├── raw_search_results.json        # All search data
        ├── storm_gen_outline.txt          # Research outline
        ├── storm_gen_article.txt          # Draft article
        ├── storm_gen_article_polished.txt # Final article
        └── run_config.json                # Metadata
```

## Features

- **Universal Topics**: Works with any research subject
- **Interactive Approval**: User controls search query quality
- **High-Quality Output**: 3000+ word comprehensive articles
- **Real Search Data**: Uses SerpAPI for Google search results
- **Publication Ready**: Polished, structured final articles
- **Complete Artifacts**: Saves all intermediate and final outputs

## Architecture

### Core Components

- **`research_generator.py`**: Main research generation backend
- **`run_research.py`**: Entry point for E2E pipeline  
- **`knowledge_storm/`**: Supporting STORM framework modules
- **`knowledge_storm/rm.py`**: Search engine integrations (SerpAPI, Perplexity)
- **`knowledge_storm/lm.py`**: Language model wrappers (OpenAI, DeepSeek, etc.)

### Search Engines

- **SerpApiRM**: Google search via SerpAPI
- **PerplexityRM**: Perplexity AI search  
- **TavilyRM**: Tavily search engine (coming soon)

### Language Models

- **OpenAIModel**: GPT models with token tracking
- **DeepSeekModel**: DeepSeek API integration
- **TogetherClient**: Together AI models
- **Custom Models**: Extensible LM framework

## Example Research Topics

The system handles any topic effectively:

- **Technology**: "Quantum Computing Advances 2020-2025" 
- **Science**: "CRISPR Gene Therapy Clinical Trials"
- **Business**: "Remote Work Impact on Corporate Culture"
- **History**: "Women's Contributions to Early Computer Science"
- **Health**: "Microbiome Research and Mental Health"
- **Environment**: "Carbon Capture Technology Developments"

## Quality Assurance

- **Real Search Data**: No synthetic or hallucinated sources
- **Citation Accuracy**: All claims linked to search results  
- **Comprehensive Coverage**: Multi-perspective analysis
- **Professional Style**: Academic writing standards
- **User Control**: Approval workflow ensures relevance
- **Reproducible**: All artifacts and metadata saved

---

## Legacy STORM-Academic Components

The system includes enhanced STORM framework components:
- **Enhanced STORM Engine** - Academic workflow with verification
- **Citation Verification** - Real-time academic source validation
- **Multi-Agent Architecture** - Specialized research agents
- **Academic Workflow** - Comprehensive research pipeline

**Previous quantum computing research example**: Produced 18,472 character, 2,326 word publication-ready article with full citations and comprehensive coverage.