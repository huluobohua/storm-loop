import click

@click.command("init")
@click.option("--topic", required=True, help="Research topic")
@click.option("--domain", default="general", help="Domain of study")
def init_cmd(topic: str, domain: str) -> None:
    """Initialize a new systematic review project."""
    click.echo(f"Initialized project on '{topic}' in domain '{domain}'.")
