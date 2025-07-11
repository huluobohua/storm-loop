import json
from pathlib import Path

import click


def write_config(path: Path, topic: str, domain: str) -> None:
    config = {"topic": topic, "domain": domain}
    path.write_text(json.dumps(config, indent=2))


@click.command()
@click.option("--topic", required=True, help="Review topic")
@click.option("--domain", required=True, help="Domain of study")
@click.option(
    "--output",
    type=click.Path(),
    default=".prisma-assistant.json",
    help="Config file path",
)
def init_cmd(topic: str, domain: str, output: str) -> None:
    """Initialize a new systematic review project."""
    cfg_path = Path(output)
    write_config(cfg_path, topic, domain)
    click.echo(f"Initialized project at {cfg_path}")
