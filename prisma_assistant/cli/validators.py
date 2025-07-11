"""Simple input validators used across commands."""

from __future__ import annotations

from pathlib import Path

import click


def existing_file(path: str) -> str:
    if not Path(path).exists():
        raise click.BadParameter(f"File not found: {path}")
    return path
