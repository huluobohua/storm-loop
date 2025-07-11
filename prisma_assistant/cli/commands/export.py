import json
from pathlib import Path

import click


@click.command()
@click.argument("results", type=click.Path(exists=True))
@click.option(
    "--format", "fmt", default="prisma-flow", show_default=True, help="Export format"
)
@click.option(
    "--output", "output_file", required=True, type=click.Path(), help="Output path"
)
def export_cmd(results: str, fmt: str, output_file: str) -> None:
    """Export screening results to various formats."""
    data = json.loads(Path(results).read_text())
    if fmt == "prisma-flow":
        flow = {
            "records": len(data),
            "included": sum(1 for r in data if r.get("include")),
        }
        Path(output_file).write_text(json.dumps(flow, indent=2))
    else:
        raise click.ClickException(f"Unknown format: {fmt}")
    click.echo(f"Exported {fmt} data to {output_file}")
