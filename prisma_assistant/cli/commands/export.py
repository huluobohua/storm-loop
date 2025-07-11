import click

@click.command("export")
@click.option("--results", "results_file", required=True, type=click.Path(exists=True), help="Results JSON from screening")
@click.option("--format", "format_", required=True, type=click.Choice(["prisma-flow", "csv", "json"]))
@click.option("--output", "output_file", required=False, type=click.Path())
def export_cmd(results_file: str, format_: str, output_file: str | None) -> None:
    """Export screening results to various formats."""
    msg = f"Exporting {results_file} as {format_}"
    if output_file:
        msg += f" -> {output_file}"
    click.echo(msg)
