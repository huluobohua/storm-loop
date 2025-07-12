"""Basic CLI tests for PRISMA Assistant."""

import pytest
from click.testing import CliRunner

from prisma_assistant.cli.main import cli


def test_cli_help():
    """Test that the CLI help command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "PRISMA Assistant 80/20 screening system" in result.output


def test_cli_commands_available():
    """Test that all expected commands are available."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "screen" in result.output
    assert "stats" in result.output
    assert "export" in result.output


def test_init_command_help():
    """Test that the init command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new systematic review project" in result.output


def test_screen_command_help():
    """Test that the screen command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["screen", "--help"])
    assert result.exit_code == 0
    assert "Screen a batch of papers" in result.output


def test_init_command_execution():
    """Test that the init command executes without errors."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "--topic", "test topic", "--domain", "general"])
        assert result.exit_code == 0
        assert "Initializing PRISMA systematic review project" in result.output
        assert "Topic: test topic" in result.output
        assert "Domain: general" in result.output


def test_screen_command_validation():
    """Test that the screen command validates required parameters."""
    runner = CliRunner()
    result = runner.invoke(cli, ["screen", "--output", "test.json"])
    assert result.exit_code != 0
    assert "Missing option" in result.output
