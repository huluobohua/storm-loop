import click

@click.command("screen")
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="Input file with papers")
@click.option("--output", "output_file", required=True, type=click.Path(), help="Output results JSON")
@click.option("--confidence-threshold", default=0.5, show_default=True, type=float)
def screen_cmd(input_file: str, output_file: str, confidence_threshold: float) -> None:
    """Screen a batch of papers."""
    click.echo(
        f"Screening {input_file} -> {output_file} at threshold {confidence_threshold}")
