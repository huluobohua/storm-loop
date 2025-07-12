import json
import asyncio
from pathlib import Path
from datetime import datetime
import click


@click.command("init")
@click.option("--topic", required=True, help="Research topic or question")
@click.option("--domain", default="general", type=click.Choice(["medical", "cs", "general"]), help="Domain of study")
@click.option("--output-dir", default=".", help="Output directory for project files")
@click.option("--generate-search-strategy", is_flag=True, help="Generate comprehensive search strategy")
def init_cmd(topic: str, domain: str, output_dir: str, generate_search_strategy: bool) -> None:
    """Initialize a new systematic review project with PRISMA Assistant."""
    
    click.echo(f"🚀 Initializing PRISMA systematic review project")
    click.echo(f"📋 Topic: {topic}")
    click.echo(f"🏷️  Domain: {domain}")
    
    try:
        # Create project structure
        project_dir = Path(output_dir) / "prisma_review"
        _create_project_structure(project_dir)
        
        # Generate project configuration
        config = _create_project_config(topic, domain)
        _save_config(config, project_dir / "project_config.json")
        
        # Generate search strategy if requested
        if generate_search_strategy:
            click.echo("🔍 Generating search strategy...")
            search_strategy = asyncio.run(_generate_search_strategy(topic, domain))
            _save_search_strategy(search_strategy, project_dir / "search_strategy.json")
            _create_search_documentation(search_strategy, project_dir / "search_strategy.md")
        
        # Create template files
        _create_template_files(project_dir, topic, domain)
        
        # Display next steps
        _display_next_steps(project_dir, topic)
        
        click.echo(f"✅ Project initialized in {project_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


def _create_project_structure(project_dir: Path) -> None:
    """Create the project directory structure."""
    dirs_to_create = [
        project_dir,
        project_dir / "data" / "raw",
        project_dir / "data" / "processed",
        project_dir / "results",
        project_dir / "docs",
        project_dir / "templates"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create .gitignore
    gitignore_content = """# Data files
*.csv
*.xlsx
*.json
!project_config.json
!search_strategy.json

# Results
results/screening_*.json
results/stats_*.json

# Temporary files
*.tmp
*.log

# OS files
.DS_Store
Thumbs.db
"""
    
    with open(project_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)


def _create_project_config(topic: str, domain: str) -> dict:
    """Create project configuration."""
    return {
        "project_info": {
            "title": f"Systematic Review: {topic}",
            "research_question": topic,
            "domain": domain,
            "created_date": datetime.now().isoformat(),
            "version": "1.0.0"
        },
        "screening_config": {
            "confidence_threshold": 0.8,
            "target_auto_decision_rate": 0.8,
            "include_patterns": [],
            "exclude_patterns": []
        },
        "databases": {
            "medical": ["pubmed", "scopus", "cochrane", "embase"],
            "cs": ["ieee", "acm", "scopus", "web_of_science"],
            "general": ["scopus", "web_of_science"]
        }.get(domain, ["scopus", "web_of_science"]),
        "workflow": {
            "current_stage": "initialization",
            "completed_stages": ["initialization"],
            "next_stage": "search_execution"
        }
    }


def _save_config(config: dict, filepath: Path) -> None:
    """Save project configuration to JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


async def _generate_search_strategy(topic: str, domain: str) -> dict:
    """Generate comprehensive search strategy."""
    from knowledge_storm.prisma_assistant import SearchStrategyBuilder
    
    builder = SearchStrategyBuilder()
    strategy = builder.build_search_strategy(topic, domain)
    
    # Convert to dictionary for serialization
    return {
        'research_question': strategy.research_question,
        'pico_elements': strategy.pico_elements,
        'search_queries': strategy.search_queries,
        'inclusion_criteria': strategy.inclusion_criteria,
        'exclusion_criteria': strategy.exclusion_criteria,
        'date_range': strategy.date_range,
        'languages': strategy.languages
    }


def _save_search_strategy(strategy: dict, filepath: Path) -> None:
    """Save search strategy to JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(strategy, f, indent=2, ensure_ascii=False)


def _create_search_documentation(strategy: dict, filepath: Path) -> None:
    """Create human-readable search strategy documentation."""
    doc = f"""# Search Strategy

## Research Question
{strategy['research_question']}

## PICO Elements
"""
    
    for element, terms in strategy['pico_elements'].items():
        if terms:
            doc += f"- **{element.title()}**: {', '.join(terms)}\n"
    
    doc += f"\n## Date Range\n"
    if strategy['date_range']:
        doc += f"- From: {strategy['date_range'][0]}\n"
        doc += f"- To: {strategy['date_range'][1]}\n"
    
    doc += f"\n## Languages\n"
    for lang in strategy['languages']:
        doc += f"- {lang}\n"
    
    doc += f"\n## Inclusion Criteria\n"
    for criteria in strategy['inclusion_criteria']:
        doc += f"- {criteria}\n"
    
    doc += f"\n## Exclusion Criteria\n"
    for criteria in strategy['exclusion_criteria']:
        doc += f"- {criteria}\n"
    
    doc += f"\n## Database Queries\n"
    for db, query in strategy['search_queries'].items():
        doc += f"\n### {db.upper()}\n```\n{query}\n```\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(doc)


def _create_template_files(project_dir: Path, topic: str, domain: str) -> None:
    """Create template files for the project."""
    
    # Sample papers template (CSV)
    papers_template = """id,title,abstract,authors,year,journal,doi,url
1,"Sample Paper Title","This is a sample abstract for demonstration purposes...","Author1;Author2;Author3",2024,"Journal of Examples","10.1000/sample","https://example.com/paper1
2,"Another Sample Paper","Another sample abstract...","Author4;Author5",2023,"Sample Journal","10.1000/sample2","https://example.com/paper2
"""
    
    with open(project_dir / "templates" / "sample_papers.csv", "w") as f:
        f.write(papers_template)
    
    # README template
    readme_content = f"""# Systematic Review: {topic}

## Overview
This project uses PRISMA Assistant for systematic review of literature on: {topic}

## Project Structure
- `data/raw/` - Original search results from databases
- `data/processed/` - Processed and cleaned data
- `results/` - Screening results and statistics
- `docs/` - Documentation and reports
- `templates/` - Template files and examples

## Usage

### 1. Prepare Your Data
Place your paper data in CSV or JSON format in `data/raw/`.
Use the template in `templates/sample_papers.csv` as a guide.

### 2. Screen Papers
```bash
prisma-assistant screen --input data/raw/papers.csv --output results/screening_results.json
```

### 3. Generate Statistics
```bash
prisma-assistant stats --results results/screening_results.json
```

### 4. Export Results
```bash
prisma-assistant export --results results/screening_results.json --format prisma-flow
```

## Domain
{domain}

## Generated
{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    with open(project_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # PRISMA checklist template
    checklist_content = """# PRISMA 2020 Checklist

## Identification
- [ ] Database searches documented
- [ ] Search strategies saved
- [ ] Date ranges specified

## Screening
- [ ] Inclusion/exclusion criteria defined
- [ ] Screening performed with PRISMA Assistant
- [ ] Screening statistics generated
- [ ] Human review completed for uncertain papers

## Eligibility
- [ ] Full-text assessment completed
- [ ] Final inclusion/exclusion decisions made
- [ ] PRISMA flow diagram created

## Analysis
- [ ] Data extraction completed
- [ ] Risk of bias assessment
- [ ] Statistical analysis (if applicable)

## Reporting
- [ ] Results written up
- [ ] Limitations discussed
- [ ] Conclusions stated
"""
    
    with open(project_dir / "docs" / "prisma_checklist.md", "w") as f:
        f.write(checklist_content)


def _display_next_steps(project_dir: Path, topic: str) -> None:
    """Display next steps for the user."""
    click.echo("\n" + "="*50)
    click.echo("🎯 NEXT STEPS")
    click.echo("="*50)
    
    click.echo("\n1. 📁 Project Structure Created:")
    click.echo(f"   cd {project_dir}")
    
    click.echo("\n2. 📄 Prepare Your Paper Data:")
    click.echo(f"   - Place CSV/JSON files in data/raw/")
    click.echo(f"   - Use templates/sample_papers.csv as a guide")
    
    click.echo("\n3. 🔍 Screen Papers:")
    click.echo(f"   prisma-assistant screen --input data/raw/papers.csv --output results/screening.json")
    
    click.echo("\n4. 📊 Generate Statistics:")
    click.echo(f"   prisma-assistant stats --results results/screening.json")
    
    click.echo("\n5. 📤 Export Results:")
    click.echo(f"   prisma-assistant export --results results/screening.json --format prisma-flow")
    
    click.echo("\n6. 📋 Follow PRISMA Guidelines:")
    click.echo(f"   - Review docs/prisma_checklist.md")
    click.echo(f"   - Complete human review of uncertain papers")
    click.echo(f"   - Generate final PRISMA flow diagram")
    
    click.echo("\n💡 For help: prisma-assistant --help")
    click.echo("="*50)
