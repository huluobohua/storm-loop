import csv
import json
from pathlib import Path

import click


def _read_input(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".csv":
        with path.open() as f:
            reader = csv.DictReader(f)
            return list(reader)
    if path.suffix == ".json":
        return json.loads(path.read_text())
    raise click.ClickException("Unsupported input format")


@click.command()
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input file",
)
@click.option(
    "--output",
    "output_file",
    required=True,
    type=click.Path(),
    help="Results JSON path",
)
@click.option(
    "--confidence-threshold",
    default=0.5,
    show_default=True,
    help="Confidence threshold",
)
def screen_cmd(input_file: str, output_file: str, confidence_threshold: float) -> None:
    """Screen a batch of papers."""
    inp = Path(input_file)
    data = _read_input(inp)
    results = []
    total = len(data)
    for idx, paper in enumerate(data, 1):
        title = paper.get("title", "")
        # Placeholder scoring
        score = 1.0 if len(title) % 2 == 0 else 0.0
        include = score >= confidence_threshold
        results.append({"title": title, "score": score, "include": include})
        click.echo(f"Processed {idx}/{total}", nl=False)
        click.echo("\r", nl=False)
    Path(output_file).write_text(json.dumps(results, indent=2))
    click.echo(f"Saved results to {output_file}")
