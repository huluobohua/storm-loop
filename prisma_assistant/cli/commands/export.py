import json
import csv
from pathlib import Path
from datetime import datetime
import click


@click.command("export")
@click.option("--results", "results_file", required=True, type=click.Path(exists=True), help="Results JSON from screening")
@click.option("--format", "output_format", required=True, type=click.Choice(["prisma-flow", "csv", "json", "markdown"]))
@click.option("--output", "output_file", required=False, type=click.Path())
@click.option("--include-abstracts", is_flag=True, help="Include abstracts in export (CSV/markdown only)")
def export_cmd(results_file: str, output_format: str, output_file: str | None, include_abstracts: bool) -> None:
    """Export screening results to various formats for reporting and analysis."""
    
    click.echo(f"📤 Exporting {results_file} as {output_format}")
    
    try:
        # Load results
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Generate output filename if not provided
        if not output_file:
            base_name = Path(results_file).stem
            extensions = {
                "prisma-flow": "md",
                "csv": "csv", 
                "json": "json",
                "markdown": "md"
            }
            output_file = f"{base_name}_export.{extensions[output_format]}"
        
        # Export based on format
        if output_format == "prisma-flow":
            _export_prisma_flow(results, output_file)
        elif output_format == "csv":
            _export_csv(results, output_file, include_abstracts)
        elif output_format == "json":
            _export_json(results, output_file)
        elif output_format == "markdown":
            _export_markdown(results, output_file, include_abstracts)
        
        click.echo(f"✅ Export completed: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


def _export_prisma_flow(results: dict, output_file: str) -> None:
    """Export results as PRISMA flow diagram documentation."""
    metrics = results.get('performance_metrics', {})
    
    content = f"""# PRISMA Flow Diagram Data

## Identification
- **Records identified through database searching**: [TO BE FILLED]
- **Additional records identified through other sources**: [TO BE FILLED]

## Screening
- **Records after duplicates removed**: {metrics.get('total_papers', 0)}
- **Records screened**: {metrics.get('total_papers', 0)}
- **Records excluded**: {len(results.get('definitely_exclude', []))}

### Exclusion Reasons:
"""
    
    exclusion_stats = results.get('exclusion_stats', {})
    for reason, count in exclusion_stats.items():
        content += f"- {reason.replace('_', ' ').title()}: {count}\n"
    
    content += f"""
## Eligibility
- **Full-text articles assessed for eligibility**: {len(results.get('definitely_include', [])) + len(results.get('needs_human_review', []))}
- **Full-text articles excluded**: [TO BE DETERMINED AFTER HUMAN REVIEW]
- **Reasons for exclusion**: [TO BE DETERMINED]

## Included
- **Studies included in qualitative synthesis**: [TO BE DETERMINED]
- **Studies included in quantitative synthesis (meta-analysis)**: [TO BE DETERMINED]

## Automated Screening Performance
- **Auto-decision rate**: {metrics.get('auto_decision_rate', 0):.1%}
- **Papers requiring human review**: {len(results.get('needs_human_review', []))}
- **Confidence threshold used**: {metrics.get('confidence_threshold', 0.8)}

## Generated
{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

**Note**: Numbers marked as "TO BE FILLED" or "TO BE DETERMINED" require manual completion after full systematic review process.
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


def _export_csv(results: dict, output_file: str, include_abstracts: bool) -> None:
    """Export results as CSV file with paper details and screening decisions."""
    
    # Combine all papers
    all_papers = []
    
    # Add definitely excluded papers
    for paper in results.get('definitely_exclude', []):
        all_papers.append({**paper, 'final_decision': 'exclude', 'confidence': 'high'})
    
    # Add definitely included papers
    for paper in results.get('definitely_include', []):
        all_papers.append({**paper, 'final_decision': 'include', 'confidence': 'high'})
    
    # Add papers needing human review
    for paper in results.get('needs_human_review', []):
        all_papers.append({**paper, 'final_decision': 'needs_review', 'confidence': 'medium/low'})
    
    # Define CSV headers
    headers = ['id', 'title', 'authors', 'year', 'journal', 'doi', 'url', 
               'screening_decision', 'exclusion_reason', 'confidence_score', 
               'final_decision', 'confidence']
    
    if include_abstracts:
        headers.insert(2, 'abstract')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for paper in all_papers:
            row = {
                'id': paper.get('id', ''),
                'title': paper.get('title', ''),
                'authors': '; '.join(paper.get('authors', [])) if paper.get('authors') else '',
                'year': paper.get('year', ''),
                'journal': paper.get('journal', ''),
                'doi': paper.get('doi', ''),
                'url': paper.get('url', ''),
                'screening_decision': paper.get('screening_decision', ''),
                'exclusion_reason': paper.get('exclusion_reason', ''),
                'confidence_score': f"{paper.get('confidence_score', 0):.3f}",
                'final_decision': paper.get('final_decision', ''),
                'confidence': paper.get('confidence', '')
            }
            
            if include_abstracts:
                row['abstract'] = paper.get('abstract', '')
            
            writer.writerow(row)


def _export_json(results: dict, output_file: str) -> None:
    """Export results as formatted JSON with metadata."""
    
    export_data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'format_version': '1.0',
            'source_file': 'screening_results.json',
            'total_papers': results.get('performance_metrics', {}).get('total_papers', 0)
        },
        'screening_results': results,
        'summary': {
            'definitely_include_count': len(results.get('definitely_include', [])),
            'definitely_exclude_count': len(results.get('definitely_exclude', [])),
            'needs_human_review_count': len(results.get('needs_human_review', [])),
            'auto_decision_rate': results.get('performance_metrics', {}).get('auto_decision_rate', 0),
            'exclusion_breakdown': dict(results.get('exclusion_stats', {}))
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


def _export_markdown(results: dict, output_file: str, include_abstracts: bool) -> None:
    """Export results as markdown report."""
    
    metrics = results.get('performance_metrics', {})
    
    content = f"""# Screening Results Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary

| Metric | Value |
|--------|-------|
| Total Papers | {metrics.get('total_papers', 0):,} |
| Auto-included | {len(results.get('definitely_include', []))} |
| Auto-excluded | {len(results.get('definitely_exclude', []))} |
| Needs Human Review | {len(results.get('needs_human_review', []))} |
| Auto-decision Rate | {metrics.get('auto_decision_rate', 0):.1%} |

## Performance Metrics

- **Target Achievement**: {'✅ Met' if metrics.get('target_achieved', False) else '⚠️ Not Met'} (Target: 80% auto-decision rate)
- **Confidence Threshold**: {metrics.get('confidence_threshold', 0.8)}
- **Human Review Rate**: {metrics.get('human_review_rate', 0):.1%}

## Exclusion Statistics

"""
    
    exclusion_stats = results.get('exclusion_stats', {})
    if exclusion_stats:
        for reason, count in sorted(exclusion_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results.get('definitely_exclude', [1])) * 100) if results.get('definitely_exclude') else 0
            content += f"- **{reason.replace('_', ' ').title()}**: {count} papers ({percentage:.1f}%)\n"
    else:
        content += "No exclusions recorded.\n"
    
    # Add paper lists if requested
    if include_abstracts:
        content += "\n## Definitely Included Papers\n\n"
        for i, paper in enumerate(results.get('definitely_include', []), 1):
            content += f"### {i}. {paper.get('title', 'Untitled')}\n"
            content += f"**Authors**: {', '.join(paper.get('authors', []))}\n"
            content += f"**Year**: {paper.get('year', 'N/A')}\n"
            content += f"**Journal**: {paper.get('journal', 'N/A')}\n"
            if paper.get('doi'):
                content += f"**DOI**: {paper.get('doi')}\n"
            content += f"**Confidence**: {paper.get('confidence_score', 0):.3f}\n"
            if paper.get('abstract'):
                content += f"**Abstract**: {paper.get('abstract')[:200]}...\n"
            content += "\n---\n\n"
        
        content += "\n## Papers Needing Human Review\n\n"
        for i, paper in enumerate(results.get('needs_human_review', []), 1):
            content += f"### {i}. {paper.get('title', 'Untitled')}\n"
            content += f"**Authors**: {', '.join(paper.get('authors', []))}\n"
            content += f"**Year**: {paper.get('year', 'N/A')}\n"
            content += f"**Journal**: {paper.get('journal', 'N/A')}\n"
            content += f"**Confidence**: {paper.get('confidence_score', 0):.3f}\n"
            content += f"**Reason**: {paper.get('exclusion_reason', 'Uncertain relevance')}\n"
            if include_abstracts and paper.get('abstract'):
                content += f"**Abstract**: {paper.get('abstract')[:200]}...\n"
            content += "\n---\n\n"
    
    content += f"""
## Next Steps

1. **Human Review**: {len(results.get('needs_human_review', []))} papers require expert review
2. **Quality Check**: Spot-check auto-excluded papers for false negatives
3. **Data Extraction**: Begin data extraction for included papers
4. **PRISMA Flow**: Create final PRISMA flow diagram
5. **Risk Assessment**: Conduct risk of bias assessment

## Automation Performance

The PRISMA Assistant achieved a {metrics.get('auto_decision_rate', 0):.1%} auto-decision rate, {'meeting' if metrics.get('target_achieved', False) else 'falling short of'} the 80% target for efficient systematic review automation.

---

*Generated by PRISMA Assistant - Systematic Review Automation Tool*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
