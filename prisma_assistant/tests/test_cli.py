"""Basic CLI tests for PRISMA Assistant."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_cli_help():
    """Test that the CLI help command works."""
    result = subprocess.run(
        [sys.executable, "-m", "prisma_assistant", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    assert result.returncode == 0
    assert "PRISMA Assistant 80/20 screening system" in result.stdout


def test_cli_commands_available():
    """Test that all expected commands are available."""
    result = subprocess.run(
        [sys.executable, "-m", "prisma_assistant", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    assert result.returncode == 0
    assert "init" in result.stdout
    assert "screen" in result.stdout
    assert "stats" in result.stdout
    assert "export" in result.stdout


def test_init_command_help():
    """Test that the init command help works."""
    result = subprocess.run(
        [sys.executable, "-m", "prisma_assistant", "init", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    assert result.returncode == 0
    assert "Initialize a new systematic review project" in result.stdout


def test_screen_command_help():
    """Test that the screen command help works."""
    result = subprocess.run(
        [sys.executable, "-m", "prisma_assistant", "screen", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    assert result.returncode == 0
    assert "Screen a batch of papers" in result.stdout
