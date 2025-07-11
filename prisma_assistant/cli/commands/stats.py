import json
from pathlib import Path

import click


@click.command()
@click.argument("results", type=click.Path(exists=True))
def stats_cmd(results: str) -> None:
    """Generate screening statistics."""
    data = json.loads(Path(results).read_text())
    total = len(data)
    included = sum(1 for r in data if r.get("include"))
    click.echo(f"Total: {total}\nIncluded: {included}\nExcluded: {total - included}")
