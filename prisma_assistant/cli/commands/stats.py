import click

@click.command("stats")
@click.option("--results", "results_file", required=True, type=click.Path(exists=True), help="Results JSON from screening")
def stats_cmd(results_file: str) -> None:
    """Generate screening statistics."""
    click.echo(f"Generating statistics for {results_file}")
