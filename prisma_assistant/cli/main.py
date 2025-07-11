import click
from .commands.init import init_cmd
from .commands.screen import screen_cmd
from .commands.stats import stats_cmd
from .commands.export import export_cmd


@click.group()
def cli() -> None:
    """PRISMA Assistant command line interface."""
    pass


cli.add_command(init_cmd, name="init")
cli.add_command(screen_cmd, name="screen")
cli.add_command(stats_cmd, name="stats")
cli.add_command(export_cmd, name="export")

if __name__ == "__main__":
    cli()
