import json
import asyncio
from pathlib import Path
import click

from prisma_assistant.core import get_screener


@click.command("screen")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Input file with papers")
@click.option("--output", "output_file", required=True, type=click.Path(), help="Output results JSON")
@click.option("--confidence-threshold", default=0.8, show_default=True, type=float)
@click.option("--include-patterns", default="", help="Comma-separated inclusion patterns")
@click.option("--exclude-patterns", default="", help="Comma-separated exclusion patterns")
def screen_cmd(input_file: str, output_file: str, confidence_threshold: float, 
               include_patterns: str, exclude_patterns: str) -> None:
    """Screen a batch of papers using PRISMA 80/20 methodology."""
    
    click.echo(f"🔍 Screening papers from {input_file}")
    click.echo(f"📊 Confidence threshold: {confidence_threshold}")
    
    try:
        # Parse patterns
        include_list = [p.strip() for p in include_patterns.split(",")] if include_patterns else None
        exclude_list = [p.strip() for p in exclude_patterns.split(",")] if exclude_patterns else None
        
        # Load papers from input file
        papers = _load_papers_from_file(input_file)
        click.echo(f"📄 Loaded {len(papers)} papers")
        
        # Get screener and run screening
        screener = get_screener(
            include_patterns=include_list,
            exclude_patterns=exclude_list,
            threshold=confidence_threshold
        )
        
        # Run screening (async)
        results = asyncio.run(_run_screening(screener, papers))
        
        # Save results
        _save_results(results, output_file)
        
        # Display summary
        _display_summary(results)
        
        click.echo(f"✅ Results saved to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


async def _run_screening(screener, papers):
    """Run the actual screening process."""
    return await screener.screen_papers(papers)


def _load_papers_from_file(input_file: str):
    """Load papers from input file (JSON or CSV format)."""
    from knowledge_storm.prisma_assistant import Paper
    
    path = Path(input_file)
    papers = []
    
    if path.suffix.lower() == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for paper_data in data:
                papers.append(Paper(
                    id=paper_data.get('id', str(len(papers))),
                    title=paper_data.get('title', ''),
                    abstract=paper_data.get('abstract', ''),
                    authors=paper_data.get('authors', []),
                    year=paper_data.get('year', 2024),
                    journal=paper_data.get('journal', ''),
                    doi=paper_data.get('doi'),
                    url=paper_data.get('url')
                ))
    else:
        # Handle CSV format
        import csv
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                papers.append(Paper(
                    id=row.get('id', str(i)),
                    title=row.get('title', ''),
                    abstract=row.get('abstract', ''),
                    authors=row.get('authors', '').split(';') if row.get('authors') else [],
                    year=int(row.get('year', 2024)) if row.get('year') else 2024,
                    journal=row.get('journal', ''),
                    doi=row.get('doi'),
                    url=row.get('url')
                ))
    
    return papers


def _save_results(results: dict, output_file: str) -> None:
    """Save screening results to JSON file."""
    # Convert Paper objects to dictionaries for JSON serialization
    def paper_to_dict(paper):
        return {
            'id': paper.id,
            'title': paper.title,
            'abstract': paper.abstract,
            'authors': paper.authors,
            'year': paper.year,
            'journal': paper.journal,
            'doi': paper.doi,
            'url': paper.url,
            'screening_decision': paper.screening_decision,
            'exclusion_reason': paper.exclusion_reason,
            'confidence_score': paper.confidence_score
        }
    
    serializable_results = {
        'definitely_exclude': [paper_to_dict(p) for p in results['definitely_exclude']],
        'definitely_include': [paper_to_dict(p) for p in results['definitely_include']],
        'needs_human_review': [paper_to_dict(p) for p in results['needs_human_review']],
        'exclusion_stats': dict(results['exclusion_stats']),
        'confidence_distribution': results['confidence_distribution'],
        'performance_metrics': results['performance_metrics']
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)


def _display_summary(results: dict) -> None:
    """Display screening summary statistics."""
    metrics = results['performance_metrics']
    
    click.echo("\n📈 Screening Summary:")
    click.echo(f"   Total papers: {metrics['total_papers']}")
    click.echo(f"   Auto-decided: {metrics['auto_decided']} ({metrics['auto_decision_rate']:.1%})")
    click.echo(f"   Human review needed: {len(results['needs_human_review'])}")
    
    click.echo("\n🎯 Decisions:")
    click.echo(f"   ✅ Include: {len(results['definitely_include'])}")
    click.echo(f"   ❌ Exclude: {len(results['definitely_exclude'])}")
    click.echo(f"   🤔 Uncertain: {len(results['needs_human_review'])}")
    
    if results['exclusion_stats']:
        click.echo("\n📊 Exclusion reasons:")
        for reason, count in results['exclusion_stats'].items():
            click.echo(f"   - {reason}: {count}")
    
    target_met = "✅" if metrics.get('target_achieved', False) else "⚠️"
    click.echo(f"\n{target_met} 80/20 Target: {metrics['auto_decision_rate']:.1%} auto-decided (target: 80%)")
