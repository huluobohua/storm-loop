"""
Tests for STORM-Loop utilities
"""
import pytest
from unittest.mock import patch, MagicMock
from storm_loop.utils.logging import setup_logging


class TestLogging:
    """Test logging utilities"""

    @patch('storm_loop.utils.logging.logger')
    def test_setup_logging(self, mock_logger):
        """Test logging setup"""
        # Mock logger methods
        mock_logger.remove = MagicMock()
        mock_logger.add = MagicMock()
        
        # Call setup_logging
        result_logger = setup_logging()
        
        # Verify logger methods were called
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2  # Console and file handlers
        
        # Check that the returned logger is the mock
        assert result_logger == mock_logger

    def test_logging_config_parameters(self):
        """Test that logging configuration uses correct parameters"""
        with patch('storm_loop.utils.logging.logger') as mock_logger:
            mock_logger.remove = MagicMock()
            mock_logger.add = MagicMock()
            
            setup_logging()
            
            # Check that add was called with correct parameters
            calls = mock_logger.add.call_args_list
            assert len(calls) == 2
            
            # First call should be for stdout (console handler)
            console_call = calls[0]
            console_args, console_kwargs = console_call
            assert console_kwargs.get('colorize') is True
            assert 'level' in console_kwargs
            assert 'format' in console_kwargs
            
            # Second call should be for file handler
            file_call = calls[1]
            file_args, file_kwargs = file_call
            assert file_kwargs.get('rotation') == "10 MB"
            assert file_kwargs.get('retention') == "1 week"
            assert file_kwargs.get('compression') == "zip"