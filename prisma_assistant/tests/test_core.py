"""Tests for core PRISMA integration."""

import pytest
from unittest.mock import patch

from prisma_assistant.core import get_screener


def test_get_screener_with_defaults():
    """Test getting screener with default parameters."""
    with patch("prisma_assistant.core.PRISMAScreener") as mock_screener:
        get_screener()
        mock_screener.assert_called_once_with(
            include_patterns=None,
            exclude_patterns=None,
            threshold=0.8,
        )


def test_get_screener_with_custom_params():
    """Test getting screener with custom parameters."""
    with patch("prisma_assistant.core.PRISMAScreener") as mock_screener:
        get_screener(
            include_patterns=["custom"],
            exclude_patterns=["exclude"],
            threshold=0.9,
        )
        mock_screener.assert_called_once_with(
            include_patterns=["custom"],
            exclude_patterns=["exclude"],
            threshold=0.9,
        )


def test_get_screener_import_error():
    """Test handling of import errors."""
    with patch("prisma_assistant.core.PRISMAScreener", None):
        with pytest.raises(ImportError, match="PRISMA screener not available"):
            get_screener()
