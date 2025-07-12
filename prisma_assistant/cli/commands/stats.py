import json
from pathlib import Path
import click


@click.command("stats")
@click.option("--results", "results_file", required=True, type=click.Path(exists=True), help="Results JSON from screening")
@click.option("--output", "output_file", help="Save detailed stats to file")
@click.option("--format", "output_format", type=click.Choice(["console", "json", "csv"]), default="console", help="Output format")
def stats_cmd(results_file: str, output_file: str = None, output_format: str = "console") -> None:
    """Generate comprehensive screening statistics and performance metrics."""
    
    click.echo(f"📊 Analyzing screening results from {results_file}")
    
    try:
        # Load results
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Generate statistics
        stats = _generate_statistics(results)
        
        # Display based on format
        if output_format == "console":
            _display_console_stats(stats)
        
        # Save to file if requested
        if output_file:
            _save_stats(stats, output_file, output_format)
            click.echo(f"📁 Detailed stats saved to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


def _generate_statistics(results: dict) -> dict:
    """Generate comprehensive statistics from screening results."""
    metrics = results.get('performance_metrics', {})
    total_papers = metrics.get('total_papers', 0)
    
    # Basic counts
    definitely_exclude = len(results.get('definitely_exclude', []))
    definitely_include = len(results.get('definitely_include', []))
    needs_review = len(results.get('needs_human_review', []))
    
    # Performance metrics
    auto_decided = definitely_exclude + definitely_include
    auto_decision_rate = auto_decided / total_papers if total_papers > 0 else 0
    human_review_rate = needs_review / total_papers if total_papers > 0 else 0
    
    # Exclusion analysis
    exclusion_stats = results.get('exclusion_stats', {})
    top_exclusions = sorted(exclusion_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Confidence distribution
    confidence_dist = results.get('confidence_distribution', {})
    
    # 80/20 performance
    target_achieved = auto_decision_rate >= 0.8
    efficiency_score = min(auto_decision_rate * 100, 100)
    
    # Time savings estimate (3 minutes per paper for manual screening)
    time_saved_minutes = auto_decided * 3
    time_saved_hours = time_saved_minutes / 60
    
    # Quality metrics
    precision_estimate = definitely_include / (definitely_include + needs_review) if (definitely_include + needs_review) > 0 else 0
    recall_coverage = auto_decided / total_papers if total_papers > 0 else 0
    
    return {
        'summary': {
            'total_papers': total_papers,
            'definitely_include': definitely_include,
            'definitely_exclude': definitely_exclude,
            'needs_human_review': needs_review,
            'auto_decided': auto_decided
        },
        'performance': {
            'auto_decision_rate': auto_decision_rate,
            'human_review_rate': human_review_rate,
            'target_achieved': target_achieved,
            'efficiency_score': efficiency_score,
            'precision_estimate': precision_estimate,
            'recall_coverage': recall_coverage
        },
        'exclusions': {
            'total_excluded': definitely_exclude,
            'top_reasons': top_exclusions,
            'all_reasons': dict(exclusion_stats)
        },
        'confidence': confidence_dist,
        'time_savings': {
            'minutes': time_saved_minutes,
            'hours': time_saved_hours,
            'cost_estimate': f"${time_saved_hours * 25:.2f}"  # $25/hour estimate
        },
        'quality_indicators': {
            'high_confidence_decisions': confidence_dist.get('high', 0),
            'medium_confidence_decisions': confidence_dist.get('medium', 0),
            'low_confidence_decisions': confidence_dist.get('low', 0),
            'confidence_threshold': metrics.get('confidence_threshold', 0.8)
        }
    }


def _display_console_stats(stats: dict) -> None:
    """Display statistics in formatted console output."""
    summary = stats['summary']
    performance = stats['performance']
    exclusions = stats['exclusions']
    time_savings = stats['time_savings']
    quality = stats['quality_indicators']
    
    click.echo("\n" + "="*60)
    click.echo("📊 PRISMA SCREENING STATISTICS")
    click.echo("="*60)
    
    # Summary section
    click.echo("\n📈 SUMMARY:")
    click.echo(f"   Total papers processed: {summary['total_papers']:,}")
    click.echo(f"   ✅ Auto-included: {summary['definitely_include']:,}")
    click.echo(f"   ❌ Auto-excluded: {summary['definitely_exclude']:,}")
    click.echo(f"   🤔 Needs human review: {summary['needs_human_review']:,}")
    
    # Performance section
    click.echo("\n🎯 PERFORMANCE:")
    efficiency = "🎯 TARGET MET" if performance['target_achieved'] else "⚠️  BELOW TARGET"
    click.echo(f"   Auto-decision rate: {performance['auto_decision_rate']:.1%} {efficiency}")
    click.echo(f"   Human review rate: {performance['human_review_rate']:.1%}")
    click.echo(f"   Efficiency score: {performance['efficiency_score']:.1f}/100")
    click.echo(f"   Estimated precision: {performance['precision_estimate']:.1%}")
    
    # Time savings section
    click.echo("\n⏰ TIME SAVINGS:")
    click.echo(f"   Time saved: {time_savings['hours']:.1f} hours ({time_savings['minutes']} minutes)")
    click.echo(f"   Cost savings estimate: {time_savings['cost_estimate']}")
    click.echo(f"   Papers processed automatically: {summary['auto_decided']:,}")
    
    # Quality indicators
    click.echo("\n🔍 QUALITY INDICATORS:")
    click.echo(f"   High confidence decisions: {quality['high_confidence_decisions']}")
    click.echo(f"   Medium confidence decisions: {quality['medium_confidence_decisions']}")
    click.echo(f"   Low confidence decisions: {quality['low_confidence_decisions']}")
    click.echo(f"   Confidence threshold: {quality['confidence_threshold']}")
    
    # Top exclusion reasons
    if exclusions['top_reasons']:
        click.echo("\n📋 TOP EXCLUSION REASONS:")
        for i, (reason, count) in enumerate(exclusions['top_reasons'], 1):
            percentage = (count / exclusions['total_excluded'] * 100) if exclusions['total_excluded'] > 0 else 0
            click.echo(f"   {i}. {reason}: {count} papers ({percentage:.1f}%)")
    
    # Recommendations
    click.echo("\n💡 RECOMMENDATIONS:")
    if performance['auto_decision_rate'] >= 0.8:
        click.echo("   ✅ Excellent automation rate! System is performing optimally.")
    elif performance['auto_decision_rate'] >= 0.6:
        click.echo("   ⚡ Good automation rate. Consider refining inclusion/exclusion patterns.")
    else:
        click.echo("   ⚠️  Low automation rate. Review patterns and thresholds.")
    
    if summary['needs_human_review'] > 0:
        click.echo(f"   📝 {summary['needs_human_review']} papers require human expert review.")
    
    click.echo("\n" + "="*60)


def _save_stats(stats: dict, output_file: str, format_type: str) -> None:
    """Save statistics to file in specified format."""
    path = Path(output_file)
    
    if format_type == "json":
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    elif format_type == "csv":
        import csv
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers and data
            writer.writerow(['Metric', 'Value'])
            
            # Summary metrics
            writer.writerow(['Total Papers', stats['summary']['total_papers']])
            writer.writerow(['Auto-included', stats['summary']['definitely_include']])
            writer.writerow(['Auto-excluded', stats['summary']['definitely_exclude']])
            writer.writerow(['Needs Review', stats['summary']['needs_human_review']])
            
            # Performance metrics
            writer.writerow(['Auto-decision Rate', f"{stats['performance']['auto_decision_rate']:.1%}"])
            writer.writerow(['Efficiency Score', f"{stats['performance']['efficiency_score']:.1f}"])
            writer.writerow(['Time Saved (hours)', f"{stats['time_savings']['hours']:.1f}"])
            writer.writerow(['Cost Savings', stats['time_savings']['cost_estimate']])
    
    else:  # Default to JSON for unknown formats
        _save_stats(stats, output_file, "json")
