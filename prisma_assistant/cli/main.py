import click

from .commands.init import init_cmd
from .commands.screen import screen_cmd
from .commands.stats import stats_cmd
from .commands.export import export_cmd

@click.group()
@click.version_option(package_name="prisma-assistant", version="0.1.0")
def cli():
    """PRISMA Assistant 80/20 screening system."""

cli.add_command(init_cmd)
cli.add_command(screen_cmd)
cli.add_command(stats_cmd)
cli.add_command(export_cmd)
